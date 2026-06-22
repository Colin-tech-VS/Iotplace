"""Payment orchestration on application acceptance."""

from __future__ import annotations

from data import store
from payments import stripe_service


def on_application_accepted(message: dict, enterprise_user: dict) -> dict:
    """
    Called when an enterprise accepts a startup application.
    Creates engagement, auto-invoice (if Stripe configured), updates project status.
    """
    if message.get("kind") != "application":
        return {"ok": True, "skipped": True, "reason": "not_application"}

    project_id = message.get("project_id")
    if not project_id:
        return {"ok": False, "error": "Projet introuvable pour cette candidature."}

    project = store.get_project(project_id)
    if not project:
        return {"ok": False, "error": "Projet introuvable."}

    profile = store.get_enterprise_for_user(enterprise_user["id"])
    if not profile or project.get("enterprise_id") != profile["id"]:
        return {"ok": False, "error": "Non autorisé sur ce projet."}

    startup_id = message.get("from_profile_id")
    startup = store.get_startup(startup_id) if startup_id else None
    if not startup:
        return {"ok": False, "error": "Profil startup introuvable."}

    existing = store.get_engagement_by_message(message["id"])
    if existing:
        return {
            "ok": True,
            "engagement": existing,
            "invoice_url": existing.get("stripe_hosted_invoice_url"),
            "already_exists": True,
        }

    amount_cents = store.resolve_project_amount_cents(project)
    fee_percent = stripe_service.get_commission_percent_for_enterprise(profile)
    platform_fee_cents = int(amount_cents * fee_percent / 100)
    startup_payout_cents = amount_cents - platform_fee_cents

    engagement = store.create_engagement({
        "application_message_id": message["id"],
        "project_id": project_id,
        "enterprise_id": profile["id"],
        "startup_id": startup["id"],
        "amount_cents": amount_cents,
        "platform_fee_cents": platform_fee_cents,
        "startup_payout_cents": startup_payout_cents,
        "currency": "eur",
        "status": "draft",
    })

    _decline_other_applications(project_id, message["id"])
    store.update_project(project_id, {"status": "En cours"})

    result = {
        "ok": True,
        "engagement": engagement,
        "invoice_url": None,
        "stripe_configured": stripe_service.is_configured(),
        "startup_onboarding_required": not startup.get("stripe_onboarding_complete"),
    }

    if not stripe_service.is_configured():
        store.update_engagement(engagement["id"], {
            "status": "pending_payment",
            "notes": "Stripe non configuré — facture manuelle requise.",
        })
        return result

    try:
        startup_user = store._user_for_startup_id(startup["id"])
        invoice_data = stripe_service.create_escrow_invoice(
            engagement, profile, enterprise_user, project, startup
        )
        result["invoice_url"] = invoice_data.get("hosted_invoice_url")
        result["engagement"] = store.get_engagement(engagement["id"])
    except stripe_service.PaymentError as exc:
        store.update_engagement(engagement["id"], {
            "status": "payment_error",
            "notes": str(exc),
        })
        result["payment_error"] = str(exc)

    return result


def _decline_other_applications(project_id: str, accepted_message_id: str) -> None:
    for app in store.get_applications_for_project(project_id):
        if app["id"] == accepted_message_id:
            continue
        if app.get("status") == "pending":
            store.update_message_status_direct(app["id"], "declined")


def release_engagement(engagement_id: str, enterprise_user: dict) -> dict:
    engagement = store.get_engagement(engagement_id)
    if not engagement:
        return {"ok": False, "error": "Engagement introuvable."}

    profile = store.get_enterprise_for_user(enterprise_user["id"])
    if not profile or engagement.get("enterprise_id") != profile["id"]:
        return {"ok": False, "error": "Non autorisé."}

    if engagement.get("status") != "escrowed":
        return {"ok": False, "error": "Les fonds ne sont pas en séquestre (paiement en attente)."}

    startup = store.get_startup(engagement.get("startup_id"))
    if not startup:
        return {"ok": False, "error": "Startup introuvable."}

    if not stripe_service.is_configured():
        return {"ok": False, "error": "Stripe non configuré."}

    try:
        transfer = stripe_service.release_escrow_to_startup(engagement, startup)
        return {"ok": True, "transfer": transfer, "engagement": store.get_engagement(engagement_id)}
    except stripe_service.PaymentError as exc:
        return {"ok": False, "error": str(exc)}

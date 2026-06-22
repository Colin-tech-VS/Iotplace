"""Paid PoC application flow for startups."""

from __future__ import annotations

from data import store
from data.engagement_phases import requires_startup_application_fee
from payments import stripe_service


def project_requires_poc_fee(project: dict) -> bool:
    return requires_startup_application_fee(project.get("engagement_phase"))


def start_poc_application(user: dict, startup: dict, project: dict, message_body: str) -> dict:
    if not stripe_service.is_checkout_ready():
        raise stripe_service.PaymentError(
            "Stripe n'est pas configuré — candidatures PoC indisponibles."
        )
    if store.startup_already_applied(startup["id"], project["id"]):
        raise ValueError("Vous avez déjà candidaté à ce projet.")
    if not project_requires_poc_fee(project):
        raise ValueError("Ce projet ne nécessite pas de frais de candidature PoC.")

    fee_cents = stripe_service.get_poc_application_fee_cents()
    commission_percent = stripe_service.get_poc_application_commission_percent()
    platform_fee_cents = int(fee_cents * commission_percent / 100)

    checkout = store.create_application_checkout({
        "project_id": project["id"],
        "startup_id": startup["id"],
        "user_id": user["id"],
        "message_body": message_body,
        "amount_cents": fee_cents,
        "platform_fee_cents": platform_fee_cents,
        "commission_percent": commission_percent,
    })

    session = stripe_service.create_poc_application_checkout(checkout, user, startup, project)
    store.update_application_checkout(checkout["id"], {"stripe_session_id": session.id})

    return {"checkout_url": session.url, "checkout_id": checkout["id"]}


def complete_from_stripe_session(session: dict) -> dict:
    checkout_id = (session.get("metadata") or {}).get("iotplace_checkout_id")
    if not checkout_id:
        return {"ok": False, "error": "checkout_id manquant"}
    if session.get("payment_status") != "paid":
        return {"ok": False, "error": "paiement non confirmé"}
    return _finalize_checkout(checkout_id, session.get("id"))


def complete_from_session_id(session_id: str) -> dict:
    if not session_id:
        return {"ok": False, "error": "session_id manquant"}
    if not stripe_service.is_configured():
        return {"ok": False, "error": "Stripe non configuré"}
    try:
        session = stripe_service.retrieve_checkout_session(session_id)
    except stripe_service.PaymentError as exc:
        return {"ok": False, "error": str(exc)}
    return complete_from_stripe_session(session)


def _finalize_checkout(checkout_id: str, stripe_session_id: str | None = None) -> dict:
    checkout = store.get_application_checkout(checkout_id)
    if not checkout:
        return {"ok": False, "error": "Candidature PoC introuvable."}

    if checkout.get("status") == "completed":
        return {
            "ok": True,
            "message_id": checkout.get("message_id"),
            "already_completed": True,
        }

    user = store.get_user(checkout["user_id"])
    startup = store.get_startup(checkout["startup_id"])
    project = store.get_project(checkout["project_id"])
    if not user or not startup or not project:
        return {"ok": False, "error": "Données candidature incomplètes."}

    if store.startup_already_applied(startup["id"], project["id"]):
        store.update_application_checkout(checkout_id, {
            "status": "completed",
            "message_id": checkout.get("message_id"),
            "stripe_session_id": stripe_session_id or checkout.get("stripe_session_id"),
        })
        return {"ok": True, "already_applied": True}

    try:
        message = store.apply_to_project(
            user,
            startup,
            project,
            checkout["message_body"],
            poc_fee_cents=checkout.get("amount_cents"),
            poc_checkout_id=checkout_id,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    store.update_application_checkout(checkout_id, {
        "status": "completed",
        "message_id": message["id"],
        "stripe_session_id": stripe_session_id or checkout.get("stripe_session_id"),
        "paid_at": store._now().isoformat(),
    })
    return {"ok": True, "message_id": message["id"]}

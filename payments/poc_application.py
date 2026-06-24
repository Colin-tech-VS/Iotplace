"""Paid PoC application flow for startups."""

from __future__ import annotations

import logging

from data import store
from data.engagement_phases import requires_startup_application_fee
from payments import stripe_service

logger = logging.getLogger(__name__)


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


def complete_from_stripe_session(
    session: dict,
    *,
    expected_project_id: str | None = None,
) -> dict:
    sget = stripe_service.sget
    meta = sget(session, "metadata") or {}
    checkout_id = sget(meta, "iotplace_checkout_id")
    if not checkout_id:
        return {"ok": False, "error": "checkout_id manquant"}
    if sget(meta, "iotplace_type") != "poc_application":
        return {"ok": False, "error": "Type de paiement invalide."}
    project_id = sget(meta, "project_id")
    if expected_project_id and project_id != expected_project_id:
        return {"ok": False, "error": "Ce paiement ne correspond pas à ce projet."}
    if sget(session, "payment_status") != "paid":
        return {"ok": False, "error": "paiement non confirmé"}
    return _finalize_checkout(checkout_id, sget(session, "id"))


def complete_from_session_id(
    session_id: str,
    *,
    expected_project_id: str | None = None,
) -> dict:
    if not session_id:
        return {"ok": False, "error": "session_id manquant"}
    if not stripe_service.is_configured():
        return {"ok": False, "error": "Stripe non configuré"}
    try:
        session = stripe_service.retrieve_checkout_session(session_id)
    except stripe_service.PaymentError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception:
        logger.exception("Stripe session retrieve failed session_id=%s", session_id[:20])
        return {"ok": False, "error": "Impossible de vérifier le paiement Stripe."}
    try:
        return complete_from_stripe_session(
            session,
            expected_project_id=expected_project_id,
        )
    except Exception:
        logger.exception("PoC checkout finalization failed session_id=%s", session_id[:20])
        return {"ok": False, "error": "Erreur lors de la finalisation de la candidature."}


def mark_checkout_cancelled(session: dict) -> dict:
    sget = stripe_service.sget
    checkout_id = sget(sget(session, "metadata") or {}, "iotplace_checkout_id")
    if not checkout_id:
        return {"ok": False, "error": "checkout_id manquant"}
    checkout = store.get_application_checkout(checkout_id)
    if not checkout:
        return {"ok": False, "error": "Candidature PoC introuvable."}
    if checkout.get("status") == "completed":
        return {"ok": True, "already_completed": True}
    store.update_application_checkout(checkout_id, {
        "status": "cancelled",
        "cancelled_at": store._now().isoformat(),
        "stripe_session_id": sget(session, "id") or checkout.get("stripe_session_id"),
    })
    return {"ok": True, "checkout_id": checkout_id}


def _finalize_checkout(checkout_id: str, stripe_session_id: str | None = None) -> dict:
    checkout = store.get_application_checkout(checkout_id)
    if not checkout:
        return {"ok": False, "error": "Candidature PoC introuvable."}

    user_id = checkout.get("user_id")

    if checkout.get("status") == "completed":
        return {
            "ok": True,
            "message_id": checkout.get("message_id"),
            "user_id": user_id,
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
        return {"ok": True, "user_id": user_id, "already_applied": True}

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
    except Exception:
        logger.exception("apply_to_project failed checkout_id=%s", checkout_id)
        return {"ok": False, "error": "Erreur lors de l'enregistrement de la candidature."}

    try:
        store.update_application_checkout(checkout_id, {
            "status": "completed",
            "message_id": message["id"],
            "stripe_session_id": stripe_session_id or checkout.get("stripe_session_id"),
            "paid_at": store._now().isoformat(),
        })
    except Exception:
        logger.exception("checkout update failed checkout_id=%s", checkout_id)
        return {
            "ok": True,
            "message_id": message["id"],
            "user_id": user_id,
            "warning": "Candidature enregistrée mais mise à jour du paiement incomplète.",
        }

    return {"ok": True, "message_id": message["id"], "user_id": user_id}

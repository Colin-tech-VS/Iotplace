"""Transactional emails for compte (password reset, etc.)."""

from __future__ import annotations


class MailDeliveryError(Exception):
    pass


def send_password_reset_email(to_email: str, reset_url: str, locale: str = "fr") -> dict:
    from crm.email_service import EmailError, is_smtp_configured, send_email
    from data.store import get_site_url

    if not is_smtp_configured():
        raise MailDeliveryError("SMTP non configuré.")

    if locale == "en":
        subject = "Reset your Iotplace password"
        body = (
            "<p>You requested a password reset for your <strong>Iotplace</strong> account.</p>"
            "<p>Click the button below to choose a new password. This link is valid for 24 hours.</p>"
            f"<p style='margin:20px 0'><a href='{reset_url}' "
            "style='display:inline-block;padding:12px 22px;border-radius:10px;background:#00e8c8;"
            "color:#041018;font-weight:700;text-decoration:none'>Reset password →</a></p>"
            "<p style='font-size:13px;color:#8b95a8'>If you did not request this email, you can ignore it — "
            "your password will not change.</p>"
        )
    else:
        subject = "Réinitialisation de votre mot de passe Iotplace"
        body = (
            "<p>Vous avez demandé la réinitialisation du mot de passe de votre compte <strong>Iotplace</strong>.</p>"
            "<p>Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe. Ce lien est valable 24 h.</p>"
            f"<p style='margin:20px 0'><a href='{reset_url}' "
            "style='display:inline-block;padding:12px 22px;border-radius:10px;background:#00e8c8;"
            "color:#041018;font-weight:700;text-decoration:none'>Réinitialiser le mot de passe →</a></p>"
            "<p style='font-size:13px;color:#8b95a8'>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email — "
            "votre mot de passe ne sera pas modifié.</p>"
        )

    try:
        return send_email(
            to_email,
            subject,
            body,
            site_url=get_site_url(),
            locale=locale if locale in ("fr", "en") else "fr",
        )
    except EmailError as exc:
        raise MailDeliveryError(str(exc)) from exc

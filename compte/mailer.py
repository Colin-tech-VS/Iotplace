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


def _mission_url(message_id: str) -> str:
    from data.store import get_site_url

    base = get_site_url().rstrip("/")
    if message_id:
        return f"{base}/compte/messages/{message_id}"
    return f"{base}/compte"


def _cta_button(url: str, label: str) -> str:
    return (
        f"<p style='margin:22px 0'><a href='{url}' "
        "style='display:inline-block;padding:12px 22px;border-radius:10px;background:#00e8c8;"
        f"color:#041018;font-weight:700;text-decoration:none'>{label} →</a></p>"
    )


def send_progress_update_email(
    to_email: str,
    *,
    startup_name: str,
    project_title: str,
    progress_percent: int,
    body: str,
    message_id: str = "",
    locale: str = "fr",
) -> dict:
    """Notify an enterprise that a startup posted a progress update on its mission."""
    from crm.email_service import EmailError, is_smtp_configured, send_email
    from data.store import get_site_url

    if not is_smtp_configured():
        raise MailDeliveryError("SMTP non configuré.")

    url = _mission_url(message_id)
    excerpt = (body or "").strip()
    if len(excerpt) > 280:
        excerpt = excerpt[:277] + "…"

    if locale == "en":
        subject = f"{startup_name} updated your project ({progress_percent}%)"
        intro = (
            f"<p><strong>{startup_name}</strong> just posted a progress update on your IoT "
            f"mission <strong>{project_title}</strong>.</p>"
            f"<p>Progress: <strong>{progress_percent}%</strong></p>"
        )
        quote = f"<blockquote style='margin:0 0 4px;padding:10px 14px;border-left:3px solid #00e8c8'>{excerpt}</blockquote>" if excerpt else ""
        cta = _cta_button(url, "View the mission")
    else:
        subject = f"{startup_name} a mis à jour votre projet ({progress_percent} %)"
        intro = (
            f"<p><strong>{startup_name}</strong> vient de publier un point d'avancement sur votre "
            f"mission IoT <strong>{project_title}</strong>.</p>"
            f"<p>Avancement : <strong>{progress_percent} %</strong></p>"
        )
        quote = f"<blockquote style='margin:0 0 4px;padding:10px 14px;border-left:3px solid #00e8c8'>{excerpt}</blockquote>" if excerpt else ""
        cta = _cta_button(url, "Voir la mission")

    try:
        return send_email(
            to_email,
            subject,
            intro + quote + cta,
            site_url=get_site_url(),
            locale=locale if locale in ("fr", "en") else "fr",
        )
    except EmailError as exc:
        raise MailDeliveryError(str(exc)) from exc


def send_progress_reminder_email(
    to_email: str,
    *,
    startup_name: str,
    project_title: str,
    message_id: str = "",
    locale: str = "fr",
) -> dict:
    """Remind a startup to post a progress update on an active mission."""
    from crm.email_service import EmailError, is_smtp_configured, send_email
    from data.store import get_site_url

    if not is_smtp_configured():
        raise MailDeliveryError("SMTP non configuré.")

    url = _mission_url(message_id)
    if locale == "en":
        subject = f"Update the progress of {project_title}"
        body = (
            f"<p>Hi {startup_name},</p>"
            f"<p>Your client hasn't heard from you on the mission <strong>{project_title}</strong> "
            "for a while. Posting a short progress update keeps the enterprise confident and "
            "speeds up the release of escrowed funds.</p>"
            + _cta_button(url, "Post an update")
            + "<p style='font-size:13px;color:#8b95a8'>A two-line update with a progress percentage is enough.</p>"
        )
    else:
        subject = f"Mettez à jour l'avancement de {project_title}"
        body = (
            f"<p>Bonjour {startup_name},</p>"
            f"<p>Votre client n'a pas eu de nouvelles de la mission <strong>{project_title}</strong> "
            "depuis quelque temps. Publier un point d'avancement rassure l'entreprise et accélère "
            "la libération des fonds en séquestre.</p>"
            + _cta_button(url, "Publier un avancement")
            + "<p style='font-size:13px;color:#8b95a8'>Deux lignes et un pourcentage d'avancement suffisent.</p>"
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

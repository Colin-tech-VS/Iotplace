"""SMTP outbound + IMAP inbox for CRM mailing."""

from __future__ import annotations

import email
import hashlib
import imaplib
import os
import re
import smtplib
import ssl
from datetime import datetime, timezone
from email.header import decode_header
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

TRACKING_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01"
    b"\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class EmailError(Exception):
    pass


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _env_bool(name: str, default: bool = True) -> bool:
    raw = _env(name)
    if not raw:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def get_platform_email() -> str:
    from data.site_config import CONTACT_EMAIL

    return _env("SMTP_FROM_EMAIL") or _env("SMTP_USER") or CONTACT_EMAIL


def get_smtp_config() -> dict:
    return {
        "host": _env("SMTP_HOST"),
        "port": int(_env("SMTP_PORT", "587") or "587"),
        "user": _env("SMTP_USER"),
        "password": _env("SMTP_PASSWORD"),
        "from_email": get_platform_email(),
        "from_name": _env("SMTP_FROM_NAME", "Iotplace"),
        "use_tls": _env_bool("SMTP_USE_TLS", True),
    }


def get_imap_config() -> dict:
    host = _env("IMAP_HOST") or _env("SMTP_HOST")
    return {
        "host": host,
        "port": int(_env("IMAP_PORT", "993") or "993"),
        "user": _env("IMAP_USER") or _env("SMTP_USER"),
        "password": _env("IMAP_PASSWORD") or _env("SMTP_PASSWORD"),
        "use_ssl": _env_bool("IMAP_USE_SSL", True),
        "mailbox": _env("IMAP_MAILBOX", "INBOX"),
    }


def is_smtp_configured() -> bool:
    cfg = get_smtp_config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"] and cfg["from_email"])


def is_imap_configured() -> bool:
    cfg = get_imap_config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def recipient_token(campaign_id: str, email_address: str) -> str:
    raw = f"{campaign_id}:{email_address.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _decode_mime_header(value: str) -> str:
    if not value:
        return ""
    parts = []
    for chunk, enc in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(str(chunk))
    return "".join(parts).strip()


def _html_to_text(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", "", html or "", flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def wrap_email_html(
    body_html: str,
    *,
    tracking_url: str | None = None,
    unsubscribe_hint: str = "",
    site_url: str = "",
    locale: str = "fr",
    subject: str = "",
) -> str:
    """Wrap inner content in the Iotplace branded email shell (always used on send)."""
    accent = "#00e8c8"
    bg_outer = "#070b12"
    bg_card = "#0f1522"
    text_main = "#e8ecf4"
    text_muted = "#8b95a8"
    border = "rgba(0, 232, 200, 0.22)"
    site = (site_url or store.get_site_url() or "https://iotplace.fr").rstrip("/")
    from data.site_config import CONTACT_EMAIL

    contact = CONTACT_EMAIL
    if locale == "en":
        tagline = "B2B IoT subcontracting marketplace"
        cta_label = "Visit Iotplace"
        footer_line = "You receive this email from Iotplace."
        contact_label = "Contact us"
    else:
        tagline = "Marketplace B2B de sous-traitance IoT"
        cta_label = "Visiter Iotplace"
        footer_line = "Vous recevez cet email de la part d'Iotplace."
        contact_label = "Nous contacter"

    pixel = ""
    if tracking_url:
        pixel = f'<img src="{tracking_url}" width="1" height="1" alt="" style="display:none!important;max-height:0;overflow:hidden" />'

    extra_footer = ""
    if unsubscribe_hint:
        extra_footer = f'<p style="margin:12px 0 0;font-size:11px;color:{text_muted};">{unsubscribe_hint}</p>'

    safe_subject = subject.replace("&", "&amp;").replace("<", "&lt;") if subject else "Iotplace"

    return f"""<!DOCTYPE html>
<html lang="{locale}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="dark">
<title>{safe_subject}</title>
</head>
<body style="margin:0;padding:0;background:{bg_outer};font-family:'DM Sans',Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{bg_outer};padding:32px 16px;">
<tr><td align="center">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%;background:{bg_card};border-radius:16px;border:1px solid {border};overflow:hidden;">
<tr><td style="height:4px;background:linear-gradient(90deg,{accent},#3b82f6);font-size:0;line-height:0;">&nbsp;</td></tr>
<tr><td style="padding:28px 32px 20px;text-align:center;border-bottom:1px solid {border};">
  <a href="{site}" style="text-decoration:none;font-size:26px;font-weight:700;letter-spacing:-0.03em;">
    <span style="color:#ffffff;">Iot</span><span style="color:{accent};">place</span>
  </a>
  <p style="margin:8px 0 0;font-size:12px;color:{text_muted};letter-spacing:0.02em;">{tagline}</p>
</td></tr>
<tr><td style="padding:32px;color:{text_main};font-size:15px;line-height:1.65;">
  <div style="color:{text_main};">
    {body_html}
  </div>
  <table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0 8px;">
  <tr><td style="border-radius:10px;background:{accent};">
    <a href="{site}" style="display:inline-block;padding:12px 22px;color:#041018;font-size:14px;font-weight:700;text-decoration:none;">{cta_label} →</a>
  </td></tr>
  </table>
</td></tr>
<tr><td style="padding:20px 32px 28px;border-top:1px solid {border};text-align:center;">
  <p style="margin:0;font-size:12px;color:{text_muted};">{footer_line}</p>
  <p style="margin:8px 0 0;font-size:12px;"><a href="mailto:{contact}" style="color:{accent};text-decoration:none;">{contact}</a> · <a href="{site}" style="color:{accent};text-decoration:none;">{site.replace('https://', '')}</a></p>
  {extra_footer}
  {pixel}
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def test_smtp_connection() -> dict:
    if not is_smtp_configured():
        raise EmailError("SMTP non configuré — renseignez SMTP_HOST, SMTP_USER et SMTP_PASSWORD.")
    cfg = get_smtp_config()
    try:
        with _smtp_connection(cfg) as smtp:
            smtp.noop()
        return {"ok": True, "host": cfg["host"], "port": cfg["port"], "user": cfg["user"]}
    except Exception as exc:
        raise EmailError(f"Connexion SMTP échouée : {exc}") from exc


def send_email(
    to: str,
    subject: str,
    body_html: str,
    *,
    body_text: str | None = None,
    reply_to: str | None = None,
    tracking_url: str | None = None,
    site_url: str = "",
    locale: str = "fr",
) -> dict:
    if not is_smtp_configured():
        raise EmailError("SMTP non configuré.")
    to_addr = parseaddr(to)[1] or to.strip()
    if not to_addr or "@" not in to_addr:
        raise EmailError(f"Destinataire invalide : {to}")

    cfg = get_smtp_config()
    html = wrap_email_html(
        body_html,
        tracking_url=tracking_url,
        site_url=site_url,
        locale=locale,
        subject=subject,
    )
    text = body_text or _html_to_text(body_html)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((cfg["from_name"], cfg["from_email"]))
    msg["To"] = to_addr
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        with _smtp_connection(cfg) as smtp:
            smtp.send_message(msg)
    except Exception as exc:
        raise EmailError(str(exc)) from exc

    return {
        "to": to_addr,
        "subject": subject,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }


def build_branded_preview(body_html: str, subject: str = "", locale: str = "fr", site_url: str = "") -> str:
    from data.store import get_site_url
    return wrap_email_html(
        body_html or "<p>…</p>",
        site_url=site_url or get_site_url(),
        locale=locale if locale in ("fr", "en") else "fr",
        subject=subject,
    )


def send_test_email(to: str, locale: str = "fr", site_url: str = "") -> dict:
    if locale == "en":
        body = (
            "<p>This is a <strong>test email</strong> sent from the <strong>Iotplace CRM</strong>.</p>"
            "<p>If you received this message, your SMTP connection is working and emails use the Iotplace brand template.</p>"
        )
        subject = "Iotplace CRM test — SMTP connection OK"
    else:
        body = (
            "<p>Ceci est un <strong>email de test</strong> envoyé depuis le <strong>CRM Iotplace</strong>.</p>"
            "<p>Si vous recevez ce message, la connexion SMTP fonctionne et les emails utilisent le template de marque Iotplace.</p>"
        )
        subject = "Test Iotplace CRM — connexion SMTP OK"
    return send_email(to, subject, body, site_url=site_url, locale=locale)


def _smtp_connection(cfg: dict):
    if cfg["use_tls"] and cfg["port"] == 465:
        smtp = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=30)
    else:
        smtp = smtplib.SMTP(cfg["host"], cfg["port"], timeout=30)
        if cfg["use_tls"]:
            smtp.starttls(context=ssl.create_default_context())
    smtp.login(cfg["user"], cfg["password"])
    return smtp


def test_imap_connection() -> dict:
    if not is_imap_configured():
        raise EmailError("IMAP non configuré — renseignez IMAP_HOST (ou SMTP_HOST), IMAP_USER et IMAP_PASSWORD.")
    cfg = get_imap_config()
    try:
        with _imap_connection(cfg) as imap:
            status, data = imap.select(cfg["mailbox"], readonly=True)
            count = int(data[0]) if status == "OK" and data and data[0] else 0
        return {"ok": True, "host": cfg["host"], "mailbox": cfg["mailbox"], "messages": count}
    except Exception as exc:
        raise EmailError(f"Connexion IMAP échouée : {exc}") from exc


def fetch_inbox(limit: int = 40) -> list[dict]:
    if not is_imap_configured():
        raise EmailError("IMAP non configuré.")
    cfg = get_imap_config()
    limit = max(1, min(limit, 100))
    messages: list[dict] = []

    with _imap_connection(cfg) as imap:
        imap.select(cfg["mailbox"], readonly=True)
        status, data = imap.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []
        ids = data[0].split()
        for msg_id in reversed(ids[-limit:]):
            status, fetched = imap.fetch(msg_id, "(RFC822)")
            if status != "OK" or not fetched:
                continue
            raw = fetched[0][1] if isinstance(fetched[0], tuple) else None
            if not raw:
                continue
            parsed = email.message_from_bytes(raw)
            subject = _decode_mime_header(parsed.get("Subject", ""))
            from_hdr = _decode_mime_header(parsed.get("From", ""))
            date_hdr = parsed.get("Date", "")
            body = _extract_body(parsed)
            messages.append({
                "id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                "subject": subject or "(sans objet)",
                "from": from_hdr,
                "date": date_hdr,
                "preview": (body or "")[:280],
                "body": body,
                "synced_at": datetime.now(timezone.utc).isoformat(),
            })
    return messages


def _imap_connection(cfg: dict):
    if cfg["use_ssl"]:
        imap = imaplib.IMAP4_SSL(cfg["host"], cfg["port"])
    else:
        imap = imaplib.IMAP4(cfg["host"], cfg["port"])
    imap.login(cfg["user"], cfg["password"])
    return imap


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return _html_to_text(payload.decode(charset, errors="replace"))
        return ""
    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    charset = msg.get_content_charset() or "utf-8"
    text = payload.decode(charset, errors="replace")
    if msg.get_content_type() == "text/html":
        return _html_to_text(text)
    return text

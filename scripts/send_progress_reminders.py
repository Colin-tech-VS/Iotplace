"""Email startups whose active missions have gone quiet — drives them back to the site.

A mission is "stale" when it is in escrow (or awaiting payment) and the startup has
not posted a progress update for IOTPLACE_PROGRESS_REMINDER_DAYS days (default 7).
Each reminder is throttled so a startup is not emailed more than once per window.

Usage:
  python scripts/send_progress_reminders.py            # send reminders
  python scripts/send_progress_reminders.py --dry-run  # list without sending
  python scripts/send_progress_reminders.py --days 10  # custom staleness window

Scalingo (weekly): add to the Scheduler add-on, e.g.
  "0 9 * * 1": "python scripts/send_progress_reminders.py"
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _reminder_window_days(default: int = 7) -> int:
    raw = (os.environ.get("IOTPLACE_PROGRESS_REMINDER_DAYS") or "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def main() -> int:
    parser = argparse.ArgumentParser(description="Send progress-update reminders to startups.")
    parser.add_argument("--days", type=int, default=_reminder_window_days())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from data import store
    from compte.mailer import MailDeliveryError, send_progress_reminder_email
    from crm.email_service import is_smtp_configured

    if not args.dry_run and not is_smtp_configured():
        print("SMTP non configuré — aucun email envoyé. Configurez SMTP_* ou utilisez --dry-run.")
        return 1

    cutoff_iso = (store._now() - store.timedelta(days=args.days)).isoformat()
    stale = store.get_stale_engagements(days=args.days)
    sent = skipped = 0

    for engagement in stale:
        last_reminder = engagement.get("last_reminder_at")
        if last_reminder and last_reminder > cutoff_iso:
            skipped += 1
            continue

        startup = store.get_startup(engagement.get("startup_id", ""))
        startup_user = store._user_for_startup_id(engagement.get("startup_id", ""))
        if not startup or not startup_user or not startup_user.get("email"):
            skipped += 1
            continue

        project = store.get_project(engagement.get("project_id", "")) or {}
        project_title = project.get("title", "votre projet IoT")
        email = startup_user["email"]

        if args.dry_run:
            print(f"[dry-run] reminder → {email} (mission: {project_title})")
            sent += 1
            continue

        try:
            send_progress_reminder_email(
                email,
                startup_name=startup.get("name", "votre équipe"),
                project_title=project_title,
                message_id=engagement.get("application_message_id", ""),
            )
            store.update_engagement(engagement["id"], {"last_reminder_at": store._now().isoformat()})
            sent += 1
            print(f"reminder → {email} (mission: {project_title})")
        except MailDeliveryError as exc:
            skipped += 1
            print(f"échec → {email}: {exc}", file=sys.stderr)

    print(f"Terminé — {sent} relance(s) envoyée(s), {skipped} ignorée(s) sur {len(stale)} mission(s) en attente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

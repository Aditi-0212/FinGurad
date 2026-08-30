"""
Sends the daily digest email via SMTP.

This is a standalone script, not an API endpoint — it's meant to be
triggered by a scheduler (Windows Task Scheduler, cron, or a hosted
cron service once deployed) rather than a user action, since "send
myself a daily email" isn't something that should happen on a button
click.

Configuration comes entirely from environment variables (see the
SMTP_* and DIGEST_* entries added to .env.example) — nothing is
hardcoded, per the project's own rule about not hardcoding what should
be configurable.

Run manually to test:
    python -m scripts.send_digest

Schedule on Windows (daily at 8 AM):
    Task Scheduler -> Create Task -> Trigger: Daily 8:00 AM
    Action: Start a program
      Program: C:\\path\\to\\backend\\.venv\\Scripts\\python.exe
      Arguments: -m scripts.send_digest
      Start in: C:\\path\\to\\backend
"""

import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings
from app.database.session import SessionLocal
from app.services.digest_service import build_digest_data
from app.services.digest_template import render_digest_html


def send_digest():
    settings = get_settings()

    missing = [
        name
        for name in ("smtp_host", "smtp_port", "smtp_user", "smtp_password", "digest_recipient")
        if not getattr(settings, name, None)
    ]
    if missing:
        print(f"Cannot send digest — missing settings: {', '.join(missing)}. Check your .env file.")
        sys.exit(1)

    db = SessionLocal()
    try:
        data = build_digest_data(db)
        html = render_digest_html(data)
    finally:
        db.close()

    message = MIMEMultipart("alternative")
    message["Subject"] = f"FinGuard AI Daily Digest — Health Score {data.health_score}/100"
    message["From"] = settings.smtp_user
    message["To"] = settings.digest_recipient
    message.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, settings.digest_recipient, message.as_string())

    print(f"Digest sent to {settings.digest_recipient} (health score: {data.health_score}/100)")


if __name__ == "__main__":
    send_digest()

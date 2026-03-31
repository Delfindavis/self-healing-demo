import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

developer_emails = {
    "webapp-main":    "sandrasureshpanicker@gmail.com",
    "webapp-auth":    "kavyasnairrkd2004@gmail.com",
    "webapp-payment": "mrudhulamohanan@gmail.com"
}


def send_email(service, reason):
    try:
        from monitor.db import log_email
    except ModuleNotFoundError:
        from db import log_email

    receiver = developer_emails.get(service, "admin@gmail.com")
    ts = datetime.utcnow().isoformat()

    subject = f"Critical Service Failure: {service}"
    body = f"""
Self-Healing Monitoring Alert
==============================
Service:        {service}
Failure Reason: {reason}
Time (UTC):     {ts}

The service has exceeded the maximum restart attempts.
Automatic recovery was not possible.

Manual intervention is required.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver

    if not SENDER_EMAIL or not APP_PASSWORD:
        status = "SKIPPED: missing SENDER_EMAIL/APP_PASSWORD"
        print("Email skipped: configure SENDER_EMAIL and APP_PASSWORD env vars.")
        log_email(ts, service, reason, receiver, status)
        return

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver, msg.as_string())
        server.quit()
        print(f"Email sent to {receiver}")
        log_email(ts, service, reason, receiver, "SENT")

    except Exception as e:
        print(f"Email failed: {e}")
        log_email(ts, service, reason, receiver, f"FAILED: {str(e)[:60]}")
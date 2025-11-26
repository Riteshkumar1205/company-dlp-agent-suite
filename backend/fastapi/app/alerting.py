import json
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from . import config as backend_config

CONFIG_PATH = Path(__file__).parent / "alert_config.json"

def load_alert_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"global_admins": [], "per_device_admins": {}, "alert_rules": {}}

def should_alert(event_type: str) -> bool:
    cfg = load_alert_config()
    rules = cfg.get("alert_rules", {})
    return rules.get(event_type, False)

def get_recipients(device_id: str):
    cfg = load_alert_config()
    recipients = set(cfg.get("global_admins", []))
    device_specific = cfg.get("per_device_admins", {}).get(device_id, [])
    recipients.update(device_specific)
    return list(recipients)

def send_email(to_list, subject, body, sender=None):
    if not to_list:
        return
    if sender is None:
        sender = backend_config.SMTP_CONFIG.get("sender")
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)
    try:
        s = smtplib.SMTP(backend_config.SMTP_CONFIG["host"], backend_config.SMTP_CONFIG.get("port", 587), timeout=10)
        if backend_config.SMTP_CONFIG.get("use_tls", True):
            s.starttls()
        s.login(backend_config.SMTP_CONFIG["user"], backend_config.SMTP_CONFIG["password"])
        s.sendmail(sender, to_list, msg.as_string())
        s.quit()
    except Exception as e:
        print("send_email failed", e)

def alert_admin(event: dict):
    event_type = event.get("event_type")
    device_id = event.get("device_id")
    if not should_alert(event_type):
        return
    recipients = get_recipients(device_id)
    if not recipients:
        return
    subj = f"[ALERT] {event_type} on {device_id}"
    body = json.dumps(event, indent=2)
    send_email(recipients, subj, body)

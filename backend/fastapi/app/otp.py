import random, string, time, json
from pathlib import Path
from email.mime.text import MIMEText
import smtplib

OTP_STORE = Path(__file__).parent / "otp_store.json"

def _load():
    if OTP_STORE.exists():
        return json.loads(OTP_STORE.read_text())
    return {}

def _save(d):
    OTP_STORE.write_text(json.dumps(d, indent=2))

def generate_otp(length=6, ttl_seconds=300):
    return ''.join(random.choices(string.digits, k=length)), int(time.time()) + ttl_seconds

def send_otp_email(to_email: str, otp: str, smtp_cfg: dict):
    body = f"Your Company DLP activation code is: {otp}\nValid for a few minutes."
    msg = MIMEText(body)
    msg["Subject"] = "Company DLP OTP"
    msg["From"] = smtp_cfg.get("sender", smtp_cfg.get("user"))
    msg["To"] = to_email
    try:
        s = smtplib.SMTP(smtp_cfg["host"], smtp_cfg.get("port", 587), timeout=10)
        if smtp_cfg.get("use_tls", True):
            s.starttls()
        s.login(smtp_cfg["user"], smtp_cfg["password"])
        s.sendmail(msg["From"], [to_email], msg.as_string())
        s.quit()
        return True
    except Exception:
        return False

def request_otp(email, device_id, smtp_cfg):
    otp, expiry = generate_otp()
    store = _load()
    store[device_id] = {"email": email, "otp": otp, "expiry": expiry}
    _save(store)
    return send_otp_email(email, otp, smtp_cfg)

def verify_otp(device_id, code):
    store = _load()
    rec = store.get(device_id)
    if not rec:
        return False
    if int(time.time()) > rec["expiry"]:
        del store[device_id]; _save(store); return False
    if str(code) == str(rec["otp"]):
        del store[device_id]; _save(store); return True
    return False

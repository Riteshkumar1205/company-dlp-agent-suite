import os
from dotenv import load_dotenv
load_dotenv()

SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST","smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT","587")),
    "user": os.getenv("SMTP_USER",""),
    "password": os.getenv("SMTP_PASS",""),
    "use_tls": os.getenv("SMTP_TLS","true").lower() == "true",
    "sender": os.getenv("SMTP_SENDER", os.getenv("SMTP_USER", "dlp-alerts@company.com"))
}

CERT_AUTH_ENABLED = os.getenv("CERT_AUTH_ENABLED","false").lower() == "true"

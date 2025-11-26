from fastapi import Header, HTTPException, Request
import os
from . import config
ADMIN_TOKEN = os.getenv("ADMIN_API_TOKEN","admintoken-demo")

def admin_required(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="missing auth")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"role":"admin"}

def cert_auth_required(request: Request):
    if not config.CERT_AUTH_ENABLED:
        raise HTTPException(status_code=503, detail="cert auth disabled")
    cert_subj = request.headers.get("X-SSL-CLIENT-S-DN")
    if not cert_subj:
        raise HTTPException(status_code=401, detail="client cert required")
    return {"cert_subject": cert_subj}

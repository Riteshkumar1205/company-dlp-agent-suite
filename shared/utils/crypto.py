#!/usr/bin/env python3
"""
Simple local encryption helpers using cryptography.Fernet
- Generates and stores a key at ~/.company_agent_key (secure perms)
- encrypt_json(obj) -> bytes
- decrypt_bytes(bytes) -> dict
Note: For production use a vault/KMS/HSM. This is suitable for lab/prototype.
"""

from cryptography.fernet import Fernet
from pathlib import Path
import os
import json

KEY_PATH = Path.home() / ".company_agent_key"
KEY_PATH.parent.mkdir(parents=True, exist_ok=True)

def ensure_key():
    if not KEY_PATH.exists():
        k = Fernet.generate_key()
        KEY_PATH.write_bytes(k)
        try:
            os.chmod(str(KEY_PATH), 0o600)
        except Exception:
            pass
    return KEY_PATH.read_bytes()

def encrypt_json(obj: dict) -> bytes:
    key = ensure_key()
    f = Fernet(key)
    data = json.dumps(obj).encode("utf-8")
    return f.encrypt(data)

def decrypt_bytes(b: bytes) -> dict:
    key = ensure_key()
    f = Fernet(key)
    plain = f.decrypt(b)
    return json.loads(plain.decode("utf-8"))

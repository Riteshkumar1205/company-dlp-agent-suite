import uuid, json
from pathlib import Path
from datetime import datetime

DEVICES_PATH = Path(__file__).parent / "devices.json"
DEVICES_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_devices():
    if not DEVICES_PATH.exists():
        return {}
    return json.loads(DEVICES_PATH.read_text())

def save_devices(d):
    DEVICES_PATH.write_text(json.dumps(d, indent=2))

def register_device(email: str, requested_device_id: str = None, metadata: dict = None):
    d = load_devices()
    device_id = requested_device_id or f"dev-{uuid.uuid4().hex[:12]}"
    d[device_id] = {
        "device_id": device_id,
        "owner": email,
        "metadata": metadata or {},
        "bound": False,
        "bound_info": {},
        "activated": False,
        "activation_time": None,
        "last_seen": None,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    save_devices(d)
    return device_id

def bind_device(device_id: str, mac: str = None, serial: str = None):
    d = load_devices()
    if device_id not in d:
        return False
    d[device_id]["bound"] = True
    d[device_id]["bound_info"] = {"mac": mac, "serial": serial}
    save_devices(d)
    return True

def activate_device(device_id: str):
    d = load_devices()
    if device_id not in d:
        return False
    d[device_id]["activated"] = True
    d[device_id]["activation_time"] = datetime.utcnow().isoformat() + "Z"
    save_devices(d)
    return True

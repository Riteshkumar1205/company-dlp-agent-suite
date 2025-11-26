from fastapi import APIRouter, Depends, HTTPException
from .auth import admin_required
from . import devices
router = APIRouter(prefix="/admin")

@router.get("/devices")
def list_devices(user=Depends(admin_required)):
    return devices.load_devices()

@router.get("/devices/{device_id}")
def get_device(device_id: str, user=Depends(admin_required)):
    devs = devices.load_devices()
    if device_id not in devs:
        raise HTTPException(404, "not found")
    return devs[device_id]

@router.post("/devices/{device_id}/activate")
def activate_device(device_id: str, user=Depends(admin_required)):
    ok = devices.activate_device(device_id)
    if not ok:
        raise HTTPException(404, "device not found")
    return {"status":"ok"}

@router.post("/devices/{device_id}/bind")
def bind_device(device_id: str, info: dict, user=Depends(admin_required)):
    ok = devices.bind_device(device_id, mac=info.get("mac"), serial=info.get("serial"))
    if not ok:
        raise HTTPException(404, "device not found")
    return {"status":"ok"}

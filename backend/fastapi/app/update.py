from fastapi import APIRouter
import json
from pathlib import Path
router = APIRouter(prefix="/update")
MANIFEST_PATH = Path(__file__).parent / "update_manifest.json"
if not MANIFEST_PATH.exists():
    MANIFEST_PATH.write_text(json.dumps({"latest_version":"1.0.0","channels":{"stable":{"url":""}}}))

@router.get("/manifest/{device_id}")
def get_manifest(device_id: str):
    return json.loads(MANIFEST_PATH.read_text())

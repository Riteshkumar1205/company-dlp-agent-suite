from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
import os, json, uuid, logging
from . import db, storage, schemas, auth, commands

logger = logging.getLogger("uvicorn")
app = FastAPI(title="Company DLP Collector")

STORAGE = Path(os.getenv("STORAGE_PATH", "./data/uploads"))
STORAGE.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
def startup():
    db.init_db(os.getenv("DATABASE_URL", "sqlite:///./data/collector.db"))
    storage.ensure_storage_dir(STORAGE)

@app.post("/api/v1/events")
async def receive_event(payload: dict, request: Request):
    try:
        event_id = payload.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}"
        storage_path = storage.event_json_save(STORAGE, event_id, payload)
        db.create_event(db.get_sync_session(), event_id, payload, str(storage_path))
        return {"status":"ok", "id": event_id}
    except Exception as e:
        logger.exception("receive_event failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/events/{event_id}/thumbnail")
async def receive_thumbnail(event_id: str, thumbnail: UploadFile = File(...)):
    try:
        ext = Path(thumbnail.filename).suffix or ".png"
        out_path = STORAGE / f"{event_id}_thumb{ext}"
        await storage.save_upload_async(thumbnail, out_path)
        db.attach_thumbnail(db.get_sync_session(), event_id, str(out_path))
        return {"status":"ok", "id": event_id}
    except Exception as e:
        logger.exception("thumbnail upload failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents/{device_id}/commands")
def poll_commands(device_id: str):
    try:
        return commands.fetch_and_mark_delivered_sync(device_id)
    except Exception:
        raise HTTPException(status_code=500, detail="poll error")

@app.post("/api/v1/agents/{device_id}/commands")
def create_command(device_id: str, cmd: schemas.CommandCreate, user=Depends(auth.admin_required)):
    try:
        cmd_id = commands.enqueue_command_sync(device_id, cmd.type, cmd.payload or {})
        return {"status":"ok", "id": cmd_id}
    except Exception:
        raise HTTPException(status_code=500, detail="enqueue error")

@app.get("/sample_screenshot")
def sample_screenshot():
    # Return the uploaded developer screenshot path (local file URL)
    return {"file_url": "file:///mnt/data/986e25d8-3655-4c50-af76-b09f54aebf80.png"}

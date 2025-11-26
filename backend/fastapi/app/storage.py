import json
from pathlib import Path
import aiofiles

def ensure_storage_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def event_json_save(storage_dir: Path, event_id: str, payload: dict):
    out = storage_dir / f"{event_id}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f)
    return out

async def save_upload_async(upload_file, out_path: Path):
    async with aiofiles.open(out_path, "wb") as f:
        content = await upload_file.read()
        await f.write(content)

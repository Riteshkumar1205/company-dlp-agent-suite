from PIL import Image
import imagehash
from pathlib import Path
import logging

logger = logging.getLogger("phash")

def compute_phash(path: Path):
    try:
        img = Image.open(path).convert("RGB")
        ph = imagehash.phash(img)
        return str(ph)
    except Exception:
        logger.exception("compute_phash failed")
        return None

from PIL import Image
from pathlib import Path

def make_thumbnail(src: Path, dst: Path, size=(512,512)):
    img = Image.open(src)
    img = img.convert("RGB")
    img.thumbnail(size)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, format="PNG", optimize=True)
    return dst

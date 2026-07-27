from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def store_photo(source: str, photo_dir: Path) -> str:
    src = Path(source)
    if not src.is_file() or src.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Format de photo non pris en charge")
    photo_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()[:20]
    destination = photo_dir / f"{digest}{src.suffix.lower()}"
    if not destination.exists():
        shutil.copy2(src, destination)
    return str(destination)

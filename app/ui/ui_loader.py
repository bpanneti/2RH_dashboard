from pathlib import Path
from PyQt6 import uic

FORMS_DIR = Path(__file__).resolve().parent / "forms"

def load_ui(filename: str, instance) -> None:
    path = FORMS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Fichier UI introuvable : {path}")
    uic.loadUi(str(path), instance)

import sys
from pathlib import Path

def _get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

BASE_DIR = _get_base_dir()

SYNC_FOLDER = BASE_DIR / "data" / "incoming"
PROJECTS_FOLDER = BASE_DIR / "data" / "projects"

GROQ_API_KEY = "gsk_..."
AI_TIMEOUT = 60

SYNC_FOLDER.mkdir(parents=True, exist_ok=True)
PROJECTS_FOLDER.mkdir(parents=True, exist_ok=True)

from pathlib import Path

# Main directories
CORE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = CORE_DIR.parent

# Database
DATABASE_PATH = CORE_DIR / "story_pixelai.db"

# Storage
STORAGE_DIR = CORE_DIR / "storage"
TEMP_DIR = STORAGE_DIR / "temp"
EXPORT_DIR = STORAGE_DIR / "exports"

# Google Drive
GOOGLE_DRIVE_FOLDER = "STORY_PIXELAI_STUDIO"

# Application
APP_NAME = "STORY PIXEL AI"
APP_VERSION = "0.3.0"
DEBUG = True

# Create required directories
for folder in [STORAGE_DIR, TEMP_DIR, EXPORT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


from pathlib import Path
import os

from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

# ai-dam/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables from backend/.env
ENV_FILE = PROJECT_ROOT / "backend" / ".env"
load_dotenv(ENV_FILE)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DATASET_PATH = (
    PROJECT_ROOT / "dataset"
).resolve()

DATABASE_PATH = (
    PROJECT_ROOT / "data" / "dam.db"
).resolve()

FAISS_INDEX_PATH = (
    PROJECT_ROOT / "data" / "multimodal.index.faiss"
).resolve()


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
}

PDF_EXTENSIONS = {
    ".pdf",
}

SUPPORTED_EXTENSIONS = (
    IMAGE_EXTENSIONS
    | VIDEO_EXTENSIONS
    | PDF_EXTENSIONS
)


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

DATASET_PATH.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

FAISS_INDEX_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)
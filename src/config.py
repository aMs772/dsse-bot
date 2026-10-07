import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
WEBSITE_DIR = DATA_DIR / "website"
COURSES_DIR = DATA_DIR / "courses"

CHROMA_DIR = BASE_DIR / "chroma_db"


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-3-small",
)


if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from .env")

if not CHAT_MODEL:
    raise ValueError("CHAT_MODEL is missing from .env")
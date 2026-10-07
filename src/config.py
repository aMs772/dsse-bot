import os
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
WEBSITE_DIR = DATA_DIR / "website"
COURSES_DIR = DATA_DIR / "courses"

CHROMA_DIR = BASE_DIR / "chroma_db"


def get_secret(name, default=None):
    value = os.getenv(name)

    if value:
        return value

    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
CHAT_MODEL = get_secret("CHAT_MODEL")
EMBEDDING_MODEL = get_secret(
    "EMBEDDING_MODEL",
    "text-embedding-3-small",
)


if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing")

if not CHAT_MODEL:
    raise ValueError("CHAT_MODEL is missing")
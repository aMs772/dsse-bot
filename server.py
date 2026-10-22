"""
Numa - FastAPI server for the DSSE / Tinkerers' Lab assistant.

Replaces app.py (Streamlit). The RAG pipeline in src/ is used unchanged.

Local:
    uv run uvicorn server:app --reload --port 8000

Deployed (Render sets $PORT):
    uv run uvicorn server:app --host 0.0.0.0 --port $PORT

Set NUMA_PASSWORD in the environment to put HTTP basic auth in front of the
whole site. Leave it unset and the site is open - fine locally, not fine on a
public URL, because every question spends your OpenAI credit.
"""

import base64
import os
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from src.chatbot import get_response

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

NUMA_USER = os.getenv("NUMA_USER", "dsse")
NUMA_PASSWORD = os.getenv("NUMA_PASSWORD")

app = FastAPI(title="Numa", description="IITB Innovation Chatbot")


# ----------------------------------------------------------------- auth

class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Password-gate everything, but only when NUMA_PASSWORD is set."""

    async def dispatch(self, request, call_next):
        if not NUMA_PASSWORD or request.url.path == "/api/health":
            return await call_next(request)

        supplied = request.headers.get("Authorization", "")
        authorised = False

        if supplied.startswith("Basic "):
            try:
                user, _, password = (
                    base64.b64decode(supplied[6:]).decode("utf-8").partition(":")
                )
                authorised = secrets.compare_digest(user, NUMA_USER) and \
                    secrets.compare_digest(password, NUMA_PASSWORD)
            except Exception:
                authorised = False

        if not authorised:
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Numa"'},
            )

        return await call_next(request)


app.add_middleware(BasicAuthMiddleware)


# ----------------------------------------------------------------- api

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str


# NOTE: declared with `def`, not `async def`, on purpose.
# The OpenAI calls inside the pipeline are blocking, so FastAPI runs this in a
# worker thread and one slow answer does not freeze the whole server.
@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = [m.model_dump() for m in request.history]
    answer = get_response(request.message, history)
    return ChatResponse(answer=answer)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


# Everything else (css, js, assets) is served straight from web/.
app.mount("/", StaticFiles(directory=WEB_DIR), name="web")
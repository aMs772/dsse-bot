"""
Numa - FastAPI server for the DSSE / Tinkerers' Lab assistant.

Replaces app.py (Streamlit). The RAG pipeline in src/ is used unchanged.

Run:
    uv run uvicorn server:app --reload --port 8000
Then open http://localhost:8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.chatbot import get_response

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="Numa", description="IITB Department Assistant")


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
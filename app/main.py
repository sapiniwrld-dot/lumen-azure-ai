from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.rag import answer_with_sources

app = FastAPI(
    title="Lumen Day & Knowledge Copilot",
    description="Terraform-managed AI assistant running on Azure",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Citation(BaseModel):
    number: int
    title: str
    source: str
    score: float


class AnswerResponse(BaseModel):
    answer: str
    model: str
    citations: list[Citation]


RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
_request_history: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


@app.middleware("http")
async def rate_limit_ask_requests(request: Request, call_next):
    if request.method != "POST" or request.url.path != "/ask":
        return await call_next(request)

    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else request.client.host if request.client else "unknown"
    )
    now = monotonic()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    with _rate_limit_lock:
        history = _request_history[client_ip]

        while history and history[0] <= cutoff:
            history.popleft()

        if len(history) >= RATE_LIMIT_REQUESTS:
            retry_after = max(
                1,
                int(RATE_LIMIT_WINDOW_SECONDS - (now - history[0])) + 1,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many prompts. Please wait before trying again."
                    )
                },
                headers={"Retry-After": str(retry_after)},
            )

        history.append(now)

    return await call_next(request)


@app.get("/", response_class=FileResponse)
def root() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "model": settings.chat_deployment,
        "search_index": settings.search_index,
    }


@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest) -> AnswerResponse:
    try:
        result = answer_with_sources(request.question)

        return AnswerResponse(
            answer=result["answer"],
            model=settings.chat_deployment,
            citations=result["citations"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Azure AI request failed",
        ) from exc

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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

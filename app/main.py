from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ai import answer_question
from app.config import settings

app = FastAPI(
    title="Lumen Support Copilot",
    description="Terraform-managed RAG assistant running on Azure AI",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AnswerResponse(BaseModel):
    answer: str
    model: str


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
        answer = answer_question(request.question)
        return AnswerResponse(
            answer=answer,
            model=settings.chat_deployment,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Azure AI request failed",
        ) from exc

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.rag import answer_with_sources

app = FastAPI(
    title="Lumen Support Copilot",
    description="Terraform-managed RAG assistant running on Azure AI",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class Citation(BaseModel):
    number: int
    title: str
    source: str
    score: float


class AnswerResponse(BaseModel):
    answer: str
    model: str
    citations: list[Citation]


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Lumen Support Copilot",
        "docs": "/docs",
    }


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

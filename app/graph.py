from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai import client
from app.config import settings
from app.gemini import answer_with_gemini


class AnswerState(TypedDict, total=False):
    prompt: str
    answer: str
    model: str
    azure_failed: bool


def azure_node(state: AnswerState) -> dict:
    try:
        response = client.responses.create(
            model=settings.chat_deployment,
            input=state["prompt"],
            reasoning={"effort": "low"},
            max_output_tokens=700,
        )

        answer = response.output_text
        if not answer or not answer.strip():
            return {"azure_failed": True}

        return {
            "answer": answer.strip(),
            "model": settings.chat_deployment,
            "azure_failed": False,
        }
    except Exception:
        return {"azure_failed": True}


def gemini_node(state: AnswerState) -> dict:
    return {
        "answer": answer_with_gemini(state["prompt"]),
        "model": settings.gemini_model,
    }


def route_after_azure(state: AnswerState) -> str:
    if state["azure_failed"]:
        return "gemini"
    return "done"


builder = StateGraph(AnswerState)

builder.add_node("azure", azure_node)
builder.add_node("gemini", gemini_node)

builder.add_edge(START, "azure")
builder.add_conditional_edges(
    "azure",
    route_after_azure,
    {"gemini": "gemini", "done": END},
)
builder.add_edge("gemini", END)

answer_graph = builder.compile()
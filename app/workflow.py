from typing_extensions import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from app.chat import generate_text
from app.retrieval import retrieve


class RetrievedSource(TypedDict):
    title: str
    content: str
    source: str
    score: float


class Citation(TypedDict):
    number: int
    title: str
    source: str
    score: float


class WorkflowInput(TypedDict):
    question: str


class WorkflowOutput(TypedDict):
    answer: str
    citations: list[Citation]


class WorkflowState(WorkflowInput):
    sources: NotRequired[list[RetrievedSource]]
    context: NotRequired[str]
    answer: NotRequired[str]
    citations: NotRequired[list[Citation]]


class RetrievalUpdate(TypedDict):
    sources: list[RetrievedSource]
    context: str


def retrieval_agent(state: WorkflowState) -> RetrievalUpdate:
    """Retrieve evidence and prepare numbered context for the responder."""
    sources: list[RetrievedSource] = [
        {
            "title": source["title"],
            "content": source["content"],
            "source": source["source"],
            "score": float(source["score"]),
        }
        for source in retrieve(state["question"])
    ]

    context = "\n\n".join(
        (
            f"[{position}] {source['title']}\n"
            f"{source['content']}\n"
            f"Source: {source['source']}"
        )
        for position, source in enumerate(sources, start=1)
    )

    return {
        "sources": sources,
        "context": context,
    }


def response_agent(state: WorkflowState) -> WorkflowOutput:
    """Generate a grounded answer and format its source citations."""
    prompt = f"""
You are Lumen, a customer-support assistant.

Answer only from the supplied knowledge-base context.
Cite supporting passages with references such as [1].
If the context does not contain the answer, say that you do not know.
Be concise and operationally useful.

Knowledge-base context:
{state["context"]}

Question:
{state["question"]}
"""

    answer = generate_text(prompt, max_output_tokens=500)

    citations: list[Citation] = [
        {
            "number": position,
            "title": source["title"],
            "source": source["source"],
            "score": round(source["score"], 6),
        }
        for position, source in enumerate(state["sources"], start=1)
    ]

    return {
        "answer": answer,
        "citations": citations,
    }


def build_support_workflow():
    builder = StateGraph(
        WorkflowState,
        input_schema=WorkflowInput,
        output_schema=WorkflowOutput,
    )
    builder.add_node("retrieval_agent", retrieval_agent)
    builder.add_node("response_agent", response_agent)
    builder.add_edge(START, "retrieval_agent")
    builder.add_edge("retrieval_agent", "response_agent")
    builder.add_edge("response_agent", END)

    return builder.compile()


support_workflow = build_support_workflow()


def run_support_workflow(question: str) -> WorkflowOutput:
    result = support_workflow.invoke({"question": question})

    return {
        "answer": result["answer"],
        "citations": result["citations"],
    }
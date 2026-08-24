from app.ai import client
from app.config import settings
from app.retrieval import retrieve


def answer_with_sources(question: str) -> dict:
    sources = retrieve(question)

    context = "\n\n".join(
        (
            f"[{position}] {source['title']}\n"
            f"{source['content']}\n"
            f"Source: {source['source']}"
        )
        for position, source in enumerate(sources, start=1)
    )

    prompt = f"""
You are Lumen, a customer-support assistant.

Answer only from the supplied knowledge-base context.
Cite supporting passages with bracketed references such as [1].
If the context does not contain the answer, say that you do not know.
Be concise and operationally useful.

Knowledge-base context:
{context}

Question:
{question}
"""

    response = client.responses.create(
        model=settings.chat_deployment,
        input=prompt,
        reasoning={"effort": "low"},
        max_output_tokens=500,
    )

    citations = [
        {
            "number": position,
            "title": source["title"],
            "source": source["source"],
            "score": round(source["score"], 6),
        }
        for position, source in enumerate(sources, start=1)
    ]

    return {
        "answer": response.output_text,
        "citations": citations,
    }

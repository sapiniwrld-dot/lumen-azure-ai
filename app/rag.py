from app.ai import client
from app.config import settings
from app.retrieval import retrieve

DANGEROUS_TERMS = {
    "bomb", "explosive", "weapon", "poison",
    "kill", "murder", "terrorist",
}

SUPPORT_TERMS = {
    "order", "refund", "return", "delivery", "shipping",
    "damaged", "product", "account", "password", "payment",
}


def is_dangerous_request(message: str) -> bool:
    lowered = message.lower()
    return any(term in lowered for term in DANGEROUS_TERMS)


def is_support_question(question: str) -> bool:
    words = set(question.lower().replace("?", "").split())
    return bool(words & SUPPORT_TERMS)


def answer_general_question(question: str) -> dict:
    prompt = f"""
You are Lumen, a friendly conversational personal assistant.

Respond naturally to greetings, statements, questions, and requests.
Help with everyday information and practical day planning.
Never provide instructions that facilitate weapons, explosives,
violence, illegal activity, or self-harm.
You do not currently have live web or news access. When asked for
latest or current news, clearly disclose that limitation and recommend
checking a reputable current news source.
For planning requests:
- Organize tasks into realistic time blocks.
- Include breaks and buffer time.
- Put the highest-priority work during focused hours.
- Keep the response concise and easy to scan.
- If important information is missing, state your assumptions.

Do not claim to know private facts that the user did not provide.
For medical, legal, or financial matters, encourage professional advice.

User request:
{question}
"""

    response = client.responses.create(
        model=settings.chat_deployment,
        input=prompt,
        reasoning={"effort": "low"},
        max_output_tokens=700,
    )

    return {
        "answer": response.output_text,
        "citations": [],
    }


def answer_support_question(question: str) -> dict:
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
Cite supporting passages with references such as [1].
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


def answer_with_sources(question: str) -> dict:
    if is_dangerous_request(question):
        return {
            "answer": (
                "I can't help create weapons, explosives, or plans "
                "to harm people. I can help with safe topics instead."
            ),
            "citations": [],
        }

    if is_support_question(question):
        return answer_support_question(question)

    return answer_general_question(question)

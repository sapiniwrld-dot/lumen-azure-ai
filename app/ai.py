from azure.identity import (
    DefaultAzureCredential,
    get_bearer_token_provider,
)
from openai import OpenAI

from app.config import settings

credential = DefaultAzureCredential()

token_provider = get_bearer_token_provider(
    credential,
    "https://cognitiveservices.azure.com/.default",
)

client = OpenAI(
    base_url=f"{settings.openai_endpoint.rstrip('/')}/openai/v1/",
    api_key=token_provider,
)


def answer_question(question: str) -> str:
    response = client.responses.create(
        model=settings.chat_deployment,
        input=question,
        reasoning={"effort": "low"},
        max_output_tokens=300,
    )

    return response.output_text

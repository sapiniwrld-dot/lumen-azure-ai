from functools import lru_cache

from google import genai
from google.genai import types

from app.ai import client as azure_client
from app.config import settings


SUPPORTED_CHAT_PROVIDERS = {
    "azure_openai",
    "gemini_api",
    "vertex_ai",
}


def _chat_provider() -> str:
    provider = settings.chat_provider.strip().lower()

    if provider not in SUPPORTED_CHAT_PROVIDERS:
        raise ValueError(
            "CHAT_PROVIDER must be azure_openai, gemini_api, or vertex_ai"
        )

    return provider


def active_chat_model() -> str:
    provider = _chat_provider()

    if provider == "azure_openai":
        if not settings.chat_deployment:
            raise RuntimeError(
                "AZURE_OPENAI_CHAT_DEPLOYMENT is required for Azure OpenAI"
            )
        return settings.chat_deployment

    if not settings.gemini_model:
        raise RuntimeError("GEMINI_MODEL is required for Gemini")

    return settings.gemini_model


@lru_cache(maxsize=1)
def _gemini_client() -> genai.Client:
    provider = _chat_provider()

    if provider == "gemini_api":
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY or GOOGLE_API_KEY is required for Gemini API"
            )
        return genai.Client(api_key=settings.gemini_api_key)

    if provider == "vertex_ai":
        if not settings.google_cloud_project:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT is required for Vertex AI"
            )
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            http_options=types.HttpOptions(api_version="v1"),
        )

    raise RuntimeError(
        "A Gemini client was requested for a non-Gemini provider"
    )


def generate_text(prompt: str, *, max_output_tokens: int) -> str:
    provider = _chat_provider()
    model = active_chat_model()

    if provider == "azure_openai":
        response = azure_client.responses.create(
            model=model,
            input=prompt,
            reasoning={"effort": "low"},
            max_output_tokens=max_output_tokens,
        )
        text = response.output_text
    else:
        response = _gemini_client().models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
            ),
        )
        text = response.text

    if not text or not text.strip():
        raise RuntimeError(f"{provider} returned an empty response")

    return text.strip()

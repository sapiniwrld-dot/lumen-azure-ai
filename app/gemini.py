from google import genai

from app.config import settings


def answer_with_gemini(prompt: str) -> str:
    if not settings.gemini_api_key or not settings.gemini_model:
        raise RuntimeError("Gemini fallback is not configured")

    with genai.Client(api_key=settings.gemini_api_key) as client:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

    if not response.text or not response.text.strip():
        raise RuntimeError("Gemini returned no text")

    return response.text.strip()
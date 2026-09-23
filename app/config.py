import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    chat_provider: str = os.getenv("CHAT_PROVIDER", "azure_openai")
    gemini_model: str = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )
    gemini_api_key: str | None = (
        os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    )
    google_cloud_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = os.getenv(
        "GOOGLE_CLOUD_LOCATION",
        "global",
    )
    retrieval_backend: str = os.getenv("RETRIEVAL_BACKEND", "azure_search")
    pgvector_dsn: str | None = os.getenv("PGVECTOR_DSN")
    openai_endpoint: str = required("AZURE_OPENAI_ENDPOINT")
    chat_deployment: str | None = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    embedding_deployment: str = required("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    search_endpoint: str = required("AZURE_SEARCH_ENDPOINT")
    search_index: str = required("AZURE_SEARCH_INDEX")
    storage_account: str = required("AZURE_STORAGE_ACCOUNT")
    storage_container: str = required("AZURE_STORAGE_CONTAINER")


settings = Settings()

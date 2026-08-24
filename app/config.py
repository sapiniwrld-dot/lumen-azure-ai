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
    openai_endpoint: str = required("AZURE_OPENAI_ENDPOINT")
    chat_deployment: str = required("AZURE_OPENAI_CHAT_DEPLOYMENT")
    embedding_deployment: str = required(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    search_endpoint: str = required("AZURE_SEARCH_ENDPOINT")
    search_index: str = required("AZURE_SEARCH_INDEX")
    storage_account: str = required("AZURE_STORAGE_ACCOUNT")
    storage_container: str = required("AZURE_STORAGE_CONTAINER")


settings = Settings()

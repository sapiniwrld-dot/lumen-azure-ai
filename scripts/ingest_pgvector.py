from app.pgvector_store import (
    initialize_database,
    upsert_documents,
)
from scripts.ingest import load_sections


def main() -> None:
    initialize_database()

    documents = load_sections()
    upsert_documents(documents)

    print(
        f"Indexed {len(documents)} sections into pgvector"
    )


if __name__ == "__main__":
    main()

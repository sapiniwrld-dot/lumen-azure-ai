import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.config import settings


EMBEDDING_DIMENSIONS = 1536


def _database_dsn() -> str:
    if not settings.pgvector_dsn:
        raise RuntimeError(
            "PGVECTOR_DSN is required when "
            "RETRIEVAL_BACKEND=pgvector"
        )
    return settings.pgvector_dsn


def initialize_database() -> None:
    with psycopg.connect(_database_dsn()) as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(connection)

        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                embedding VECTOR({EMBEDDING_DIMENSIONS}) NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw
            ON document_chunks
            USING hnsw (embedding vector_cosine_ops)
            """
        )


def upsert_documents(documents: list[dict]) -> None:
    if not documents:
        return

    rows = [
        (
            document["id"],
            document["title"],
            document["content"],
            document["source"],
            Vector(document["content_vector"]),
        )
        for document in documents
    ]

    with psycopg.connect(_database_dsn()) as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO document_chunks (
                    id,
                    title,
                    content,
                    source,
                    embedding
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    source = EXCLUDED.source,
                    embedding = EXCLUDED.embedding
                """,
                rows,
            )


def search_documents(
    embedding: list[float],
    limit: int = 3,
) -> list[dict]:
    query_vector = Vector(embedding)

    with psycopg.connect(_database_dsn()) as connection:
        register_vector(connection)

        rows = connection.execute(
            """
            SELECT
                title,
                content,
                source,
                1 - (embedding <=> %s) AS score
            FROM document_chunks
            ORDER BY embedding <=> %s
            LIMIT %s
            """,
            (query_vector, query_vector, limit),
        ).fetchall()

    return [
        {
            "title": row[0],
            "content": row[1],
            "source": row[2],
            "score": float(row[3]),
        }
        for row in rows
    ]
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from app import retrieval


def test_retrieve_uses_pgvector(monkeypatch) -> None:
    embedding = [0.25, 0.75]
    create_embedding = Mock(
        return_value=SimpleNamespace(
            data=[SimpleNamespace(embedding=embedding)]
        )
    )

    monkeypatch.setattr(
        retrieval,
        "client",
        SimpleNamespace(
            embeddings=SimpleNamespace(create=create_embedding)
        ),
    )
    monkeypatch.setattr(
        retrieval,
        "settings",
        SimpleNamespace(
            retrieval_backend="pgvector",
            embedding_deployment="test-embedding",
        ),
    )

    expected = [
        {
            "title": "Refund Policy",
            "content": "Refunds are available.",
            "source": "handbook.txt",
            "score": 0.95,
        }
    ]
    search_documents = Mock(return_value=expected)
    monkeypatch.setattr(
        retrieval,
        "search_documents",
        search_documents,
    )

    result = retrieval.retrieve(
        "Where is my refund?",
        limit=2,
    )

    assert result == expected
    create_embedding.assert_called_once_with(
        model="test-embedding",
        input="Where is my refund?",
    )
    search_documents.assert_called_once_with(embedding, 2)


def test_retrieve_rejects_unknown_backend(monkeypatch) -> None:
    monkeypatch.setattr(
        retrieval,
        "settings",
        SimpleNamespace(retrieval_backend="unknown"),
    )

    with pytest.raises(
        RuntimeError,
        match="RETRIEVAL_BACKEND",
    ):
        retrieval.retrieve("Test question")


def test_retrieve_keeps_azure_search_path(monkeypatch) -> None:
    embedding = [0.1, 0.2]
    create_embedding = Mock(
        return_value=SimpleNamespace(
            data=[SimpleNamespace(embedding=embedding)]
        )
    )

    monkeypatch.setattr(
        retrieval,
        "client",
        SimpleNamespace(
            embeddings=SimpleNamespace(create=create_embedding)
        ),
    )
    monkeypatch.setattr(
        retrieval,
        "settings",
        SimpleNamespace(
            retrieval_backend="azure_search",
            embedding_deployment="test-embedding",
        ),
    )

    azure_search = Mock(
        return_value=[
            {
                "title": "Shipping Policy",
                "content": "Orders ship in two days.",
                "source": "handbook.txt",
                "@search.score": 0.88,
            }
        ]
    )
    monkeypatch.setattr(
        retrieval,
        "search_client",
        SimpleNamespace(search=azure_search),
    )

    pgvector_search = Mock()
    monkeypatch.setattr(
        retrieval,
        "search_documents",
        pgvector_search,
    )

    result = retrieval.retrieve(
        "When will my order ship?",
        limit=1,
    )

    assert result == [
        {
            "title": "Shipping Policy",
            "content": "Orders ship in two days.",
            "source": "handbook.txt",
            "score": 0.88,
        }
    ]
    azure_search.assert_called_once()
    pgvector_search.assert_not_called()
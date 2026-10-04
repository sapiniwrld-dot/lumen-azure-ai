from unittest.mock import Mock

from scripts import ingest_pgvector


def test_main_ingests_sections(monkeypatch, capsys) -> None:
    documents = [
        {
            "id": "handbook-0",
            "title": "Refund Policy",
        }
    ]

    initialize_database = Mock()
    load_sections = Mock(return_value=documents)
    upsert_documents = Mock()

    monkeypatch.setattr(
        ingest_pgvector,
        "initialize_database",
        initialize_database,
    )
    monkeypatch.setattr(
        ingest_pgvector,
        "load_sections",
        load_sections,
    )
    monkeypatch.setattr(
        ingest_pgvector,
        "upsert_documents",
        upsert_documents,
    )

    ingest_pgvector.main()

    initialize_database.assert_called_once_with()
    load_sections.assert_called_once_with()
    upsert_documents.assert_called_once_with(documents)

    assert (
        capsys.readouterr().out
        == "Indexed 1 sections into pgvector\n"
    )

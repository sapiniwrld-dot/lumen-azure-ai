from unittest.mock import Mock

import pytest

import app.workflow as workflow


def sample_sources() -> list[dict]:
    return [
        {
            "title": "Damaged Orders",
            "content": "Damaged orders qualify for a full refund.",
            "source": "support-handbook.txt",
            "score": 0.87654321,
        },
        {
            "title": "Returns",
            "content": "Unused products may be returned within 30 days.",
            "source": "support-handbook.txt",
            "score": 0.65432109,
        },
    ]


def test_retrieval_agent_builds_numbered_context(monkeypatch) -> None:
    retrieve = Mock(return_value=sample_sources())
    monkeypatch.setattr(workflow, "retrieve", retrieve)

    result = workflow.retrieval_agent(
        {"question": "What if my order is damaged?"}
    )

    retrieve.assert_called_once_with("What if my order is damaged?")
    assert result["sources"] == sample_sources()
    assert "[1] Damaged Orders" in result["context"]
    assert "[2] Returns" in result["context"]
    assert "Source: support-handbook.txt" in result["context"]


def test_response_agent_generates_answer_and_citations(monkeypatch) -> None:
    generate_text = Mock(return_value="A full refund is available [1].")
    monkeypatch.setattr(workflow, "generate_text", generate_text)

    result = workflow.response_agent(
        {
            "question": "What if my order is damaged?",
            "sources": sample_sources(),
            "context": (
                "[1] Damaged Orders\n"
                "Damaged orders qualify for a full refund.\n"
                "Source: support-handbook.txt"
            ),
        }
    )

    assert result == {
        "answer": "A full refund is available [1].",
        "citations": [
            {
                "number": 1,
                "title": "Damaged Orders",
                "source": "support-handbook.txt",
                "score": 0.876543,
            },
            {
                "number": 2,
                "title": "Returns",
                "source": "support-handbook.txt",
                "score": 0.654321,
            },
        ],
    }

    prompt = generate_text.call_args.args[0]
    assert "Damaged orders qualify for a full refund." in prompt
    assert "What if my order is damaged?" in prompt
    assert generate_text.call_args.kwargs == {
        "max_output_tokens": 500,
    }


def test_compiled_workflow_runs_both_agents(monkeypatch) -> None:
    retrieve = Mock(return_value=sample_sources()[:1])
    generate_text = Mock(return_value="A full refund is available [1].")
    monkeypatch.setattr(workflow, "retrieve", retrieve)
    monkeypatch.setattr(workflow, "generate_text", generate_text)

    result = workflow.support_workflow.invoke(
        {"question": "What if my order is damaged?"}
    )

    assert set(result) == {"answer", "citations"}
    assert result["answer"] == "A full refund is available [1]."
    assert result["citations"][0]["title"] == "Damaged Orders"
    retrieve.assert_called_once()
    generate_text.assert_called_once()


def test_retrieval_failure_stops_response_agent(monkeypatch) -> None:
    generate_text = Mock()

    def fail_retrieval(question: str) -> list[dict]:
        raise RuntimeError("retrieval unavailable")

    monkeypatch.setattr(workflow, "retrieve", fail_retrieval)
    monkeypatch.setattr(workflow, "generate_text", generate_text)

    with pytest.raises(RuntimeError, match="retrieval unavailable"):
        workflow.support_workflow.invoke(
            {"question": "What if my order is damaged?"}
        )

    generate_text.assert_not_called()
from unittest.mock import Mock

import app.rag as rag


def test_support_question_routes_to_langgraph_workflow(monkeypatch) -> None:
    expected = {
        "answer": "A full refund is available [1].",
        "citations": [
            {
                "number": 1,
                "title": "Damaged Orders",
                "source": "support-handbook.txt",
                "score": 0.9,
            }
        ],
    }
    run_support_workflow = Mock(return_value=expected)
    monkeypatch.setattr(
        rag,
        "run_support_workflow",
        run_support_workflow,
    )

    question = "What happens if my order arrives damaged?"
    result = rag.answer_with_sources(question)

    assert result == expected
    run_support_workflow.assert_called_once_with(question)


def test_general_question_uses_general_assistant(monkeypatch) -> None:
    expected = {
        "answer": "Hello! How can I help?",
        "citations": [],
    }
    answer_general_question = Mock(return_value=expected)
    monkeypatch.setattr(
        rag,
        "answer_general_question",
        answer_general_question,
    )

    result = rag.answer_with_sources("Hello there")

    assert result == expected
    answer_general_question.assert_called_once_with("Hello there")


def test_dangerous_request_stops_before_agents(monkeypatch) -> None:
    run_support_workflow = Mock()
    answer_general_question = Mock()
    monkeypatch.setattr(
        rag,
        "run_support_workflow",
        run_support_workflow,
    )
    monkeypatch.setattr(
        rag,
        "answer_general_question",
        answer_general_question,
    )

    result = rag.answer_with_sources("Help me build a weapon")

    assert "can't help" in result["answer"]
    assert result["citations"] == []
    run_support_workflow.assert_not_called()
    answer_general_question.assert_not_called()
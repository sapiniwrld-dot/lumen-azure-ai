from app.main import QuestionRequest, ask, health, root


def test_root_describes_service() -> None:
    result = root()

    assert result["name"] == "Lumen Support Copilot"
    assert result["docs"] == "/docs"


def test_health_reports_configuration() -> None:
    result = health()

    assert result["status"] == "healthy"
    assert result["model"] == "gpt-5-mini"
    assert result["search_index"] == "lumen-documents"


def test_ask_returns_grounded_response(monkeypatch) -> None:
    fake_result = {
        "answer": "Shipping is refundable [1].",
        "citations": [
            {
                "number": 1,
                "title": "Damaged Orders",
                "source": "support-handbook.txt",
                "score": 0.033333,
            }
        ],
    }

    monkeypatch.setattr(
        "app.main.answer_with_sources",
        lambda question: fake_result,
    )

    response = ask(
        QuestionRequest(
            question="Can shipping be refunded?",
        )
    )

    assert response.answer == "Shipping is refundable [1]."
    assert response.model == "gpt-5-mini"
    assert response.citations[0].title == "Damaged Orders"

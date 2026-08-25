from fastapi.testclient import TestClient

from app.config import settings

from app.main import (
    QuestionRequest,
    _request_history,
    app,
    ask,
    health,
    root,
)


def test_root_serves_chat_interface() -> None:
    response = root()

    assert response.path == "app/static/index.html"


def test_health_reports_configuration() -> None:
    result = health()

    assert result["status"] == "healthy"
    assert result["model"] == settings.chat_deployment
    assert result["search_index"] == settings.search_index


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
    assert response.model == settings.chat_deployment
    assert response.citations[0].title == "Damaged Orders"


def test_ask_rate_limit(monkeypatch) -> None:
    fake_result = {
        "answer": "Test response.",
        "citations": [],
    }
    monkeypatch.setattr(
        "app.main.answer_with_sources",
        lambda question: fake_result,
    )

    client = TestClient(app)
    headers = {"x-forwarded-for": "203.0.113.10"}
    _request_history.clear()

    try:
        for _ in range(10):
            response = client.post(
                "/ask",
                json={"question": "Hello"},
                headers=headers,
            )
            assert response.status_code == 200

        blocked = client.post(
            "/ask",
            json={"question": "One more"},
            headers=headers,
        )

        assert blocked.status_code == 429
        assert "Retry-After" in blocked.headers
        assert blocked.json()["detail"].startswith("Too many prompts")
    finally:
        _request_history.clear()

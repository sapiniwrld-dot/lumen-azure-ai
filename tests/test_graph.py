from unittest.mock import Mock

import app.graph as graph_module


def test_azure_failure_uses_gemini(monkeypatch):
    azure_call = Mock(side_effect=RuntimeError("Azure unavailable"))
    gemini_call = Mock(return_value="Gemini fallback answer")

    monkeypatch.setattr(
        graph_module.client.responses,
        "create",
        azure_call,
    )
    monkeypatch.setattr(
        graph_module,
        "answer_with_gemini",
        gemini_call,
    )

    result = graph_module.answer_graph.invoke({"prompt": "Hello"})

    azure_call.assert_called_once()
    gemini_call.assert_called_once_with("Hello")
    assert result["answer"] == "Gemini fallback answer"
    assert result["model"] == graph_module.settings.gemini_model
    assert result["azure_failed"] is True
def test_azure_success_skips_gemini(monkeypatch):
    azure_call = Mock(
        return_value=Mock(output_text="Azure answer")
    )
    gemini_call = Mock()

    monkeypatch.setattr(
        graph_module.client.responses,
        "create",
        azure_call,
    )
    monkeypatch.setattr(
        graph_module,
        "answer_with_gemini",
        gemini_call,
    )

    result = graph_module.answer_graph.invoke({"prompt": "Hello"})

    azure_call.assert_called_once()
    gemini_call.assert_not_called()
    assert result["answer"] == "Azure answer"
    assert result["model"] == graph_module.settings.chat_deployment
    assert result["azure_failed"] is False
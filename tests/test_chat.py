from types import SimpleNamespace
from unittest.mock import Mock

import app.chat as chat


def provider_settings(provider: str) -> SimpleNamespace:
    return SimpleNamespace(
        chat_provider=provider,
        chat_deployment="test-azure-chat",
        gemini_model="gemini-test-model",
        gemini_api_key="test-gemini-key",
        google_cloud_project="test-google-project",
        google_cloud_location="global",
    )


def test_generate_text_with_azure_openai(monkeypatch) -> None:
    create = Mock(
        return_value=SimpleNamespace(output_text="Azure answer")
    )
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(create=create)
    )

    monkeypatch.setattr(
        chat,
        "settings",
        provider_settings("azure_openai"),
    )
    monkeypatch.setattr(chat, "azure_client", fake_client)

    result = chat.generate_text("Hello", max_output_tokens=100)

    assert result == "Azure answer"
    create.assert_called_once_with(
        model="test-azure-chat",
        input="Hello",
        reasoning={"effort": "low"},
        max_output_tokens=100,
    )


def test_generate_text_with_gemini_api(monkeypatch) -> None:
    generate_content = Mock(
        return_value=SimpleNamespace(text="Gemini answer")
    )
    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    )
    client_constructor = Mock(return_value=fake_client)

    monkeypatch.setattr(
        chat,
        "settings",
        provider_settings("gemini_api"),
    )
    monkeypatch.setattr(chat.genai, "Client", client_constructor)
    chat._gemini_client.cache_clear()

    try:
        result = chat.generate_text("Hello", max_output_tokens=120)
    finally:
        chat._gemini_client.cache_clear()

    assert result == "Gemini answer"
    client_constructor.assert_called_once_with(
        api_key="test-gemini-key"
    )

    call = generate_content.call_args
    assert call.kwargs["model"] == "gemini-test-model"
    assert call.kwargs["contents"] == "Hello"
    assert call.kwargs["config"].max_output_tokens == 120


def test_generate_text_with_vertex_ai(monkeypatch) -> None:
    generate_content = Mock(
        return_value=SimpleNamespace(text="Vertex answer")
    )
    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    )
    client_constructor = Mock(return_value=fake_client)

    monkeypatch.setattr(
        chat,
        "settings",
        provider_settings("vertex_ai"),
    )
    monkeypatch.setattr(chat.genai, "Client", client_constructor)
    chat._gemini_client.cache_clear()

    try:
        result = chat.generate_text("Hello", max_output_tokens=140)
    finally:
        chat._gemini_client.cache_clear()

    assert result == "Vertex answer"

    client_kwargs = client_constructor.call_args.kwargs
    assert client_kwargs["vertexai"] is True
    assert client_kwargs["project"] == "test-google-project"
    assert client_kwargs["location"] == "global"
    assert client_kwargs["http_options"].api_version == "v1"

    call = generate_content.call_args
    assert call.kwargs["model"] == "gemini-test-model"
    assert call.kwargs["contents"] == "Hello"
    assert call.kwargs["config"].max_output_tokens == 140

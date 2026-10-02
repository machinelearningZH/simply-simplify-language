"""Offline contracts across the real Streamlit UI and model-client boundary."""

import sys
from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from _streamlit_app import app_core


@pytest.fixture
def app(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[AppTest, list[dict], list[str | None]]]:
    requests: list[dict] = []

    def complete(**kwargs: object) -> SimpleNamespace:
        requests.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response[0]))]
        )

    response = ["<einfachesprache>**Grüße** aus Zürich.</einfachesprache>"]
    monkeypatch.syspath_prepend(str(app_core.APP_DIR))
    monkeypatch.setitem(sys.modules, "app_core", app_core)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "openai.OpenAI",
        lambda **kwargs: SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=complete))
        ),
    )
    monkeypatch.setattr(app_core, "start_understandability_loading", lambda: None)
    monkeypatch.setattr(app_core, "get_zix", lambda text: 1.5)
    monkeypatch.setattr(app_core, "get_cefr", lambda score: "B1")
    test_app = AppTest.from_file(str(app_core.app_path("sprache-vereinfachen.py")))
    try:
        yield test_app, requests, response
    finally:
        # Streamlit resource caches are process-global, including the fake client.
        import streamlit as st

        st.cache_resource.clear()


def test_simplification_routes_request_and_preserves_result_on_rerun(
    app: tuple,
) -> None:
    test_app, requests, _ = app
    test_app.run()
    assert not test_app.exception
    assert requests == []
    test_app.text_area(key="key_textinput").input("Der Ausgangstext.")
    next(
        button for button in test_app.button if button.label == "Vereinfachen"
    ).click().run()
    assert not test_app.exception
    assert len(requests) == 1
    request = requests[0]
    config = app_core.load_yaml_config(app_core.repo_path("config.yaml"))
    selected = config["models"][0]
    assert request["model"] == selected["id"]
    assert request["extra_body"]["provider"]["sort"] == "price"
    assert "temperature" not in request
    assert request["max_tokens"] == config["api"]["max_tokens"]
    assert request["messages"][0]["role"] == "system"
    assert "<einfachesprache>" in request["messages"][0]["content"]
    assert request["messages"][1]["content"].endswith("Der Ausgangstext.")
    assert test_app.text_area[1].value == "Grüsse aus Zürich."
    test_app.text_area(key="key_textinput").input("Geänderter Ausgangstext.").run()
    assert not test_app.exception
    assert test_app.text_area[1].value == "Grüsse aus Zürich."
    assert len(requests) == 1


@pytest.mark.parametrize(
    "response", [None, "", "Ungetaggte Antwort", "<einfachesprache> </einfachesprache>"]
)
def test_invalid_model_output_shows_error_without_success_result(
    app: tuple, response: str | None
) -> None:
    test_app, requests, responses = app
    responses[0] = response
    test_app.run()
    test_app.text_area(key="key_textinput").input("Ausgangstext")
    next(
        button for button in test_app.button if button.label == "Vereinfachen"
    ).click().run()
    assert not test_app.exception
    assert len(requests) == 1
    assert any("Fehler bei der Abfrage" in error.value for error in test_app.error)
    assert "last_result" not in test_app.session_state


def test_empty_input_prevents_model_request(app: tuple) -> None:
    test_app, requests, _ = app
    test_app.run()
    next(
        button for button in test_app.button if button.label == "Vereinfachen"
    ).click().run()
    assert not test_app.exception
    assert [error.value for error in test_app.error] == ["Bitte gib einen Text ein."]
    assert requests == []


def test_analysis_uses_selected_model_routing_and_language(app: tuple) -> None:
    test_app, requests, responses = app
    responses[0] = "<leichtesprache>Eine Analyse.</leichtesprache>"
    test_app.run()
    config = app_core.load_yaml_config(app_core.repo_path("config.yaml"))
    selected = next(
        model
        for model in config["models"]
        if isinstance(model.get("subprovider"), list)
    )
    test_app.radio[0].set_value(selected["name"])
    test_app.toggle[0].set_value(True).run()
    test_app.text_area(key="key_textinput").input("Ein Satz.")
    next(
        button for button in test_app.button if button.label == "Analysieren"
    ).click().run()
    assert not test_app.exception
    assert len(requests) == 1
    request = requests[0]
    assert request["model"] == selected["id"]
    assert request["extra_body"]["provider"] == {
        "only": selected["subprovider"],
        "sort": "price",
        "allow_fallbacks": True,
        "require_parameters": True,
    }
    assert "<leichtesprache>" in request["messages"][0]["content"]
    assert "Satz für Satz" in request["messages"][1]["content"]
    assert "lass den Rest weg" not in request["messages"][1]["content"]
    assert test_app.text_area[1].label == "Deine Analyse"
    assert test_app.text_area[1].value == "Eine Analyse."

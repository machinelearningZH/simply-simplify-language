"""Behavioral gaps identified by the mutation report, using offline boundaries."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from _streamlit_app import app_core


@pytest.mark.parametrize(
    "effort", ["none", "minimal", "low", "medium", "high", "xhigh", "max"]
)
def test_reasoning_without_provider_requires_parameter_support(effort: str) -> None:
    assert app_core.model_request_parameters({"reasoning_effort": effort}) == {
        "extra_body": {
            "reasoning": {"effort": effort},
            "provider": {"sort": "price", "require_parameters": True},
        }
    }


@pytest.mark.parametrize("provider", ["a", "0", "openai/flex", "vendor_name/region-1"])
def test_provider_slug_accepts_documented_character_shapes(provider: str) -> None:
    assert app_core.model_request_parameters({"subprovider": provider}) == {
        "extra_body": {
            "provider": {
                "only": [provider],
                "sort": "price",
                "allow_fallbacks": True,
                "require_parameters": True,
            }
        }
    }


@pytest.mark.parametrize(
    "provider",
    ["/openai", "openai/", "openai//flex", "_openai", "openai\n", ("openai",)],
)
def test_provider_slug_rejects_malformed_segments(provider: object) -> None:
    with pytest.raises(ValueError, match="subprovider"):
        app_core.model_request_parameters({"subprovider": provider})


def test_tag_extraction_preserves_multiline_content_and_escapes_tag() -> None:
    assert (
        app_core.extract_tagged_response(
            "ignore <a.b>\nFirst line.\n\nSecond line.\n</a.b> ignore", "a.b"
        )
        == "First line.\n\nSecond line."
    )
    with pytest.raises(ValueError, match="expected"):
        app_core.extract_tagged_response("<axb>Other tag</axb>", "a.b")


def test_yaml_parse_failure_does_not_hide_error_or_hold_file(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("broken: [", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        app_core.load_yaml_config(path)
    path.write_text("label: Grüezi Zürich\n", encoding="utf-8")
    assert app_core.load_yaml_config(path) == {"label": "Grüezi Zürich"}
    with pytest.raises(FileNotFoundError):
        app_core.load_yaml_config(tmp_path / "missing.yaml")


def test_project_info_default_and_missing_file() -> None:
    assert app_core.load_project_info() == app_core.app_path(
        "utils_expander.md"
    ).read_text(encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        app_core.load_project_info(app_core.app_path("missing-info.md"))


def test_log_payload_has_stable_schema_and_millisecond_duration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed = datetime(2026, 1, 2, 3, 4, 5)
    clock = Mock()
    clock.now.return_value = fixed
    monkeypatch.setattr(app_core, "datetime", clock)
    assert app_core.build_log_payload(
        text="Grüezi",
        response="Antwort",
        do_analysis=True,
        do_simplification=False,
        do_one_click=True,
        leichte_sprache=True,
        model_choice="Offline model",
        time_processed=1.23456,
        success=False,
        datetime_format="%d.%m.%Y %H:%M:%S",
    ) == {
        "timestamp": "02.01.2026 03:04:05",
        "input_chars": 6,
        "response_chars": 7,
        "do_analysis": True,
        "do_simplification": False,
        "do_one_click": True,
        "leichte_sprache": True,
        "model_choice": "Offline model",
        "time_processed_seconds": 1.235,
        "success": False,
    }


def test_formatter_plain_record_interpolates_message_and_honors_date_format() -> None:
    record = logging.LogRecord(
        "offline.logger",
        logging.WARNING,
        "/app/service.py",
        12,
        "Grüezi %s",
        ("Zürich",),
        None,
    )
    record.created = 0
    formatter = app_core.JSONFormatter(datefmt="%Y/%m/%d")
    formatter.converter = time.gmtime
    rendered = formatter.format(record)
    assert "Grüezi Zürich" in rendered
    assert json.loads(rendered) == {
        "level": "WARNING",
        "logger": "offline.logger",
        "message": "Grüezi Zürich",
        "module": "service",
        "timestamp": "1970/01/01",
    }


def test_logger_defaults_then_absolute_path_and_level_filtering(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    logger = app_core.configure_event_logger({"enabled": True}, base_dir=tmp_path)
    assert logger is logging.getLogger("simply_simplify_language.events")
    app_core.write_event_log(logger, {"sequence": 1})
    destination = tmp_path / "absolute.log"
    logger = app_core.configure_event_logger(
        {"enabled": True, "filename": str(destination), "level": "WARNING"},
        base_dir=tmp_path / "nonexistent",
    )
    with caplog.at_level(logging.INFO):
        app_core.write_event_log(logger, {"sequence": 2})
        logger.warning("Grüezi Zürich")
    for handler in logger.handlers:
        handler.flush()
    assert caplog.records == []
    assert json.loads((tmp_path / "app.log").read_text(encoding="utf-8"))["event"] == {
        "sequence": 1
    }
    entries = [
        json.loads(line)
        for line in destination.read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 1
    assert entries[0]["message"] == "Grüezi Zürich"
    assert entries[0]["level"] == "WARNING"


def test_one_click_failure_does_not_score_even_nonempty_response() -> None:
    score, cefr = Mock(), Mock()
    assert app_core.format_one_click_results(
        {"A": (False, "private details"), "B": (True, " \n ")},
        score_fn=score,
        cefr_fn=cefr,
    ) == (
        False,
        "\n----- Fehlgeschlagen: A, B -----\n\nFür diese Modelle konnte kein Ergebnis erstellt werden.",
    )
    score.assert_not_called()
    cefr.assert_not_called()


def test_one_click_sections_have_readable_separators() -> None:
    assert app_core.format_one_click_results(
        {"A": (True, "First"), "B": (True, "Second")},
        score_fn=lambda text: 0.0,
        cefr_fn=lambda score: "B1",
    ) == (
        True,
        "\n----- Ergebnis von A (Verständlichkeit: 0, Niveau etwa B1) -----\n\nFirst"
        "\n\n\n\n----- Ergebnis von B (Verständlichkeit: 0, Niveau etwa B1) -----\n\nSecond",
    )


def test_logging_defaults_to_disabled() -> None:
    logger = app_core.configure_event_logger({})
    assert logger.disabled is True
    assert logger.handlers == []


def test_background_loading_does_not_prevent_process_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    # Record the loader call in this process: mutmut's stats plugin is not
    # initialized in a standalone interpreter. Actual mutant IDs are forwarded.
    monkeypatch.setattr(app_core, "_understandability_future", None)
    monkeypatch.setattr(
        app_core, "_import_understandability_functions", lambda: (str, str)
    )
    app_core.start_understandability_loading().result(timeout=2)
    child_env = os.environ.copy()
    if child_env.get("MUTANT_UNDER_TEST") == "stats":
        child_env.pop("MUTANT_UNDER_TEST")
    # The worker deliberately never finishes. Process exit is the public daemon
    # behavior; subprocess.run kills and reaps the child if a mutation hangs it.
    script = """
from threading import Event
from _streamlit_app import app_core
started = Event()
def load():
    started.set()
    Event().wait()
app_core._import_understandability_functions = load
app_core.start_understandability_loading()
assert started.wait(2)
"""
    completed = subprocess.run(
        ["uv", "run", "--active", "--offline", "--no-sync", "python", "-c", script],
        check=False,
        capture_output=True,
        timeout=5,
        env=child_env,
    )
    assert completed.returncode == 0, completed.stderr.decode()

import json
import logging
import sys
from concurrent.futures import Future
from threading import Event
from unittest.mock import Mock

import pytest

from _streamlit_app.app_core import (
    APP_DIR,
    REPO_ROOT,
    JSONFormatter,
    ResultState,
    ScoreClassification,
    _complete_understandability_load,
    app_path,
    build_log_payload,
    classify_understandability,
    configure_event_logger,
    create_prompt,
    extract_tagged_response,
    format_one_click_results,
    format_understandability_message,
    get_cefr,
    get_zix,
    load_project_info,
    load_understandability_functions,
    load_yaml_config,
    repo_path,
    result_models_used,
    rounded_score,
    start_understandability_loading,
    strip_markdown,
    temperature_request_parameters,
    write_event_log,
)
from _streamlit_app.utils_prompts import (
    REWRITE_COMPLETE,
    REWRITE_CONDENSED,
    RULES_ES,
    RULES_LS,
    SYSTEM_MESSAGE_ES,
    SYSTEM_MESSAGE_LS,
    TEMPLATE_ANALYSIS_ES,
    TEMPLATE_ANALYSIS_LS,
    TEMPLATE_ES,
    TEMPLATE_LS,
)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (-3, ScoreClassification("hard", "schwer verständlich", "red")),
        (-2, ScoreClassification("medium", "nur mässig verständlich", "orange")),
        (-1, ScoreClassification("medium", "nur mässig verständlich", "orange")),
        (0, ScoreClassification("good", "gut verständlich", "green")),
        (5, ScoreClassification("good", "gut verständlich", "green")),
    ],
)
def test_classify_understandability_maps_score_to_band(score, expected):
    assert classify_understandability(score, limit_hard=0, limit_medium=-2) == expected


@pytest.mark.parametrize(
    ("limit_hard", "limit_medium"),
    [
        (-2, 0),
        (0, 0),
    ],
)
def test_classify_understandability_rejects_invalid_thresholds(
    limit_hard, limit_medium
):
    with pytest.raises(ValueError, match="limit_medium must be lower than limit_hard"):
        classify_understandability(
            0,
            limit_hard=limit_hard,
            limit_medium=limit_medium,
        )


def test_extract_tagged_response_requires_non_empty_matching_tag():
    response = "<einfachesprache>Erster Text.</einfachesprache>"

    assert extract_tagged_response(response, "einfachesprache") == "Erster Text."

    with pytest.raises(ValueError, match="expected <leichtesprache>"):
        extract_tagged_response(response, "leichtesprache")

    with pytest.raises(ValueError, match="empty"):
        extract_tagged_response(
            "<einfachesprache>   </einfachesprache>", "einfachesprache"
        )


def test_temperature_request_parameters_omits_model_default():
    assert temperature_request_parameters("default") == {}


def test_temperature_request_parameters_includes_float_override():
    assert temperature_request_parameters(0.5) == {"temperature": 0.5}


@pytest.mark.parametrize("temperature", ["0.5", 1, True, None])
def test_temperature_request_parameters_rejects_invalid_values(temperature):
    with pytest.raises(ValueError, match="'default' or a float"):
        temperature_request_parameters(temperature)


def test_format_one_click_results_reports_partial_failures_without_error_details():
    success, output = format_one_click_results(
        {
            "Model A": (True, "Vereinfachter Text."),
            "Model B": (False, "timeout with provider details"),
        },
        score_fn=lambda text: 1.4,
        cefr_fn=lambda score: "B1",
    )

    assert success is True
    assert "Ergebnis von Model A" in output
    assert "Fehlgeschlagen: Model B" in output
    assert "timeout with provider details" not in output


def test_format_one_click_results_fails_when_all_models_fail():
    success, output = format_one_click_results(
        {
            "Model A": (False, "first failure"),
            "Model B": (False, "second failure"),
        },
        score_fn=lambda text: 0,
        cefr_fn=lambda score: "B2",
    )

    assert success is False
    assert "Model A" in output
    assert "Model B" in output


def test_build_log_payload_omits_raw_text_and_response():
    payload = build_log_payload(
        text="sensitive input",
        response="sensitive response",
        do_analysis=False,
        do_simplification=True,
        do_one_click=False,
        leichte_sprache=False,
        model_choice="Model A",
        time_processed=1.23,
        success=True,
        datetime_format="%Y-%m-%d %H:%M:%S",
    )

    serialized = json.dumps(payload)
    assert payload["input_chars"] == len("sensitive input")
    assert payload["response_chars"] == len("sensitive response")
    assert "sensitive input" not in serialized
    assert "sensitive response" not in serialized


@pytest.mark.parametrize(
    ("one_click", "expected"),
    [
        (False, "Model A"),
        (True, "Model A, Model B"),
    ],
)
def test_result_models_used_selects_models_for_processing_mode(one_click, expected):
    result = ResultState(
        source_text="original text",
        response="generated output",
        analysis=False,
        simplification=not one_click,
        one_click=one_click,
        model_choice="Model A",
        model_names=("Model A", "Model B"),
        time_processed=1.2,
        score_source=-1.5,
    )

    assert result_models_used(result) == expected


def test_create_prompt_einfache_sprache_assembles_es_template_and_complete_rules():
    prompt, system = create_prompt(
        "Quelltext",
        analysis=False,
        leichte_sprache=False,
        condense_text=False,
    )

    assert prompt == TEMPLATE_ES.format(
        rules=RULES_ES, completeness=REWRITE_COMPLETE, prompt="Quelltext"
    )
    assert system == SYSTEM_MESSAGE_ES


def test_create_prompt_leichte_sprache_condense_flag_selects_completeness_block():
    condensed, condensed_system = create_prompt(
        "Quelltext",
        analysis=False,
        leichte_sprache=True,
        condense_text=True,
    )
    complete, _ = create_prompt(
        "Quelltext",
        analysis=False,
        leichte_sprache=True,
        condense_text=False,
    )

    assert condensed == TEMPLATE_LS.format(
        rules=RULES_LS, completeness=REWRITE_CONDENSED, prompt="Quelltext"
    )
    assert complete == TEMPLATE_LS.format(
        rules=RULES_LS, completeness=REWRITE_COMPLETE, prompt="Quelltext"
    )
    assert condensed_system == SYSTEM_MESSAGE_LS


def test_create_prompt_analysis_uses_analysis_template_without_completeness_block():
    prompt, system = create_prompt(
        "Quelltext",
        analysis=True,
        leichte_sprache=False,
        condense_text=True,
    )

    # Analysis has no {completeness} slot, so the condense flag must be ignored.
    assert prompt == TEMPLATE_ANALYSIS_ES.format(rules=RULES_ES, prompt="Quelltext")
    assert system == SYSTEM_MESSAGE_ES


def test_create_prompt_analysis_uses_leichte_sprache_rules_and_system_message():
    prompt, system = create_prompt(
        "Quelltext",
        analysis=True,
        leichte_sprache=True,
        condense_text=False,
    )

    assert prompt == TEMPLATE_ANALYSIS_LS.format(rules=RULES_LS, prompt="Quelltext")
    assert system == SYSTEM_MESSAGE_LS


def test_strip_markdown_removes_headers_and_emphasis():
    text = (
        "# Titel\n## Untertitel\nDies ist **fett** und *kursiv* und __auch__ und _so_."
    )

    result = strip_markdown(text)

    assert "#" not in result
    assert "*" not in result
    assert "_" not in result
    assert "Titel" in result
    assert "fett" in result
    assert "kursiv" in result


def test_extract_tagged_response_joins_multiple_matches_with_newline():
    response = (
        "<einfachesprache>Erster Teil.</einfachesprache>"
        "Zwischentext"
        "<einfachesprache>Zweiter Teil.</einfachesprache>"
    )

    assert extract_tagged_response(response, "einfachesprache") == (
        "Erster Teil.\nZweiter Teil."
    )


def test_format_understandability_message_embeds_label_score_and_cefr():
    classification = ScoreClassification("good", "gut verständlich", "green")

    message = format_understandability_message(
        subject="Originaltext",
        rounded_score=3,
        cefr="B1",
        classification=classification,
    )

    assert "Originaltext" in message
    assert ":green[gut verständlich]" in message
    assert "3 auf einer Skala" in message
    assert ":green[Sprachniveau B1]" in message


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (1.4, 1),
        (1.5, 2),
        (-1.6, -2),
        (-0.2, 0),
    ],
)
def test_rounded_score_rounds_to_nearest_int(score, expected):
    assert rounded_score(score) == expected


def test_format_one_click_results_treats_whitespace_only_success_as_failure():
    success, output = format_one_click_results(
        {
            "Model A": (True, "   \n  "),
            "Model B": (True, "Echtes Ergebnis."),
        },
        score_fn=lambda text: 1.0,
        cefr_fn=lambda score: "B1",
    )

    assert success is True
    assert "Fehlgeschlagen: Model A" in output
    assert "Ergebnis von Model B" in output


def test_format_one_click_results_returns_generic_error_for_no_responses():
    success, output = format_one_click_results(
        {},
        score_fn=Mock(),
        cefr_fn=Mock(),
    )

    assert success is False
    assert output == "Es ist ein Fehler aufgetreten."


def test_app_path_and_repo_path_resolve_relative_to_known_roots():
    assert app_path("data", "file.parq") == APP_DIR / "data" / "file.parq"
    assert repo_path("config.yaml") == REPO_ROOT / "config.yaml"


def test_load_yaml_config_parses_mapping(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("model: test\nvalues:\n  - 1\n  - 2\n", encoding="utf-8")

    config = load_yaml_config(config_file)

    assert config == {"model": "test", "values": [1, 2]}


def test_load_project_info_reads_text_from_given_path(tmp_path):
    info_file = tmp_path / "info.md"
    info_file.write_text("Projektinfo", encoding="utf-8")

    assert load_project_info(info_file) == "Projektinfo"


def test_understandability_dependency_is_loaded_only_when_needed(monkeypatch):
    calls = []

    def score_fn(text):
        calls.append(("score", text))
        return 1.5

    def cefr_fn(score):
        calls.append(("cefr", score))
        return "B1"

    monkeypatch.setattr(
        "_streamlit_app.app_core.load_understandability_functions",
        lambda: (score_fn, cefr_fn),
    )

    assert get_zix("Ein Text.") == 1.5
    assert get_cefr(1.5) == "B1"
    assert calls == [("score", "Ein Text."), ("cefr", 1.5)]


def test_understandability_background_load_is_shared(monkeypatch):
    import_started = Event()
    allow_import_to_finish = Event()
    functions = (lambda text: 1.0, lambda score: "B1")

    def slow_import():
        import_started.set()
        allow_import_to_finish.wait(timeout=1)
        return functions

    monkeypatch.setattr("_streamlit_app.app_core._understandability_future", None)
    monkeypatch.setattr(
        "_streamlit_app.app_core._import_understandability_functions", slow_import
    )

    first_future = start_understandability_loading()
    assert import_started.wait(timeout=1)
    second_future = start_understandability_loading()

    assert first_future is second_future
    assert first_future.done() is False

    allow_import_to_finish.set()
    assert first_future.result(timeout=1) is functions


def test_load_understandability_functions_returns_shared_future_result(monkeypatch):
    functions = (lambda text: 1.0, lambda score: "B1")
    future = Future()
    future.set_result(functions)
    monkeypatch.setattr(
        "_streamlit_app.app_core.start_understandability_loading",
        lambda: future,
    )

    assert load_understandability_functions() is functions


def test_understandability_background_load_exposes_import_failure(monkeypatch):
    future = Future()
    error = RuntimeError("ZIX import failed")

    def fail_import():
        raise error

    monkeypatch.setattr(
        "_streamlit_app.app_core._import_understandability_functions",
        fail_import,
    )

    _complete_understandability_load(future)

    with pytest.raises(RuntimeError, match="ZIX import failed") as captured:
        future.result()
    assert captured.value is error


def test_json_formatter_emits_structured_payload_with_event_and_exception():
    formatter = JSONFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="model_request",
            args=(),
            exc_info=sys.exc_info(),
        )
    record.event = {"key": "value"}

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "model_request"
    assert payload["event"] == {"key": "value"}
    assert "ValueError: boom" in payload["exception"]


def test_configure_event_logger_disabled_when_not_enabled():
    logger = configure_event_logger({"enabled": False})

    assert logger.disabled is True
    assert logger.handlers == []


def test_configure_event_logger_writes_json_lines_to_relative_file(tmp_path):
    logger = configure_event_logger(
        {"enabled": True, "level": "INFO", "filename": "events.log"},
        base_dir=tmp_path,
    )

    try:
        assert logger.disabled is False

        write_event_log(logger, {"input_chars": 5, "success": True})
        for handler in logger.handlers:
            handler.flush()

        log_file = tmp_path / "events.log"
        assert log_file.exists()
        line = log_file.read_text(encoding="utf-8").strip()
        entry = json.loads(line)
        assert entry["message"] == "model_request"
        assert entry["event"] == {"input_chars": 5, "success": True}
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_write_event_log_does_not_emit_for_disabled_logger():
    logger = Mock(spec=logging.Logger)
    logger.disabled = True

    write_event_log(logger, {"input_chars": 1})

    logger.info.assert_not_called()

import json
import logging
import sys

import pytest

from _streamlit_app.app_core import (
    APP_DIR,
    REPO_ROOT,
    JSONFormatter,
    ResultState,
    app_path,
    build_log_payload,
    classify_understandability,
    configure_event_logger,
    create_prompt,
    extract_tagged_response,
    format_one_click_results,
    format_understandability_message,
    load_project_info,
    load_yaml_config,
    repo_path,
    result_models_used,
    rounded_score,
    strip_markdown,
    write_event_log,
)
from _streamlit_app.app_core import (
    ScoreClassification,
)


def test_classify_understandability_uses_ordered_thresholds():
    assert classify_understandability(-3, limit_hard=0, limit_medium=-2).key == "hard"
    assert classify_understandability(-1, limit_hard=0, limit_medium=-2).key == "medium"
    assert classify_understandability(0, limit_hard=0, limit_medium=-2).key == "good"


def test_classify_understandability_rejects_inverted_thresholds():
    with pytest.raises(ValueError, match="limit_medium must be lower than limit_hard"):
        classify_understandability(0, limit_hard=-2, limit_medium=0)


def test_extract_tagged_response_requires_non_empty_matching_tag():
    response = "<einfachesprache>Erster Text.</einfachesprache>"

    assert extract_tagged_response(response, "einfachesprache") == "Erster Text."

    with pytest.raises(ValueError, match="expected <leichtesprache>"):
        extract_tagged_response(response, "leichtesprache")

    with pytest.raises(ValueError, match="empty"):
        extract_tagged_response(
            "<einfachesprache>   </einfachesprache>", "einfachesprache"
        )


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


def test_result_state_preserves_generated_output_across_reruns():
    result = ResultState(
        source_text="original text",
        response="generated output",
        analysis=False,
        simplification=True,
        one_click=False,
        model_choice="Model A",
        model_names=("Model A", "Model B"),
        time_processed=1.2,
        score_source=-1.5,
    )

    assert result.source_text == "original text"
    assert result.response == "generated output"
    assert result.score_source == -1.5
    assert result_models_used(result) == "Model A"


def test_result_models_used_lists_all_models_for_one_click():
    result = ResultState(
        source_text="original text",
        response="generated output",
        analysis=False,
        simplification=False,
        one_click=True,
        model_choice="Model A",
        model_names=("Model A", "Model B"),
        time_processed=1.2,
        score_source=2.0,
    )

    assert result_models_used(result) == "Model A, Model B"


def test_create_prompt_einfache_sprache_uses_es_rules_and_keeps_all_information():
    prompt, system = create_prompt(
        "Quelltext",
        analysis=False,
        leichte_sprache=False,
        condense_text=False,
    )

    assert "Quelltext" in prompt
    assert "<einfachesprache>" in prompt
    assert "Einfache Sprache" in system
    # Non-condensed mode must instruct the model to keep all information.
    assert "Kürze niemals Informationen" in prompt


def test_create_prompt_leichte_sprache_condensed_switches_completeness_rule():
    condensed, _ = create_prompt(
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

    assert "<leichtesprache>" in condensed
    assert "Konzentriere dich auf das Wichtigste" in condensed
    assert "Konzentriere dich auf das Wichtigste" not in complete
    assert "Kürze niemals Informationen" in complete


def test_create_prompt_analysis_ignores_condense_and_uses_analysis_template():
    prompt, system = create_prompt(
        "Quelltext",
        analysis=True,
        leichte_sprache=False,
        condense_text=True,
    )

    assert "analysier" in prompt.lower()
    assert "Satz für Satz" in prompt
    # Completeness rules do not belong in the analysis prompt.
    assert "Kürze niemals Informationen" not in prompt
    assert "Einfache Sprache" in system


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


def test_classify_understandability_treats_thresholds_as_inclusive_lower_bounds():
    # A score exactly on limit_medium is no longer "hard".
    assert classify_understandability(-2, limit_hard=0, limit_medium=-2).key == "medium"
    # A score exactly on limit_hard is "good".
    assert classify_understandability(0, limit_hard=0, limit_medium=-2).key == "good"


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


def test_rounded_score_rounds_to_nearest_int():
    assert rounded_score(1.4) == 1
    assert rounded_score(1.5) == 2
    assert rounded_score(-1.6) == -2


def test_rounded_score_never_returns_negative_zero():
    result = rounded_score(-0.2)

    assert result == 0
    # Guard against the "-0" string representation leaking into the UI.
    assert str(result) == "0"


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


def test_app_path_and_repo_path_resolve_relative_to_known_roots():
    assert app_path("data", "file.parq") == APP_DIR / "data" / "file.parq"
    assert repo_path("config.yaml") == REPO_ROOT / "config.yaml"
    assert APP_DIR.parent == REPO_ROOT


def test_load_yaml_config_parses_mapping(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("model: test\nvalues:\n  - 1\n  - 2\n", encoding="utf-8")

    config = load_yaml_config(config_file)

    assert config == {"model": "test", "values": [1, 2]}


def test_load_project_info_reads_text_from_given_path(tmp_path):
    info_file = tmp_path / "info.md"
    info_file.write_text("Projektinfo", encoding="utf-8")

    assert load_project_info(info_file) == "Projektinfo"


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


def test_write_event_log_is_noop_for_disabled_logger(tmp_path):
    logger = configure_event_logger({"enabled": False})

    # Must not raise even though there is no handler/file attached.
    write_event_log(logger, {"input_chars": 1})

    assert list(tmp_path.iterdir()) == []

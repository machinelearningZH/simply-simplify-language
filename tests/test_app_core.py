import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import Mock

import pytest

from _streamlit_app.app_core import (
    APP_DIR,
    REPO_ROOT,
    JSONFormatter,
    ResultState,
    ScoreClassification,
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
    model_request_parameters,
    repo_path,
    result_models_used,
    rounded_score,
    start_understandability_loading,
    strip_markdown,
    temperature_request_parameters,
    write_event_log,
)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (-3, ScoreClassification("schwer verständlich", "red")),
        (-2, ScoreClassification("nur mässig verständlich", "orange")),
        (-1, ScoreClassification("nur mässig verständlich", "orange")),
        (0, ScoreClassification("gut verständlich", "green")),
        (5, ScoreClassification("gut verständlich", "green")),
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


def test_model_request_parameters_preserves_defaults() -> None:
    expected = {"extra_body": {"provider": {"sort": "price"}}}
    assert model_request_parameters({"id": "example/model"}) == expected
    assert (
        model_request_parameters(
            {"reasoning_effort": "default", "subprovider": "default"}
        )
        == expected
    )


def test_model_request_parameters_applies_reasoning_and_strict_provider() -> None:
    assert model_request_parameters(
        {"reasoning_effort": "high", "subprovider": "google-vertex/us-east5"}
    ) == {
        "extra_body": {
            "reasoning": {"effort": "high"},
            "provider": {
                "only": ["google-vertex/us-east5"],
                "allow_fallbacks": True,
                "require_parameters": True,
                "sort": "price",
            },
        }
    }


def test_model_request_parameters_routes_among_allowed_providers_by_price() -> None:
    assert model_request_parameters({"subprovider": ["openai/flex", "openai"]}) == {
        "extra_body": {
            "provider": {
                "only": ["openai/flex", "openai"],
                "allow_fallbacks": True,
                "require_parameters": True,
                "sort": "price",
            }
        }
    }


@pytest.mark.parametrize("effort", ["invalid", None, True, 1])
def test_model_request_parameters_rejects_invalid_reasoning(effort: object) -> None:
    with pytest.raises(ValueError, match="reasoning_effort"):
        model_request_parameters({"reasoning_effort": effort})


@pytest.mark.parametrize(
    "provider",
    [
        "",
        "OpenAI Provider",
        None,
        True,
        "../openai",
        [],
        ["default"],
        [1],
        ["openai", ""],
    ],
)
def test_model_request_parameters_rejects_invalid_provider(provider: object) -> None:
    with pytest.raises(ValueError, match="subprovider"):
        model_request_parameters({"subprovider": provider})


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


@pytest.mark.parametrize("analysis", [False, True])
@pytest.mark.parametrize(
    ("leichte_sprache", "language", "level", "tag", "rule"),
    [
        (
            False,
            "Einfache Sprache",
            "B1 bis A2",
            "einfachesprache",
            "höchstens 12 Wörtern",
        ),
        (True, "Leichte Sprache", "A2 bis A1", "leichtesprache", "maximal 85 Zeichen"),
    ],
)
def test_prompt_preserves_source_and_language_contract(
    analysis: bool,
    leichte_sprache: bool,
    language: str,
    level: str,
    tag: str,
    rule: str,
) -> None:
    # Literal contract anchors protect routing without duplicating template assembly.
    source = "Grüsse: {rules} und <Beispiel> bleiben erhalten."
    prompt, system = create_prompt(
        source, analysis=analysis, leichte_sprache=leichte_sprache, condense_text=False
    )
    assert prompt.endswith(source)
    assert prompt.count(source) == 1
    assert language in prompt and language in system
    assert level in system
    assert f"<{tag}>" in prompt and f"<{tag}>" in system
    assert rule in prompt
    if analysis:
        assert "Satz für Satz" in prompt
        assert "Mache einen Vorschlag für einen vereinfachten Satz." in prompt
    else:
        assert "ALLE Informationen" in prompt


@pytest.mark.parametrize("analysis", [False, True])
@pytest.mark.parametrize("leichte_sprache", [False, True])
def test_condensing_changes_only_leichte_sprache_rewrites(
    analysis: bool, leichte_sprache: bool
) -> None:
    options = {"analysis": analysis, "leichte_sprache": leichte_sprache}
    complete, system = create_prompt("Quelltext", condense_text=False, **options)
    condensed, condensed_system = create_prompt(
        "Quelltext", condense_text=True, **options
    )
    assert condensed_system == system
    if leichte_sprache and not analysis:
        assert "ALLE Informationen" in complete
        assert "lass den Rest weg" in condensed
        assert "ALLE Informationen" not in condensed
    else:
        assert condensed == complete


def test_strip_markdown_removes_headers_and_emphasis():
    text = (
        "# Titel\n## Untertitel\nDies ist **fett** und *kursiv* und __auch__ und _so_."
    )

    result = strip_markdown(text)

    assert result == "Titel\nUntertitel\nDies ist fett und kursiv und auch und so."


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
    classification = ScoreClassification("gut verständlich", "green")

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


@pytest.fixture
def isolated_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reset shared cache only for isolation; assertions use the public loader API.
    monkeypatch.setattr("_streamlit_app.app_core._understandability_future", None)


def test_understandability_background_load_serves_concurrent_callers(
    monkeypatch: pytest.MonkeyPatch, isolated_loader: None
) -> None:
    import_started = Event()
    release_import = Event()
    imports = []

    def slow_import() -> tuple:
        imports.append(1)
        import_started.set()
        if not release_import.wait(timeout=5):
            raise TimeoutError("Test did not release loader")
        return (lambda text: {"Ein Text.": 1.5}[text], lambda score: {1.5: "B1"}[score])

    monkeypatch.setattr(
        "_streamlit_app.app_core._import_understandability_functions", slow_import
    )
    future = start_understandability_loading()
    try:
        assert import_started.wait(timeout=5)
        assert not future.done()
        with ThreadPoolExecutor(max_workers=4) as executor:
            callers = [
                executor.submit(start_understandability_loading) for _ in range(4)
            ]
            shared = [caller.result(timeout=5) for caller in callers]
        assert all(result is future for result in shared)
    finally:
        release_import.set()
        future.result(timeout=5)

    assert get_zix("Ein Text.") == 1.5
    assert get_cefr(1.5) == "B1"
    assert len(imports) == 1


def test_understandability_load_failure_reaches_public_callers(
    monkeypatch: pytest.MonkeyPatch, isolated_loader: None
) -> None:
    def fail_import() -> tuple:
        raise RuntimeError("ZIX import failed")

    monkeypatch.setattr(
        "_streamlit_app.app_core._import_understandability_functions", fail_import
    )
    future = start_understandability_loading()
    with pytest.raises(RuntimeError, match="ZIX import failed"):
        future.result(timeout=5)
    for operation in (
        load_understandability_functions,
        lambda: get_zix("Text"),
        lambda: get_cefr(1),
    ):
        with pytest.raises(RuntimeError, match="ZIX import failed"):
            operation()


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


def test_reconfiguring_logging_replaces_destination_and_disabled_logging_stops_writes(
    tmp_path: Path,
) -> None:
    logger = configure_event_logger(
        {"enabled": True, "filename": "first.log"}, base_dir=tmp_path
    )
    write_event_log(logger, {"sequence": 1})
    logger = configure_event_logger(
        {"enabled": True, "filename": "second.log"}, base_dir=tmp_path
    )
    write_event_log(logger, {"sequence": 2})
    logger = configure_event_logger({})
    write_event_log(logger, {"sequence": 3})
    first = [
        json.loads(line)["event"]
        for line in (tmp_path / "first.log").read_text().splitlines()
    ]
    second = [
        json.loads(line)["event"]
        for line in (tmp_path / "second.log").read_text().splitlines()
    ]
    assert first == [{"sequence": 1}]
    assert second == [{"sequence": 2}]


def test_one_click_preserves_each_text_and_its_own_score() -> None:
    def score(text: str) -> float:
        return {"Erster Text.": 1.4, "Zweiter Text.": -2.6}[text]

    def cefr(value: float) -> str:
        return {1: "B1", -3: "C1"}[value]

    success, output = format_one_click_results(
        {
            "Model A": (True, "Erster Text."),
            "Model B": (True, "Zweiter Text."),
            "Model C": (False, "private failure details"),
            "Model D": (True, "   "),
        },
        score_fn=score,
        cefr_fn=cefr,
    )
    assert success is True
    assert (
        "Model A (Verständlichkeit: 1, Niveau etwa B1) -----\n\nErster Text." in output
    )
    assert (
        "Model B (Verständlichkeit: -3, Niveau etwa C1) -----\n\nZweiter Text."
        in output
    )
    assert "Fehlgeschlagen: Model C, Model D" in output
    assert "private failure details" not in output

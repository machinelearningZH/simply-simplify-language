import json

import pytest

from _streamlit_app.app_core import (
    ResultState,
    build_log_payload,
    classify_understandability,
    extract_tagged_response,
    format_one_click_results,
    result_models_used,
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
    )

    assert result.source_text == "original text"
    assert result.response == "generated output"
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
    )

    assert result_models_used(result) == "Model A, Model B"

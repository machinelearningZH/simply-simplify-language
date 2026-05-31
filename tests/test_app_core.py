import json

import pytest

from _streamlit_app.app_core import (
    ResultState,
    build_log_payload,
    classify_understandability,
    create_prompt,
    extract_tagged_response,
    format_one_click_results,
    result_models_used,
    strip_markdown,
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

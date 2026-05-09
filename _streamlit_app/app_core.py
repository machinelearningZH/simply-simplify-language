import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import yaml

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent


@dataclass(frozen=True)
class ScoreClassification:
    key: str
    label: str
    color: str


def app_path(*parts: str) -> Path:
    """Resolve a path relative to the Streamlit app directory."""
    return APP_DIR.joinpath(*parts)


def repo_path(*parts: str) -> Path:
    """Resolve a path relative to the repository root."""
    return REPO_ROOT.joinpath(*parts)


def load_yaml_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_project_info(path: Path | None = None) -> str:
    project_info_path = path or app_path("utils_expander.md")
    return project_info_path.read_text(encoding="utf-8")


def classify_understandability(
    score: float,
    *,
    limit_hard: float,
    limit_medium: float,
) -> ScoreClassification:
    if limit_medium >= limit_hard:
        raise ValueError("limit_medium must be lower than limit_hard")

    if score < limit_medium:
        return ScoreClassification("hard", "schwer verständlich", "red")
    if score < limit_hard:
        return ScoreClassification("medium", "nur mässig verständlich", "orange")
    return ScoreClassification("good", "gut verständlich", "green")


def format_understandability_message(
    subject: str,
    rounded_score: int,
    cefr: str,
    classification: ScoreClassification,
) -> str:
    return (
        f"Dein {subject} ist **:{classification.color}[{classification.label}]**. "
        f"({rounded_score} auf einer Skala von -10 bis 10). "
        f"Das entspricht etwa dem **:{classification.color}[Sprachniveau {cefr}]**."
    )


def extract_tagged_response(response: str, tag: str) -> str:
    result = re.findall(
        rf"<{re.escape(tag)}>(.*?)</{re.escape(tag)}>", response, re.DOTALL
    )
    extracted = "\n".join(result).strip()
    if not result:
        raise ValueError(f"Model response did not contain expected <{tag}> tags")
    if extracted == "":
        raise ValueError(f"Model response contained empty <{tag}> tags")
    return extracted


def rounded_score(score: float) -> int:
    # Adding 0 avoids displaying negative zero after rounding.
    return int(round(score, 0) + 0)


def format_one_click_results(
    responses: dict[str, tuple[bool, str]],
    *,
    score_fn: Callable[[str], float],
    cefr_fn: Callable[[float], str],
) -> tuple[bool, str]:
    response_texts = []
    failed_models = []

    for name, (success, response) in responses.items():
        if success and response.strip():
            zix = rounded_score(score_fn(response))
            cefr = cefr_fn(zix)
            response_texts.append(
                f"\n----- Ergebnis von {name} "
                f"(Verständlichkeit: {zix}, Niveau etwa {cefr}) -----\n\n{response}"
            )
        else:
            failed_models.append(name)

    if failed_models:
        response_texts.append(
            "\n----- Fehlgeschlagen: "
            f"{', '.join(failed_models)} -----\n\n"
            "Für diese Modelle konnte kein Ergebnis erstellt werden."
        )

    if not any(
        success and response.strip() for success, response in responses.values()
    ):
        return False, "\n\n\n".join(response_texts) or "Es ist ein Fehler aufgetreten."

    return True, "\n\n\n".join(response_texts)


def build_log_payload(
    *,
    text: str,
    response: str,
    do_analysis: bool,
    do_simplification: bool,
    do_one_click: bool,
    leichte_sprache: bool,
    model_choice: str,
    time_processed: float,
    success: bool,
    datetime_format: str = "%Y-%m-%d %H:%M:%S",
) -> dict[str, object]:
    return {
        "timestamp": datetime.now().strftime(datetime_format),
        "input_chars": len(text),
        "response_chars": len(response),
        "do_analysis": do_analysis,
        "do_simplification": do_simplification,
        "do_one_click": do_one_click,
        "leichte_sprache": leichte_sprache,
        "model_choice": model_choice,
        "time_processed_seconds": round(time_processed, 3),
        "success": success,
    }


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "timestamp": self.formatTime(record, self.datefmt),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_event_logger(
    logging_config: dict, *, base_dir: Path = APP_DIR
) -> logging.Logger:
    logger = logging.getLogger("simply_simplify_language.events")

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    if not logging_config.get("enabled", False):
        logger.disabled = True
        return logger

    logger.disabled = False
    logger.setLevel(logging_config.get("level", "INFO"))
    logger.propagate = False

    log_path = Path(logging_config.get("filename", "app.log"))
    if not log_path.is_absolute():
        log_path = base_dir / log_path

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    return logger


def write_event_log(logger: logging.Logger, payload: dict[str, object]) -> None:
    if logger.disabled:
        return
    logger.info("model_request", extra={"event": payload})

# AGENTS Guidelines (Python)

Guidelines for agent-assisted development in Python projects managed with `uv`.

This file defines project defaults for repositories created from this template. Follow the required rules for all work in this repo; treat stack sections as preferred choices only when the project needs that capability.

## Instruction Priority

When instructions conflict, follow this order:

1. User request
2. Safety and security constraints
3. Existing repo patterns
4. This file

## Process & Security

- **Scope**: Work only in this repo.
- **Approvals**: **ALWAYS** ask before adding dependencies, installing packages, fetching external resources, or calling external services. Routine `uv sync` is allowed when it only installs dependencies already declared in this repo.
- **Secrets**: Store in `.env`, load with `python-dotenv`. Never hardcode or commit secrets.
- **Assumptions**: Surface inconsistencies, unclear intent, and ambiguous requirements; ask for clarification before proceeding. Push back on bad ideas and present trade-offs when relevant.
- **Simplicity**: Favor simple, explicit, maintainable solutions that meet requirements without over-engineering.
- **Scope Discipline**: Only modify code directly related to the current task. Never change, move, or remove unrelated code, comments, or logic, even if it seems wrong or unclear. Flag unrelated issues separately.
- **Cleanup**: Remove dead code, temporary files, and dev artifacts after each step. Release resources (files, connections, temp dirs) with `with` context managers or `atexit` for global cleanup.
- **Self-Check Before Finishing**: Before presenting a solution, verify: (1) Did I make assumptions I should have clarified? (2) Is this the simplest solution? (3) Did I change unrelated code? (4) What alternatives or trade-offs should I mention?
- **Save durable findings in NOTES.md**: Capture non-obvious insights that should not be rediscovered later: root causes, failed approaches, confirmed constraints, refactoring risks, and important decisions. Do not add noisy step-by-step logs.
- **TODOs go in PLAN.md**: Keep actionable next steps, open tasks, follow-up ideas, deferred work, and open questions in this file. Treat `PLAN.md` as the working store for what should happen next, not `NOTES.md`. If either file is needed and does not exist yet, create it.

## Security First

- Treat security as a design constraint, not a final checklist. Prefer the smallest safe data access, network access, file permissions, and dependency surface that meet the task.
- Never commit secrets, tokens, credentials, private keys, raw personal data, or sensitive operational data. Redact them from logs, errors, fixtures, docs, and examples.
- Validate and constrain untrusted inputs at boundaries: CLI arguments, config files, uploaded files, HTTP responses, model outputs, scraped content, and user-provided paths.
- Avoid unsafe execution patterns: no `eval`, `exec`, shell injection, unsafe deserialization, path traversal, unchecked downloads, or dynamic imports from untrusted input.
- Before adding dependencies or external services, consider supply-chain risk, maintenance status, license fit, and whether the standard library or an existing dependency is enough.
- If you find a security issue, stop broad changes, document the risk, and propose the smallest focused fix. Do not bury security-relevant changes inside unrelated refactors.

## Environment and Execution (`uv` Only)

Use `uv` for all Python environment management and local Python execution. Do not run or manage Python code with Pylance tools, manually created virtual environments, `venv`, `virtualenv`, Conda, Poetry, Pipenv, direct `python`, direct `pip`, direct `pytest`, direct `ruff`, or any other Python runner or package manager.

Use the latest stable Python version that package compatibility allows. Set the supported version range in `pyproject.toml`; this template starts at Python 3.12+.

Allowed patterns:

```bash
uv sync                 # Lock/Sync
uv add [--dev] <pkg>    # Add dependency
uv run <cmd>            # Run in env
```

Required examples:

```bash
uv run python -m ai_project_template.main
uv run pytest
uv run ruff check .
uv run ruff format .
```

After dependency or lockfile changes, run `uv sync`. If a tool or assistant offers Python execution outside `uv`, translate it into an equivalent `uv run ...` command instead.

## Dependency Policy

- Do not import a package unless it is already declared in `pyproject.toml` or was first added with `uv add` / `uv add --dev` after approval.
- Keep runtime dependencies in `[project].dependencies` and development-only tools in `[dependency-groups].dev`.
- Keep `[tool.uv] exclude-newer = "7 days"` so dependency resolution uses packages at least seven days old, reducing supply-chain risk.
- If a package appears in the preferred stack below but is not declared yet, treat it as a recommendation, not as available code.

## Python Conventions

- **Types**: Modern syntax (`list[str]`, `X | None`, `Self`). No `typing.List`.
- **Data**: Use `dataclasses` or `TypedDict`.
- **Paths**: `pathlib.Path` only.
- **Errors**: Specific exceptions with messages. No bare `except:`.
- **Formatting**: f-strings. Use debug format `f"{var=}"` → outputs `var=value`.

## Configuration

- **Settings**: Store user-tunable runtime settings in `config.yaml`, loaded with `pyyaml` when configuration is needed. Examples: model names, temperatures, token limits, timeouts, retry counts, file paths, feature flags, and thresholds.
- **Secrets**: Store in `.env`, load with `python-dotenv`. Never commit to git.
- **No magic values**: Values that a project user, operator, or maintainer might reasonably change belong in configuration, not inline constants. Keep internal constants in code when changing them would require code knowledge or should not be part of normal configuration.
- **Tooling config**: Keep package, lint, format, and test configuration in `pyproject.toml` or the tool's native config file, not in `config.yaml`.

## Logging

Use the `logging` module with JSON output for structured logs. Include at least level, message, module/logger, timestamp, and exception details when present.

Minimal example:

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "timestamp": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
```

## Principles

1. **Flat Architecture**: Explicit, linear control flow. No metaclasses, `exec`, or dynamic attribute generation.
2. **Predictable**: Consistent layout, standard patterns, deterministic tests.
3. **Modular**: Decoupled modules, config-driven behavior.
4. **Quality**: Descriptive names, structured logging.

## Code Review Standards

- **Maintainability**: Flag unreachable code, unused imports or variables, misleading names, avoidable duplication, inconsistent local style, and functions that do too many things. When a split is useful, name the responsibility boundary rather than asking for a vague refactor.
- **Simplification**: Prefer standard library tools and existing project helpers over hand-rolled logic. Use comprehensions, generator expressions, early returns, and fewer intermediate variables only when they make the code clearer.
- **Performance**: Call out algorithmic issues, repeated work in loops, unnecessary I/O in hot paths, N+1 query patterns, excessive allocation or copying, blocking work inside async code, missing `await`, and inappropriate threading or multiprocessing choices. Explain the expected impact; avoid speculative micro-optimizations.
- **Python Fit**: Add type hints to public APIs and non-trivial functions. Use idiomatic constructs such as `enumerate`, `zip`, unpacking, f-strings, `with` for resources, `pathlib`, and structured data types when they clarify behavior. Avoid mutable default arguments and silent failures.

## Documentation

- **Comments/Docstrings**: Explain _why_. Follow PEP 257.
- **README**: Concise usage/examples. No fluff.
- **Files**: Avoid unnecessary docs. Prefer README/AGENTS.md unless the project clearly needs a dedicated document, such as architecture notes, API docs, deployment notes, data documentation, or model cards.

## Testing

- **Location**: `tests/` directory, mirroring source structure.
- **Naming**: `test_<module>.py`, functions `test_<behavior>()`.
- **Fixtures**: Use `conftest.py` for shared fixtures.
- **Approach**: Work test-driven wherever it makes sense. For new behavior, bug fixes, and refactors, add or update the narrowest useful test first unless the task is documentation-only, infrastructure-only, or otherwise not testable. Prefer red/green/refactor: start with a failing test, make the smallest change needed to pass, then refactor while tests stay green.
- **External services**: Do not make live network, API, or model-provider calls in tests unless explicitly requested. Mock external systems and use small local fixtures.
- **Data and ML**: Use deterministic seeds where relevant. Keep large datasets, generated outputs, and caches out of git unless they are intentional source artifacts.
- **Run**: `uv run pytest -v` (verbose) or `uv run pytest -x` (stop on first failure).

## Git

- **Commits**: Use conventional commits: `type(scope): message`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
  - Example: `feat(auth): add OAuth2 login flow`
- **Branches**: `feature/<name>`, `fix/<name>`, `refactor/<name>`
- **Keep clean**: Commit small, logical changes. No WIP commits on main.
- **Commit suggestion**: After writing or changing code, always suggest an appropriate conventional commit message for the actual scope of the change.

## Code Quality

```bash
uv run ruff format .          # Format
uv run ruff check . [--fix]   # Lint
uv run pytest                 # Test
uv run ruff format . && uv run ruff check . && uv run pytest  # All checks
```

## Core Stack

Preferred defaults when the project needs these capabilities. Add missing packages with `uv add` after approval before importing them.

- **Config**: `pyyaml` for YAML, `python-dotenv` for env vars.
- **CLI**: `typer` rather than `argparse`. Use type hints, `typer.Argument()`, `typer.Option()`, and Enum for fixed choices.
- **HTTP**: `httpx` for HTTP clients, especially async requests.
- **Output**: `rich` (`Console`, `Table`) for terminal output.

## Domain-Specific Stack

Preferred defaults for common project types. Ignore entries that do not apply to the current project.

- **FastAPI**: Pydantic validation, `app/routers/` modules, dependency injection, `async` I/O.
- **Streamlit**: `st.sidebar` for controls, `st.session_state`, `@st.cache_data`.
- **LLM**: OpenRouter via OpenAI-compatible client. Load API keys from `.env`. Store user-tunable runtime settings in `config.yaml`, such as model, temperature, token limits, endpoint, timeouts, and retry counts. Use `ThreadPoolExecutor` for simple concurrent blocking calls.
- **Embeddings**: `sentence-transformers` (local, e.g., `intfloat/multilingual-e5-small`).
- **Scraping**: Start with plain HTTP requests, using `httpx` or `requests` whenever possible. Use headless browser automation such as `playwright` only when necessary, for example when the target depends on client-side rendering, browser-driven interaction, or anti-bot flows that direct HTTP cannot handle reliably.
- **Data Science**: Jupyter, pandas (vectorized), pyarrow/parquet, scikit-learn, seaborn.
- **Document Parsing**: Use `docling` by default for DOCX and PDF, exporting to Markdown (`export_to_markdown`). Optimize Docling for maximum speed and parallel processing: parse text and text tables first, disable OCR and VLMs, skip image descriptions, and use an empty placeholder string for images. Use `pymupdf` when Markdown is not needed, or `pymupdf4llm` when Markdown is needed and a lighter alternative is sufficient.

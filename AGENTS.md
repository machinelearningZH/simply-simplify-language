# AGENTS Guidelines (Python)

Defaults for agent-assisted Python projects managed with `uv`. Follow required rules everywhere; treat stack sections as preferred choices only when that capability is needed.

## Priority

When instructions conflict, follow:

1. User request
2. Safety/security constraints
3. Existing repo patterns
4. This file

## Required Process

- **Scope**: Work only inside this repo. Change only files relevant to the task; never move, remove, or rewrite unrelated code/comments/logic, even if it seems wrong. Flag unrelated issues separately.
- **Approvals**: Always ask before adding dependencies, installing packages, fetching external resources, or calling external services. `uv sync` is allowed when it only installs dependencies already declared here.
- **Assumptions**: Surface inconsistencies, unclear intent, ambiguous requirements, and risky trade-offs; ask before proceeding when needed. Push back on bad ideas with concrete alternatives.
- **Simplicity**: Prefer small, explicit, maintainable changes that satisfy the request without over-engineering.
- **Cleanup**: Remove dead code, temp files, and dev artifacts after each step. Release files/connections/temp dirs with `with` or `atexit`.
- **Artifacts**: Keep large datasets, generated outputs, and caches out of git unless they are intentional source artifacts.
- **Before finishing**: Check: Did I clarify needed assumptions? Is this the simplest solution? Did I avoid unrelated changes? What alternatives/trade-offs should I mention?
- **Durable memory**: Put non-obvious root causes, failed approaches, confirmed constraints, refactoring risks, and important decisions in `NOTES.md`. Keep actionable next steps, open tasks/questions, deferred ideas, and follow-ups in `PLAN.md`, the working task store. Create either file only when needed; avoid noisy step logs.

## Security

- Treat security as a design constraint, not a final checklist. Prefer the smallest safe data, network, file-permission, and dependency surface.
- Never hardcode or commit secrets, tokens, credentials, private keys, raw personal data, or sensitive operational data. Store secrets in `.env`, load with `python-dotenv`, and redact sensitive values from logs, errors, fixtures, docs, and examples.
- Validate and constrain untrusted inputs at boundaries: CLI args, config files, uploaded files, HTTP responses, model outputs, scraped content, and user-provided paths.
- Avoid unsafe execution/deserialization: no `eval`, `exec`, shell injection, unsafe deserialization, path traversal, unchecked downloads, or dynamic imports from untrusted input.
- Before adding dependencies or external services, consider supply-chain risk, maintenance status, license fit, and whether the standard library or an existing dependency is enough.
- If you find a security issue, stop broad changes, document the risk, and propose the smallest focused fix. Do not bury security-relevant changes inside unrelated refactors.

## `uv` Environment

Use `uv` for all Python environment management and local Python execution. Do not use Pylance execution, direct `python`/`pip`/`pytest`/`ruff`, manually created venvs, `virtualenv`, Conda, Poetry, Pipenv, or other Python runners/package managers. Translate any assistant/tool suggestion into `uv run ...`.

Use the latest stable Python version compatible with packages. Set the supported range in `pyproject.toml`; this template starts at Python 3.12+.

Allowed commands:

```bash
uv sync
uv add [--dev] <pkg>
uv run <cmd>
```

Required examples:

```bash
uv run python -m ai_project_template.main
uv run pytest
uv run pytest -v
uv run pytest -x
uv run ruff format .
uv run ruff check . [--fix]
```

After dependency or lockfile changes, run `uv sync`.

## Dependencies

- Import only packages declared in `pyproject.toml` or added with approved `uv add` / `uv add --dev`.
- Runtime dependencies belong in `[project].dependencies`; dev tools belong in `[dependency-groups].dev`.
- Keep `[tool.uv] exclude-newer = "7 days"` so dependency resolution uses packages at least seven days old.
- Preferred-stack packages below are recommendations, not available code, until declared.

## Python Style

- **Types**: Use modern syntax: `list[str]`, `X | None`, `Self`; no `typing.List`.
- **Data**: Use `dataclasses` or `TypedDict`.
- **Paths**: Use `pathlib.Path`.
- **Errors**: Raise/catch specific exceptions with clear messages; no bare `except:`.
- **Formatting**: Use f-strings, including debug form `f"{var=}"` when useful.
- **Public/non-trivial APIs**: Add type hints.

## Configuration

- Put secrets in `.env`, load with `python-dotenv`, and never commit them.
- Avoid magic values: put user/operator/maintainer-tunable runtime settings in `config.yaml`, loaded with `pyyaml` when needed: model names, temperatures, token limits, timeouts, retry counts, endpoints, file paths, feature flags, thresholds. Keep internal constants/invariants in code when changing them requires code knowledge or should not be normal configuration.
- Keep package, lint, format, and test configuration in `pyproject.toml` or the tool's native config file, not `config.yaml`.

## Logging

Use `logging` with JSON output. Include at least level, message, logger/module, timestamp, and exception details when present.

## Architecture

Prefer high locality and deep modules: keep rules, invariants, formatting, errors, and domain knowledge close to owning code behind small stable interfaces. Avoid shallow pass-through layers, splitting one concept across many files, or hiding simple control flow behind unnecessary abstractions.

- **Explicit flow**: Favor direct readable control flow. No metaclasses, `exec`, dynamic attribute generation, or hidden registration unless already used by the project.
- **Deep modules**: Modules should own meaningful behavior, not just forward calls. Keep related validation, transformation, persistence, and error handling together when it improves locality/testability.
- **Stable boundaries**: Decouple at real boundaries: external services, storage, user interfaces, configuration, and independently testable domain behavior. Avoid generic layer splits.
- **Predictable configuration**: Use config for deployment flexibility, not for moving business logic into data files.
- **Operational quality**: Use descriptive names, deterministic tests, structured logs, and clear errors.

## Testing

- Put tests in `tests/`, mirroring source layout. Name files `test_<module>.py` and functions `test_<behavior>()`. Put shared fixtures in `conftest.py`.
- Use TDD where it makes sense: for new behavior, bug fixes, and refactors, add/update the narrowest useful failing test first, make the smallest passing change, then refactor while tests stay green. Skip only for documentation-only, infrastructure-only, or otherwise untestable work.
- Do not make live network, API, model-provider, or external-service calls in tests unless explicitly requested. Mock external systems and use small local fixtures.
- For data/ML tests, use deterministic seeds.
- Run with `uv run pytest -v` for verbose output or `uv run pytest -x` to stop on first failure.

## Code Review

- **Maintainability**: Flag unreachable code, unused imports/variables, misleading names, avoidable duplication, inconsistent style, and functions doing too much. When recommending a split, name the responsibility boundary.
- **Simplification**: Prefer standard library tools and existing helpers over hand-rolled logic. Use comprehensions, generators, early returns, and fewer intermediates only when clearer.
- **Performance**: Call out algorithmic issues, repeated loop work, unnecessary hot-path I/O, N+1 queries, excessive allocation/copying, blocking work inside async code, missing `await`, and inappropriate threading/multiprocessing. Explain expected impact; avoid speculative micro-optimizations.
- **Python fit**: Use idioms such as `enumerate`, `zip`, unpacking, f-strings, `with`, `pathlib`, and structured data types when they clarify behavior. Avoid mutable defaults and silent failures.

## Documentation

- Comments/docstrings explain why and follow PEP 257.
- README should be concise, with usage/examples and no fluff.
- Avoid unnecessary docs beyond README/AGENTS/NOTES/PLAN. Add dedicated architecture notes, API docs, deployment notes, data documentation, or model cards only when the project clearly needs them.

## Git

- Use conventional commits: `type(scope): message`; types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Example: `feat(auth): add OAuth2 login flow`.
- Branches: `feature/<name>`, `fix/<name>`, `refactor/<name>`.
- Keep commits small/logical and avoid WIP commits on `main`.
- After code changes, suggest a conventional commit message matching the actual scope.

## Quality Commands

```bash
uv run ruff format .
uv run ruff check . [--fix]
uv run pytest
uv run ruff format . && uv run ruff check . && uv run pytest
```

## Preferred Stack

Add missing packages with approved `uv add` before importing them. Ignore entries that do not apply.

- **Config**: `pyyaml` for YAML; `python-dotenv` for env vars.
- **CLI**: `typer` rather than `argparse`; use type hints, `typer.Argument()`, `typer.Option()`, and `Enum` for fixed choices.
- **HTTP**: `httpx`, especially for async clients.
- **Output**: `rich` (`Console`, `Table`) for terminal output.
- **FastAPI**: Pydantic validation, `app/routers/`, dependency injection, async I/O.
- **Streamlit**: `st.sidebar` controls, `st.session_state`, `@st.cache_data`.
- **LLM**: OpenRouter via OpenAI-compatible client. Load API keys from `.env`; configure model, temperature, token limits, endpoint, timeouts, and retries in `config.yaml`; use `ThreadPoolExecutor` for simple concurrent blocking calls.
- **Embeddings**: local `sentence-transformers`, e.g. `intfloat/multilingual-e5-small`.
- **Scraping**: Start with plain HTTP via `httpx` or `requests`. Use Playwright only when direct HTTP cannot handle client-side rendering, browser interaction, or anti-bot flows.
- **Data science**: Jupyter, vectorized pandas, pyarrow/parquet, scikit-learn, seaborn.
- **Document parsing**: Use `docling` by default for DOCX/PDF to Markdown (`export_to_markdown`). For fast parallel parsing, parse text/tables first, disable OCR/VLMs, skip image descriptions, and use an empty image placeholder. Use `pymupdf` when Markdown is unnecessary, or `pymupdf4llm` when Markdown is needed and a lighter tool is enough.

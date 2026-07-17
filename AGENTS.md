# AGENTS Guidelines (Python)

Defaults for agent-assisted Python projects managed with `uv`. Required rules apply throughout; Preferred Stack entries apply only when that capability is needed.

## Priority

When instructions conflict, follow:

1. Safety and security constraints
2. User request
3. This file
4. Existing repo patterns

Briefly flag contradictions to the user, naming the conflicting instructions, the priority applied, and any effect on the task.

## Required Process

- **Scope**: Work only inside this repo and change only task-relevant files. Do not alter unrelated code, comments, or logic; report unrelated issues separately.
- **Approvals**: Ask before adding dependencies, installing packages, fetching external resources, or calling external services. `uv sync` is pre-approved only for dependencies already declared here.
- **Assumptions**: Surface inconsistencies, ambiguity, and risky trade-offs; ask when clarification is necessary. Challenge unsafe or unsound requests with concrete alternatives.
- **Simplicity**: Prefer small, explicit, maintainable changes that satisfy the request without over-engineering.
- **Cleanup**: Remove dead code, temporary files, and development artifacts created by the work. Release resources with context managers or appropriate cleanup handlers.
- **Artifacts**: Keep large datasets, generated outputs, and caches out of git unless intentionally versioned.
- **Before finishing**: Confirm assumptions, simplicity, scope, validation, and any trade-offs worth reporting.
- **Durable memory**: Record non-obvious root causes, failed approaches, confirmed constraints, refactoring risks, and decisions in `NOTES.md`. Track open tasks, questions, deferred ideas, and follow-ups in `PLAN.md`. Update either file only when the information is durable and useful; avoid step logs.

## Security

- Treat security as a design constraint. Minimize data, network, permission, and dependency exposure.
- Never hardcode or commit secrets, tokens, credentials, private keys, personal data, or sensitive operational data. Store secrets in `.env`, load them with `python-dotenv`, and redact sensitive values from logs, errors, fixtures, documentation, and examples.
- Validate and constrain untrusted inputs at boundaries: CLI args, config files, uploaded files, HTTP responses, model outputs, scraped content, and user-provided paths.
- Do not use `eval`, `exec`, unsafe deserialization, unchecked downloads, or dynamic imports on untrusted input. Prevent shell injection and path traversal.
- Before adding dependencies or external services, consider supply-chain risk, maintenance status, license fit, and whether the standard library or an existing dependency is enough.
- If you find a security issue, stop broad changes, document the risk, and propose the smallest focused fix. Keep security changes separate from unrelated refactors.

## Python and Dependency Management

- Prefer Python 3.13 for new projects when dependencies permit. Preserve the supported range declared in `pyproject.toml` unless the task explicitly changes it.
- Use `uv` exclusively for Python environments, dependencies, and commands. Do not run `python`, `pip`, `pytest`, or `ruff` directly or create environments with other tools.
- Use `uv sync`, `uv add [--dev] <package>`, `uv sync --upgrade-package <package>`, and `uv run <command>`. Run `uv sync` after dependency or lockfile changes.
- Import only packages declared in `pyproject.toml`. Put runtime dependencies in
  `[project].dependencies` and development tools in `[dependency-groups].dev`.
- Keep `[tool.uv] exclude-newer = "7 days"` so dependency resolution uses packages at least seven days old.
- Preferred-stack packages below are recommendations, not available code, until declared.
- For new projects, prefer a `src/<project_name>/` layout with tests under `tests/`; preserve an established layout unless migration is in scope. Separate unit and integration tests where useful, and define operational scripts in `[project.scripts]`.
- Install repository pre-commit hooks with `uv run pre-commit install` before the first commit.

## Python Standards and Style

- **Types**: Use modern syntax: `list[str]`, `X | None`, `Self`; no `typing.List`.
- **Data**: Use `dataclasses` or `TypedDict`.
- **Paths**: Use `pathlib.Path`.
- **Errors**: Raise/catch specific exceptions with clear messages; no bare `except:`.
- **Formatting**: Use f-strings, including `f"{var=}"` when useful.
- **Public/non-trivial APIs**: Add type hints.

## Configuration

- Put operator-tunable runtime settings in `config.yaml`, loaded with `pyyaml` when needed: model names, temperatures, token limits, timeouts, retries, endpoints, paths, feature flags, and thresholds. Keep implementation constants and invariants in code.
- Keep package, lint, format, and test configuration in `pyproject.toml` or the tool's native config file, not `config.yaml`.

## Logging

Use `logging` with JSON output containing timestamp, level, message, logger/module, and exception details when present.

## Architecture

Prefer high locality and deep modules: keep related rules, invariants, formatting, errors, and domain knowledge behind small stable interfaces. Avoid pass-through layers, scattered concepts, and abstractions that hide simple control flow.

- **Explicit flow**: Favor direct readable control flow. No metaclasses, `exec`, dynamic attribute generation, or hidden registration unless already used by the project.
- **Deep modules**: Modules should own meaningful behavior, not just forward calls. Keep related validation, transformation, persistence, and error handling together when that improves locality or testability.
- **Stable boundaries**: Decouple at real boundaries: external services, storage, user interfaces, configuration, and independently testable domain behavior. Avoid generic layer splits.
- **Predictable configuration**: Use configuration for deployment flexibility, not to move business logic into data files.
- **Operational quality**: Use descriptive names, deterministic tests, structured logs, and clear errors.

## Containers and Operations

- Provide a Docker option when practical. Use multi-stage builds, small version-pinned base images, a `.dockerignore`, and reproducible dependency installs. Exclude secrets, credentials, caches, and development tools from runtime images.
- Run production containers as a dedicated non-root user with a read-only filesystem where practical. Drop unnecessary capabilities, avoid privileged mode, and set resource limits.
- Keep containers stateless and disposable. Persist data in named volumes or external services, write logs to stdout/stderr, handle termination signals, and use an explicit entrypoint or command.
- Add health checks that verify service behavior, not only process existence. Distinguish startup, readiness, and liveness when supported.
- Use Docker Compose for multi-container local or deployment stacks. Pin image versions, isolate services on the narrowest required networks, and use NVIDIA Container Toolkit only when GPU acceleration is required.
- Build and scan images in CI; fail on relevant high-severity vulnerabilities, generate provenance or an SBOM where supported, and rebuild regularly for security updates.

## Testing

- Mirror the source layout under `tests/`; name files `test_<module>.py` and tests descriptively as `test_<behavior>()`. Put shared fixtures in `conftest.py`.
- For new behavior, fixes, and refactors, add the narrowest useful failing test first, make the smallest passing change, then refactor while tests remain green. Skip only for documentation, infrastructure, or otherwise untestable work.
- Test observable behavior, edge cases, and public contracts rather than implementation details. Minimize mocking; isolate external HTTP, model, database, filesystem, and service boundaries only as needed for deterministic unit tests.
- Use parametrization for input matrices, fixture factories for meaningful variations, and deterministic seeds for data/ML tests.
- Keep slower integration tests distinguishable from unit tests. Run relevant unit tests in CI and integration tests in repository-defined pipelines.
- Before declaring completion, run the relevant test subset and, when practical, the full quality suite.

## Code Review

- **Correctness**: Prioritize behavioral regressions, edge cases, security, test quality, and production failure modes such as timeouts, retries, partial failures, recovery, and observability.
- **Maintainability**: Flag unreachable code, unused imports or variables, misleading names, avoidable duplication, inconsistent style, and functions with mixed responsibilities. Name the boundary when recommending a split.
- **Simplification**: Prefer standard library tools and existing helpers over hand-rolled logic. Use comprehensions, generators, early returns, and fewer intermediates only when clearer.
- **Performance**: Flag algorithmic issues, repeated loop work, hot-path I/O, N+1 queries, excessive allocation or copying, blocking async work, missing `await`, and inappropriate concurrency. Explain the expected impact; avoid speculative micro-optimizations.
- **Python fit**: Use idioms such as `enumerate`, `zip`, unpacking, f-strings, `with`, `pathlib`, and structured data types when they clarify behavior. Avoid mutable defaults and silent failures.

## Documentation

- Comments and docstrings explain why, not what; docstrings follow PEP 257.
- Keep README concise and example-driven.
- Add architecture, API, deployment, data, evaluation, or model documentation only when needed.

## Git

- Under GitHub flow, merge to `main` through reviewed pull requests with passing CI.
- For versioned releases, follow Semantic Versioning and repository automation; tag releases as `v<version>`.
- Use conventional commits: `type(scope): message`, with `feat`, `fix`, `docs`, `refactor`, `test`, or `chore`. Example: `feat(auth): add OAuth2 login flow`.
- Name branches `feature/<name>`, `fix/<name>`, or `refactor/<name>`.
- Keep commits small and focused; avoid WIP commits on `main`.
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
- **Data science**: Jupyter, vectorized pandas or polars, pyarrow/parquet, scikit-learn, seaborn.
- **Document parsing**: Use `docling` by default for DOCX/PDF to Markdown (`export_to_markdown`). For fast parallel parsing, parse text/tables first, disable OCR/VLMs, skip image descriptions, and use an empty image placeholder. Use `liteparse` as a lighter tool when only PDF conversion is needed.

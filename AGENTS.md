# AGENTS Guidelines (Python)

Instructions for AI agents working on Python projects managed with `uv`. Apply only sections relevant to the task; preserve established project choices unless a migration is requested.

## Priority

When instructions conflict, follow:

1. Safety and security constraints
2. User request
3. This file
4. Existing repository patterns

Briefly report any conflict, the rule applied, and its effect.

## Working Process

- **Scope:** Work only in this repository and change only task-relevant files. Preserve unrelated code and user changes; report unrelated issues separately.
- **Approval:** Ask before adding or installing dependencies, fetching external resources, or calling external services. `uv sync` is pre-approved only for already-declared dependencies.
- **Judgment:** Surface inconsistencies, ambiguity, and material risks. Ask only when a safe, reasonable assumption cannot resolve them; challenge unsafe requests with a concrete alternative.
- **Implementation:** Prefer the smallest explicit, maintainable solution. Avoid speculative features, shallow abstractions, and unrelated cleanup.
- **Cleanup:** Remove temporary files, caches, dead code, and development artifacts created by the task. Release resources with context managers or cleanup handlers. Keep large data and generated outputs out of Git unless intentionally versioned.
- **Memory:** Put durable findings (non-obvious root causes, failed approaches, confirmed constraints, refactoring risks, decisions) in `NOTES.md`; put open tasks, questions, and deferred work in `PLAN.md`. Do not write step logs or update either file without lasting value.
- **Completion:** Inspect the final diff, confirm scope and assumptions, run proportionate validation, and report results and trade-offs. Do not claim success without evidence.

## Security and Data Protection

- Treat security and data protection as design constraints. Minimize data, network, permission, and dependency access; default application privacy settings to the most restrictive option and require explicit opt-in for broader access.
- Never hardcode or commit secrets, tokens, credentials, private keys, personal data, or sensitive operational data. Put secrets in `.env`, load them with `python-dotenv`, keep `.env` ignored, and redact sensitive values from logs, errors, fixtures, examples, and documentation.
- Validate and constrain all untrusted inputs at boundaries, including CLI/config values, paths, uploads, HTTP responses, model output, and scraped content.
- Do not use `eval`, `exec`, unsafe deserialization, unchecked downloads, or dynamic imports on untrusted input. Prevent shell injection and path traversal.
- Before proposing a dependency or service, assess supply-chain risk, maintenance, license fit, and whether the standard library or an existing dependency suffices.
- Pin every GitHub Action `uses:` reference to a full commit SHA; a version comment may document the corresponding release.
- Keep automated dependency monitoring enabled for every project and container scanning enabled for containerized projects.
- If a security issue is found, stop broad work, document the risk, and propose the smallest focused fix. Keep security changes visible and separate from unrelated refactors.

## Python and Dependencies

- Target Python 3.13 for new projects when dependencies permit. Preserve the supported range in `pyproject.toml` unless the task changes it.
- Use `uv` exclusively for environments, dependencies, and Python commands. Use `uv sync`, `uv add [--dev] <package>`, `uv sync --upgrade-package <package>`, and `uv run <command>`; never run `python`, `pip`, `pytest`, or `ruff` directly. Run `uv sync` after dependency or lockfile changes.
- Import only declared packages. Put runtime dependencies in `[project].dependencies`, development tools in `[dependency-groups].dev`, and operational commands in `[project.scripts]`.
- Preserve `[tool.uv] exclude-newer = "7 days"` so newly published packages observe the supply-chain cooldown.
- For new projects, use `src/<project_name>/` with mirrored tests under `tests/`; preserve existing layouts unless migration is in scope. Separate unit and integration tests when useful.
- Preferred packages are not available until declared. Obtain approval before `uv add`.
- Install repository hooks with `uv run pre-commit install` before the first commit.

## Python Design and Style

- Follow PEP 8 and repository Ruff settings (default maximum line length: 100). Use four-space indentation and conventional `snake_case`, `PascalCase`, `UPPER_CASE`, and lowercase module names.
- Add type hints, including return types, to all new functions and methods. Use modern syntax (`list[str]`, `X | None`, `Self`), never legacy `typing.List` forms.
- Use Pydantic models for validated API/config/external data, dataclasses for internal data containers, and `TypedDict` for typed mappings that do not need runtime validation. Prefer `frozen=True` and `slots=True` for immutable dataclasses; use `kw_only=True` when many fields make positional construction unclear.
- Prefer functions for stateless behavior and classes for state or interfaces. Use `Protocol` for structural contracts and `ABC` only for shared implementation or enforced inheritance.
- Use receive-an-object/return-an-object when parameters or results are numerous, optional, evolving, or form a meaningful domain concept; do not add wrapper types to simple APIs.
- Keep functions focused and side effects explicit. Prefer `pathlib.Path`, f-strings, guard clauses, comprehensions for simple transformations, `enumerate`, `zip`, unpacking, and context managers when they improve clarity. Avoid wildcard imports and mutable defaults.
- Redesign interfaces to eliminate avoidable failure states. Otherwise raise/catch specific exceptions with clear messages, chain translated exceptions with `raise ... from error`, and never silently suppress errors or log an exception merely to re-raise it.
- Use async I/O when concurrency is beneficial; do not block inside `async def`. Keep CPU-bound work synchronous or move it to an appropriate executor. Run independent async operations concurrently rather than awaiting them serially.
- Use internal constants for invariants, `Enum`/`StrEnum` for related typed constants, and configuration for operator choices.

## Architecture and APIs

- Favor deep modules and high locality: keep related validation, transformation, persistence, errors, and domain rules behind small stable interfaces. Avoid pass-through layers, scattered concepts, metaclasses, dynamic attribute generation, and hidden registration.
- Decouple at real boundaries: external services, storage, UI, configuration, and independently testable domain behavior. Configuration controls deployment choices, not business logic.
- For platform applications, preserve the component boundary: model services (level 1) and shared processing (level 2) are called through orchestration workflows (level 3); application stacks (level 4) must not bypass orchestration to call lower levels directly.
- Separate frontend interaction from backend application logic. When an HTTP API is needed, prefer FastAPI; expose only interfaces appropriate to the use case (web, API, MCP, or CLI).
- In FastAPI, validate boundaries with Pydantic; keep request and response models distinct; group small domain routers; inject services/resources; use consistent error bodies and appropriate HTTP status codes.
- Applications that handle persistent data use a database/object store rather than ad hoc local-file persistence. Ingest files as controlled application-owned copies instead of reading live upstream files on every request.

## Configuration, Logging, and Operations

- Put operator-tunable runtime values in `config.yaml` (models, temperatures, token limits, timeouts, retries, endpoints, paths, flags, thresholds), loaded with `pyyaml` when needed. Keep implementation invariants in code and tool configuration in `pyproject.toml` or the tool's native file.
- Use `logging` with JSON output to stdout/stderr containing timestamp, level, message, logger/module, and exception details when present. Match log severity to impact and never emit sensitive values.
- Add observability proportionate to maturity: at minimum behavioral health checks and error logging; for pilots/production also cover relevant uptime, latency, error rate, resource use, usage, traces, and anomalies.
- Applications must be runnable in Docker. Use multi-stage builds, small version-pinned images, reproducible installs, and `.dockerignore`; exclude secrets, caches, data, and dev tools from runtime images.
- Run production Docker rootlessly and containers as dedicated non-root users. Prefer read-only filesystems, drop unnecessary capabilities, avoid privileged mode, constrain resources and networks, and use NVIDIA Container Toolkit only when GPU access is required.
- Keep containers stateless and disposable; persist state in managed volumes or services, handle termination signals, and define explicit commands. Add behavioral health checks and distinguish startup/readiness/liveness when supported.
- Use pinned images in Docker Compose for multi-container stacks. In CI, scan dependencies and containers and fail on relevant high-severity findings. Generate provenance and SBOMs for published artifacts where supported.

## Testing and Validation

- For behavior changes, fixes, and refactors, first add or update the narrowest useful failing test, then implement the smallest passing change and refactor while green. Skip only for documentation, infrastructure, or genuinely untestable work.
- Test observable behavior, public contracts, failure modes, and edge cases rather than implementation structure. Use native assertions, `pytest.raises`, parametrization for input matrices, factory fixtures for meaningful variants, and deterministic seeds for data/ML tests.
- Minimize mocking. Isolate HTTP, model, database, filesystem, and other external boundaries only as needed for fast deterministic unit tests.
- Mirror source layout under `tests/`; use `test_<module>.py`, descriptive `test_<behavior>()` names, and shared fixtures in `conftest.py`. Keep slower integration tests distinguishable and follow repository CI conventions.
- Run the relevant test subset before completion and, when practical, the full quality suite:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

## Review Guidance

When asked to review, prioritize findings over summaries and cite concrete locations.

- **Correctness/security:** Regressions, edge cases, unsafe input/data handling, tests, and production failures such as timeouts, retries, partial failure, recovery, and missing observability.
- **Maintainability:** Unreachable code, unused symbols, misleading names, duplication, inconsistent style, and mixed responsibilities. Name the boundary when recommending a split.
- **Performance:** Algorithmic issues, repeated loop work, hot-path I/O, N+1 queries, excessive allocation, blocking async work, missing `await`, and inappropriate concurrency. Explain likely impact; avoid speculative micro-optimization.
- **Simplicity/Python fit:** Prefer standard-library or existing helpers and clear idioms over custom machinery.

## Documentation and Git

- Use Google-style docstrings. Give modules, classes, and functions a concise summary; document arguments, returns, and raised exceptions for non-trivial APIs without repeating signature types. Comments explain why, not what.
- Keep README content concise and example-driven. Add architecture, API, deployment, data, evaluation, or model documentation only when the project needs it.
- Under GitHub flow, work on short-lived `feat/<name>`, `fix/<name>`, or `refactor/<name>` branches and merge to `main` only through a focused, reviewed PR with passing CI. Do not commit directly to `main`.
- Use conventional commits: `feat`, `fix`, `docs`, `refactor`, `test`, or `chore`, optionally scoped; for example, `feat(auth): add OAuth2 login`.
- Follow Semantic Versioning for releases and repository automation; tag releases `v<version>`. After code changes, suggest a conventional commit message matching the actual scope.

## Preferred Stack

Use only when the capability is needed and the package is declared or its addition approved:

- Config: `pyyaml`, `python-dotenv`
- CLI/output: `typer`, `rich`
- HTTP/API: `httpx`; FastAPI with Pydantic and async I/O
- Simple UI: Streamlit; use a dedicated frontend for complex, long-lived, asynchronous, or richer UX
- Embeddings: local `sentence-transformers` (for example, `intfloat/multilingual-e5-small`)
- Scraping: plain HTTP first; Playwright only when client rendering or browser interaction requires it
- Data science: Jupyter, vectorized pandas or polars, Parquet, scikit-learn, seaborn
- Document parsing: `docling` by default; `pymupdf` or `liteparse` for lighter needs

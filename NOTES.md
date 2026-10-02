# Engineering Notes

## CI compatibility and security scanning

- CI tests Python 3.12 and 3.13; Docker uses Python 3.12. The declared range
  is `>=3.12`, but CI does not establish support for later versions. The lockfile
  currently records spaCy 3.8.16.
- GitPython is exempt from the global seven-day `uv` release window so actionable
  security fixes are not delayed when the container vulnerability scan blocks CI.
- The container scan ignores vulnerabilities without an available fix, but continues
  to fail for fixable HIGH and CRITICAL findings.
- The `python:3.12-slim` base image may lag Debian 13 security updates. Upgrade the
  affected packages in the runtime stage when a fixable OS vulnerability blocks the
  container scan.
- The pre-commit CI job must install Python 3.13 to match the hook interpreter in
  `.pre-commit-config.yaml`; installing only 3.12 fails during hook setup.
- The runtime upgrade list includes `libpcre2-8-0` for CVE-2026-103111; the failing
  scan reported `10.46-1~deb13u2`, with the fix available in `10.46-1~deb13u3`.

## Scoring dependency and documentation limits

- The app imports scoring functions from installed `zix`, not the duplicated
  `_streamlit_app/data/` files. Keep scoring changes in the dependency boundary.
- The installed ZIX source contains a fallback that invokes `pip` to download the
  spaCy model if it is missing. The project declares that model explicitly; use
  locked dependency installation rather than relying on this fallback. A focused
  upstream fix should replace the fallback with an actionable missing-model error.
- Live model/provider availability, price estimates, ZIX calibration, and current
  contributor affiliations cannot be established from this repository. README
  model examples reflect configuration, not a verified external model catalogue.
- `publiccode.yml` describes a prototype to match the UI warning. Its former release
  date had no matching release evidence in the reviewed files and was removed.
- The Leichte Sprache condensation option selects a condensed user instruction,
  but the system message and template still request completeness. This conflicting
  guidance limits what documentation can promise about condensation behavior.

## Offline test boundaries

- Mutmut needs explicit `source_paths` for the `_streamlit_app/` layout and
  `also_copy = ["config.yaml"]`: its tests run against a copied tree in `mutants/`,
  where the app still resolves configuration relative to the source directory.
  Do not copy `.env` or developer credentials into that workspace.

- Streamlit AppTest exercises UI requests and reruns with only the OpenAI client
  and ZIX scoring boundary replaced. Disable dotenv loading in these tests so
  developer credentials cannot affect results; clear resource caches and restore
  the event logger between tests. No provider calls or model downloads are needed.
- Prompt tests protect language, output tags, source preservation, and mode-specific
  instructions rather than reconstructing strings with production templates.
  They verify instruction selection, not whether an LLM follows those instructions.

## Mutation testing contracts and limitations

- AppTest executes the script as `__main__` on a Streamlit script thread. Mutmut
  identifies app mutations as `_streamlit_app.sprache-vereinfachen`, so AppTest
  alone does not select or activate these app-function mutants. Direct tests
  import the trusted script under that module name with an inactive Streamlit UI;
  OpenAI and ZIX remain mocked at their boundaries. Keep AppTest for real UI flows.
- A no-argument `mutmut run` can retain cached results after test changes. Use
  explicit function globs (or `'*'` for all functions) to rerun affected mutants.
- The loader shutdown test forwards actual mutant IDs into a child interpreter.
  It removes only the `stats` sentinel because standalone interpreters do not
  initialize mutmut's pytest statistics plugin. A parent loader call records test
  selection. Nested `uv run --active --offline --no-sync` uses the existing
  environment even from mutmut's copied workspace; without `--active`, nested uv
  selected an environment without mutmut and failed statistics collection.
- Shutdown and parallel fan-out tests synchronize with events, not sleeps. Their
  bounded waits fail deterministically and release/reap resources. Non-daemon
  loader mutants fail the subprocess timeout assertion, rather than being counted
  as mutation-runner timeouts.

### Mutation audit, 2026-10-02

The original report contained 90 survivors and 278 mutants marked “no tests.”
After the full explicit rerun and a final affected-function rerun: **651/684
killed, 33 survived, 0 no tests, 0 timeouts, 0 suspicious results**. Of the original
report entries, 63 survivors and 272 “no tests” mutants are now killed. Production
code and dependencies were not changed. The added tests cover reasoning options,
provider slug shapes, multiline tags, configuration failures, logging schemas,
loader shutdown, model failures, parallel requests, Word bytes and formatting,
and all result-rendering modes.

IDs below are the suffixes in `x_<function>__mutmut_<ID>` (formatter IDs use
`xǁJSONFormatterǁformat`). These are newly killed entries from the original report:

| Module/function | Newly killed IDs |
| --- | --- |
| core/start_understandability_loading | 6, 10, 13 |
| core/model_request_parameters | 15–22, 25–28, 102–105 |
| core/extract_tagged_response | 7 |
| core/format_one_click_results | 17–19, 32 |
| core/build_log_payload | 1–2, 8–19, 21–26 |
| core/JSONFormatter.format | 8–11, 13, 15, 32–33 |
| core/configure_event_logger | 2–4, 13, 19, 23–24, 28, 32, 34, 37 |
| app/create_project_info | 1–30 (all) |
| app/get_result_from_response | 1–11 (all) |
| app/invoke_model | 1–36, 41–50, 53–57 |
| app/enter_sample_text | 1 (all) |
| app/get_one_click_results | 1–15 (all) |
| app/create_download_link | 1–71 (all) |
| app/log_event | 1–25 (all) |
| app/render_download_and_caption | 1–2 (all) |
| app/render_result | 1–66 (all) |

Remaining mutations are deliberately distinguished from test gaps:

| Module/function and surviving IDs | Assessment |
| --- | --- |
| core/start_understandability_loading: 5, 9, 11, 12 | Only changes the private worker's diagnostic name. Loading, sharing, exception propagation and process exit are covered; exact thread names are not a public contract. |
| core/load_yaml_config: 3 | Equivalent: `Path.open` defaults to read mode. |
| core/load_yaml_config: 2, 4; core/load_project_info: 6, 8; core/configure_event_logger: 44, 46 | Locale-dependent encoding gap: removing explicit UTF-8 is indistinguishable on this UTF-8 host. Unicode content is tested; tests do not assert internal codec arguments merely to kill mutants. |
| core/load_yaml_config: 8; core/configure_event_logger: 48 | Equivalent UTF-8 codec aliases (case-insensitive). |
| core/temperature_request_parameters: 7; core/model_request_parameters: 30, 57, 73; core/classify_understandability: 3 | Adds `XX` around diagnostic messages. Exception types and useful field/error descriptions are checked; exact decoration is not contractual. |
| core/rounded_score: 2, 4, 6 | Equivalent for supported finite scores: adding/subtracting zero or rounding without explicit zero precision gives the same final integer. |
| core/format_one_click_results: 26 | Unobservable separator: the all-failure branch can contain at most one combined failure section, so joining never uses its separator. |
| core/JSONFormatter.format: 30 | Equivalent: `ensure_ascii=None` is false, like `False`. |
| core/configure_event_logger: 8, 10, 27 | Equivalent truthiness: absent enabled defaults to false/None; propagation false/None both stop propagation. |
| core/configure_event_logger: 38 | Changes default filename to `APP.LOG`; the case-insensitive local filesystem accepts the same lookup. Platform limitation, not globally equivalent. |
| app/invoke_model: 37–40 | Changes an internal missing-content exception message that is caught and translated to the same generic failure. Missing content and exception logging are covered. |
| app/invoke_model: 51–52 | Decorates/cases diagnostic log wording. Error severity, model identity, exception information and returned failure are covered. |

No production changes were made to force mutation kills, and no assertions were
weakened. Final validation: 119 tests pass; repository Ruff lint and formatting
checks pass. Validation used the existing local Python 3.14 environment; the CI
Python 3.12/3.13 matrix was not run locally.

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

- Streamlit AppTest exercises UI requests and reruns with only the OpenAI client
  and ZIX scoring boundary replaced. Disable dotenv loading in these tests so
  developer credentials cannot affect results; clear resource caches and restore
  the event logger between tests. No provider calls or model downloads are needed.
- Prompt tests protect language, output tags, source preservation, and mode-specific
  instructions rather than reconstructing strings with production templates.
  They verify instruction selection, not whether an LLM follows those instructions.

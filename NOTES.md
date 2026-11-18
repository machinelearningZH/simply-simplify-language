# Engineering notes

## CI and packaging

- Match the pre-commit interpreter `python3.13` in CI. The application matrix
  tests 3.12 and 3.13, and Docker uses 3.12.
- The scanner fails on fixable HIGH and CRITICAL vulnerabilities. When the slim
  base image lags Debian security updates, upgrade the affected packages in the
  runtime stage and validate the rebuilt image.
- Keep the locked spaCy model in the runtime environment. With the model absent,
  the pinned ZIX release tries to install it using pip, which the image removes.
  An upstream fix should replace the fallback with an actionable missing-model
  error. The app loads its scoring assets through `zix`.

## Prompt and output handling

- Keep completeness instructions specific to the mode. Condensed Leichte Sprache
  rewrites may omit nonessential information. Complete rewrites and analysis must
  cover the whole source. Avoid shared instructions that contradict the choice.
- `strip_markdown` removes headings and emphasis from model replies. Preserve
  literal markers in content such as `Bürger*innen`, URLs and email addresses.
  Some escaped markers, paired double underscores and indented code headings
  can still be stripped. Long runs of unmatched emphasis markers can take
  quadratic time. Check both content preservation and runtime when editing the
  patterns.

## Offline and mutation tests

- Mutmut copies the source into `mutants/`. Keep `source_paths` set to
  `_streamlit_app/` and copy `config.yaml`, which the app resolves relative to
  its source tree. Keep credentials out of the copy.
- AppTest runs the Streamlit script as `__main__`. Mutmut tracks
  `_streamlit_app.sprache-vereinfachen`, so direct tests import that module to
  exercise function mutants. Keep AppTest for UI flows and mock OpenAI and ZIX at
  their boundaries. Disable dotenv loading, clear resource caches and restore
  event logging in test fixtures.
- After changing tests, use explicit function globs with `uv run mutmut run`
  (or quote `'*'` for all functions) to avoid reusing cached mutation results.
- The loader shutdown test uses `uv run --active --offline --no-sync` so the
  child inherits the test environment in the copied workspace. Pass actual
  mutant IDs to the child and clear the `stats` sentinel, which requires
  mutmut's pytest plugin. Use events and bounded waits to test shutdown and
  parallel requests.

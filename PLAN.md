# Plan

- [ ] **F001 — Sanitize provider error logs (medium).** Replace raw provider
  exception traces in `_streamlit_app/sprache-vereinfachen.py` with safe
  diagnostics, such as error category, model ID, and HTTP status. Provider errors
  can expose submitted or generated text even when event logging is disabled.
  Preserve the generic UI error. Verify with
  `tests/test_app_functions.py::test_provider_error_logs_omit_sensitive_response_details`,
  currently the sole failing regression (168 passed, 1 failed).

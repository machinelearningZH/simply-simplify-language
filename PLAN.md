# Plan

- [ ] **F001 — Sanitize provider error logs (medium).** Replace raw provider
  exception traces in `_streamlit_app/sprache-vereinfachen.py` with safe
  diagnostics, such as error category, model ID, and HTTP status. Provider errors
  can expose submitted or generated text even when event logging is disabled.
  Preserve the generic UI error. Add a regression test proving provider error
  details are excluded from logs when implementing this fix.

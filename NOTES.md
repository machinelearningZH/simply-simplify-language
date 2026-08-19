# Engineering Notes

## CI compatibility and security scanning

- Test Python 3.12 and 3.13 in CI. The runtime dependency spaCy 3.8.14 does not
  publish CPython 3.14 distributions.
- GitPython is exempt from the global seven-day `uv` release window so actionable
  security fixes are not delayed when the container vulnerability scan blocks CI.
- The container scan ignores vulnerabilities without an available fix, but continues
  to fail for fixable HIGH and CRITICAL findings.
- The `python:3.12-slim` base image may lag Debian 13 security updates. Upgrade the
  affected packages in the runtime stage when a fixable OS vulnerability blocks the
  container scan.

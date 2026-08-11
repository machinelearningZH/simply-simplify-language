# Engineering Notes

## CI compatibility and security scanning

- Test Python 3.12 and 3.13 in CI. The runtime dependency spaCy 3.8.14 does not
  publish CPython 3.14 distributions.
- GitPython is exempt from the global seven-day `uv` release window so actionable
  security fixes are not delayed when the container vulnerability scan blocks CI.
- The container scan ignores vulnerabilities without an available fix, but continues
  to fail for fixable HIGH and CRITICAL findings.

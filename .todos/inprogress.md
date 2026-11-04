# 🚧 IN PROGRESS

- [ ] 🟠 🔍 In Review: Update dependencies and improve README — uv-only dependency workflow <!-- asana:1218103840404547 -->
  - Dependency constraints preserved; `pyproject.toml`, `uv.lock`, `.python-version`, Docker, local launcher, README and CI use uv.
  - Verified: locked sync + stale-lock rejection, 3 launcher regression tests, Ruff, Django check, Docker build and offline production dependency checks; macOS and Linux checks passed.
  - No live database migrations/full Compose integration or hosted CI run; changes are local, uncommitted.


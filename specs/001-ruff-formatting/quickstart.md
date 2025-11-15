# Quickstart: Adopt Ruff Formatting Hooks

## Goal
Ensure every contributor and CI job runs Ruff for formatting/import organization through the
existing pre-commit workflow with minimal manual configuration.

## Prerequisites
- Python 3.8+ available for tooling (Flowpipe runtime still supports 3.7+).
- `pip install pre-commit` once per workstation.
- Existing Flowpipe repository clone with `pre-commit` hooks installed.

## Steps
1. **Update dependencies**
   ```bash
   pip install -U pre-commit ruff
   ```
2. **Install/refresh hooks**
   ```bash
   pre-commit install
   pre-commit autoupdate
   ```
3. **Run Ruff locally**
   ```bash
   pre-commit run --all-files
   ```
   - Hook output should show only `ruff` and `ruff-format`.
   - Auto-fixes apply in place; review git diff before committing.
4. **Address failures**
   - For lint errors that cannot auto-fix, follow Ruff’s diagnostic message.
   - Re-run the same command until it exits with code `0`.
5. **CI verification**
   - Push the branch; GitHub Actions will execute the same `pre-commit` hooks.
   - Pipelines fail if Ruff reports issues, matching local behavior.

## Rollout Notes
- Document changes in `contributing.md` and release notes.
- Delete stale Black/isort references in scripts, docs, or PR templates.
- Encourage contributors to enable Ruff extensions in their IDEs for real-time feedback.

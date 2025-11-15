# Flowpipe Release Notes

## Upcoming Changes

- **Ruff-only formatting**: Flowpipe now relies on [Ruff](https://github.com/astral-sh/ruff) for formatting, linting, and import ordering. Black and isort dependencies/hook references were removed from `pyproject.toml`, `poetry.lock`, and `.pre-commit-config.yaml`.
- **Unified tooling workflow**: Pre-commit hooks, CI jobs, and the local `pre-commit run --all-files` command all execute Ruff (`ruff` + `ruff-format`) to keep contributors and automation aligned.
- **Documentation updates**: Contributor docs explain how to install/run Ruff hooks, and README highlights the new formatting workflow.
- **CI enforcement**: GitHub Actions now includes a dedicated pre-commit workflow plus a Ruff step inside the pytest workflow to guarantee style validation before tests run.

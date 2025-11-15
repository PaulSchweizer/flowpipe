# Ruff formatting workflow

Flowpipe relies on [Ruff](https://github.com/astral-sh/ruff) for formatting, linting, and import organization. The same hooks run locally and in CI, so following this guide guarantees consistent style.

## Installation

```bash
pip install -U pre-commit ruff
pre-commit install
pre-commit autoupdate
```

## Running the hooks

To check every tracked file (the same command CI runs):

```bash
pre-commit run --all-files
```

Ruff auto-fixes most issues. Re-run the command until it exits successfully. The output should only list the `ruff` and `ruff-format` hooks.

## Troubleshooting

- **Stale hooks**: Run `pre-commit autoupdate` after pulling branches that update the hook configuration.
- **New environments**: Delete `.venv` or `.cache/pre-commit` if hooks reference old versions, then rerun the installation commands.
- **Unsupported Python**: Ruff requires Python 3.9+ for tooling. If you work on Flowpipe using an older interpreter, create a dedicated virtualenv for tooling commands.

## Editor integration

If you use VS Code, you can set the formatter to the `charliermarsh.ruff` extension like so:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

If you use another editor, point it at the `ruff` binary for format-on-save and lint diagnostics to keep results aligned with the hooks.

# Research: Adopt Ruff Formatting Hooks

## Task 1: Best practices for Ruff in pre-commit
- **Decision**: Use the official `astral-sh/ruff-pre-commit` hooks (`ruff` and `ruff-format`) with
  default arguments, enabling `--fix` on the lint hook so imports get reordered automatically.
- **Rationale**: This mirrors Ruff’s documented setup, minimizes custom scripting, and allows
  contributors to reuse existing `pre-commit` workflows without new commands.
- **Alternatives considered**:
  - *Custom local hook commands*: rejected because they add maintenance overhead and do not
    benefit from upstream hook updates.
  - *Keeping Black for formatting*: rejected because the requirement explicitly migrates to Ruff and
    Black would duplicate functionality.

## Task 2: Configuration alignment with prior style
- **Decision**: Keep Ruff’s defaults (line length 88, quote rules, import sorting) except where an
  existing Flowpipe rule conflicts; only set fields in `pyproject.toml` when parity requires it.
- **Rationale**: Flowpipe already followed Black/isort defaults, which align with Ruff’s defaults,
  so keeping configuration minimal avoids churn and honors the “write as little custom code as
  possible” directive.
- **Alternatives considered**:
  - *Comprehensive custom config*: rejected for adding noise and diverging from standard Ruff
    guidance.
  - *Relying entirely on implicit defaults with no config file*: rejected because Flowpipe already
    tracks tool metadata in `pyproject.toml`, and documenting the hook location helps future
    contributors.

## Task 3: CI and contributor workflow continuity
- **Decision**: Reuse all existing automation (pre-commit hooks, developer setup steps, CI jobs)
  by swapping the referenced hooks to Ruff; no new scripts or workflows will be introduced.
- **Rationale**: Minimal change surface satisfies “re-use as many existing tools and integrations as
  possible” and ensures compatibility with historical contributor instructions.
- **Alternatives considered**:
  - *Adding separate Ruff-only CI jobs*: rejected as redundant with the current pre-commit driven
    formatting checks.
  - *Running Ruff via make/Invoke tasks*: rejected because it introduces custom tooling and drifts
    from standard practice.

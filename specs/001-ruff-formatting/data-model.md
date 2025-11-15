# Data Model: Adopt Ruff Formatting Hooks

## Entity: PreCommitHook
- **Purpose**: Represents each hook entry managed by `.pre-commit-config.yaml`.
- **Fields**:
  - `id` (string): Unique hook identifier provided by Ruff (`ruff`, `ruff-format`).
  - `repo` (string): Source repository (`https://github.com/astral-sh/ruff-pre-commit`).
  - `rev` (string): Tagged release of Ruff hooks (kept in sync with PyPI releases).
  - `args` (list[string]): Optional CLI flags (e.g., `--fix`).
  - `stages` (list[string]): Git stages where the hook runs (default `pre-commit`).
- **Relationships**: Depends on `RuffConfig` to know which style settings to enforce.
- **Validation rules**: `id` must match available hook names; `rev` must be a valid tag; args may only
  include supported Ruff flags to avoid custom scripting.

## Entity: RuffConfig
- **Purpose**: Captures formatting and lint preferences stored in `pyproject.toml` (or `ruff.toml`).
- **Fields**:
  - `line_length` (int, default 88): Aligns with historical Black default.
  - `target_version` (enum, default `py37`): Ensures Ruff understands Flowpipe’s runtime floor.
  - `select`/`ignore` (list[string]): Additional rule toggles; minimal values expected.
  - `format` (object): Optional formatting toggles if defaults ever diverge.
- **Relationships**: Referenced by `PreCommitHook` entries and dev documentation; ensures CI and
  contributors share the same style.
- **Validation rules**: Only declare fields when diverging from Ruff defaults; unknown fields fail CI.

## Entity: DocumentationAsset
- **Purpose**: Contributor-facing instructions (README, `contributing.md`, script comments) that
  describe how to run hooks and resolve failures.
- **Fields**:
  - `path` (string): Location of the file.
  - `audience` (enum): Maintainer, contributor, CI.
  - `content_summary` (string): Brief explanation of what the doc teaches (install Ruff, run hooks).
- **Relationships**: Links to `PreCommitHook` for step-by-step instructions and to `RuffConfig` for
  describing rule sources.
- **Validation rules**: Must reference Ruff as the single formatter/import tool and avoid outdated
  references to Black or isort.

## Entity: CIJobReference
- **Purpose**: Any automated workflow (e.g., GitHub Actions, scripts) that triggers formatting checks.
- **Fields**:
  - `job_id` (string): Workflow or script identifier.
  - `trigger` (string): Event (push, PR, manual) or command (pre-commit, tox).
  - `commands` (list[string]): Steps run within the job, which must now point at Ruff.
- **Relationships**: Consumes `PreCommitHook` definitions to remain aligned with local checks.
- **Validation rules**: Commands cannot reference Black/isort; jobs must fail if Ruff reports issues.

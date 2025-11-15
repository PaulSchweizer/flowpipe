# Feature Specification: Adopt Ruff Formatting Hooks

**Feature Branch**: `001-ruff-formatting`  
**Created**: 2025-11-14  
**Status**: Draft  
**Input**: User description: "Right now we are using black and isort for formatting in the pre-commit hooks. This has to be changed to ruff"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain formatting via Ruff (Priority: P1)

As a Flowpipe maintainer, I need the pre-commit workflow to run Ruff so contributors
automatically apply the same formatting and import rules before opening pull requests.

**Why this priority**: Consistent formatting prevents noisy diffs and ensures reviewers focus on
behavior rather than style regressions.

**Independent Test**: Run `pre-commit run --all-files`; verify only Ruff executes formatting and lint
checks, and that it exits cleanly after enforcing the configured style.

**Acceptance Scenarios**:

1. **Given** a clean clone with pre-commit installed, **When** a developer commits Python changes,
   **Then** Ruff reformats files and import ordering without invoking Black or isort.
2. **Given** a file that violates the Ruff rules, **When** `pre-commit run --all-files` executes,
   **Then** the hook reports the exact issues and offers autofix instructions (or applies fixes when
   configured).

---

### User Story 2 - Document new workflow (Priority: P2)

As a contributor, I need documentation that explains which formatter runs in hooks and how to
configure my environment so I can fix formatting without guessing tools.

**Why this priority**: Clear docs reduce onboarding friction and avoid contributors running the old
Black/isort commands.

**Independent Test**: Visit the contributing guide; confirm it references Ruff, links to installation
instructions, and explains how to run the hooks locally.

**Acceptance Scenarios**:

1. **Given** a new contributor reading `contributing.md`, **When** they follow the formatting
   instructions, **Then** they install Ruff (directly or via pre-commit) and can reproduce the same
   formatting locally as CI.

---

### User Story 3 - Keep CI & historical compatibility (Priority: P3)

As a maintainer, I need CI and the supported Python 3.7+ runtime to continue working with the
new tooling so we do not break existing pipelines.

**Why this priority**: Tooling updates cannot disrupt release automation or introduce unsupported
dependencies that block older Python runtimes.

**Independent Test**: Run the existing CI formatting/lint job (or equivalent local script) and confirm
it references Ruff hooks/configs while maintaining the documented Python support matrix.

**Acceptance Scenarios**:

1. **Given** the CI pipeline or local `pre-commit run --all-files`, **When** it executes on Python 3.8+,
   **Then** only Ruff provides lint/format checks and the job passes with the same success/failure
   criteria as before.

---

### Edge Cases

- Developers with stale `.pre-commit` environments must receive clear upgrade instructions when
  Ruff replaces prior hooks.
- Contributors editing code via automated tools (e.g., IDEs) still need guidance on invoking Ruff to
  avoid style drift.
- Projects pinned to the minimum supported runtime (Python 3.7) must not be forced to install
  unsupported Ruff versions; document required interpreter versions clearly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Replace Black and isort hooks in `.pre-commit-config.yaml` with Ruff so formatting,
  linting, and import ordering run through a single tool.
- **FR-002**: Configure Ruff (e.g., `pyproject.toml`) to match the currently enforced style (line
  length, quote preference, import sections) to avoid mass churn.
- **FR-003**: Update developer documentation (`README.md`, `contributing.md`, and any script
  comments) to reference Ruff commands instead of Black/isort.
- **FR-004**: Ensure CI or local validation scripts that previously invoked Black/isort now call Ruff
  to keep automated enforcement aligned.
- **FR-005**: Provide migration notes in release documentation describing the switch so downstream
  users know which formatter to run when contributing patches.

### Key Entities *(include if feature involves data)*

- **Pre-commit Hook Definition**: Entries in `.pre-commit-config.yaml` that specify which tooling runs
  before commits; must reference Ruff repos and hook IDs.
- **Ruff Configuration**: Settings stored in `pyproject.toml` (or `ruff.toml`) defining formatting,
  linting, and import ordering standards enforced across Flowpipe.

## Assumptions

- Ruff will serve as both formatter and import organizer, eliminating the need for separate Black or
  isort hooks.
- Contributors use Python 3.8+ (or compatible) to install Ruff while Flowpipe’s runtime support for
  Python 3.7+ remains unchanged.
- No additional style rules are introduced beyond those already enforced by Black/isort unless
  explicitly documented.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The documented formatting workflow completes in under 60 seconds using a single
  formatter/import tool, with no additional manual steps required from contributors.
- **SC-002**: 100% of newly merged pull requests show zero Black or isort-related diffs because only
  Ruff formatting changes appear in commits.
- **SC-003**: Contributor documentation references Ruff exclusively, and at least 90% of new
  contributors (measured via PR checklist or templates) confirm they followed the updated steps.
- **SC-004**: CI jobs enforcing formatting succeed on the first attempt in ≥95% of runs after the switch,
  demonstrating the configuration is stable.

## Constitution Alignment Checklist *(must be explicit)*

- **Framework-Only Scope**: The change only touches tooling configuration and documentation; the
  Flowpipe runtime remains a pure framework with no bundled nodes.
- **Plain Python Simplicity**: Ruff (pure-Python) replaces two separate tools, reducing dependency
  overhead. Support for the Python 3.7+ runtime remains unchanged, while contributors install
  compatible Ruff versions on modern interpreters.
- **Portable Graph Serialization**: Formatting changes do not alter graph/node serialization; ensure
  docs mention that serialization logic stays unaffected.
- **Test-Driven Total Coverage**: Pre-commit hooks supplement, not replace, pytest coverage; any new
  hook definitions must still allow tests to run and maintain 100% coverage expectations.
- **Stable APIs & Dual-Python Support**: No public API surface changes; release notes highlight the
  tooling update so downstream packagers know about the new contribution workflow.
- **Engineering Constraints**: Update `.pre-commit-config.yaml`, `pyproject.toml`, and contributor
  docs so formatting guidance, hooks, and release steps remain synchronized.

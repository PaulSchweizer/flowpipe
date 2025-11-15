# Implementation Plan: Adopt Ruff Formatting Hooks

**Branch**: `001-ruff-formatting` | **Date**: 2025-11-14 | **Spec**: [specs/001-ruff-formatting/spec.md](specs/001-ruff-formatting/spec.md)
**Input**: Feature specification from `/specs/001-ruff-formatting/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Flowpipe must replace the current Black + isort pre-commit hooks with Ruff while keeping the
workflow lightweight and familiar. We will rely on Ruff’s formatter/import defaults wherever
possible, reuse the existing pre-commit integration, and limit changes to configuration files and
docs. CI/dev tooling must only reference Ruff once the migration lands.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python runtime support 3.7+ (library); contributors use Python 3.8+ to run Ruff  
**Primary Dependencies**: pre-commit, Ruff (formatter/linter), pytest  
**Storage**: N/A (tooling configuration only)  
**Testing**: pytest suite + `pre-commit run --all-files` verification  
**Target Platform**: Cross-platform developer environments + CI runners  
**Project Type**: Single Python library (Flowpipe core + tests/docs)  
**Performance Goals**: Formatting/lint phase completes <60s locally and in CI  
**Constraints**: Use Ruff defaults where viable, reuse existing tooling, minimal custom scripts,
documented support for existing Python runtime versions, keep framework-only scope  
**Scale/Scope**: Repository-wide formatting hooks, docs, and CI references

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Framework-Only Scope**: Work limited to `.pre-commit-config.yaml`, `pyproject.toml`, and
  docs; no runtime node code is touched.
- **Plain Python Simplicity**: Ruff replaces two tools, reducing dependencies. It is pure-Python
  and runs wherever contributors already run pre-commit; no extra services required.
- **Portable Graph Serialization**: Formatting tooling does not change how graphs/nodes are
  serialized; we will state that serialization remains unaffected.
- **Test-Driven Total Coverage**: No runtime code updates expected. If tooling scripts are touched,
  we will add/adjust pytest coverage accordingly and ensure pre-commit hook tests remain.
- **Stable APIs & Dual-Python Support**: API surface untouched. Release notes and docs will note
  the contributor workflow change; no SemVer bump required because runtime behavior stays
  identical.
- **Engineering Constraints**: Update contributor docs, README badges/instructions, CI configs,
  and release instructions to reflect Ruff usage. Use Ruff defaults wherever feasible and keep
  automation inside existing tooling (pre-commit, tox, CI).

**Status**: PASS (pre- and post-design). No violations identified; complexity tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
flowpipe/
tests/
docs/
examples/
.pre-commit-config.yaml
pyproject.toml
specs/001-ruff-formatting/
├── spec.md
├── plan.md
├── research.md        # (to be created)
├── data-model.md      # (to be created)
├── quickstart.md      # (to be created)
└── contracts/         # (to be created)
```

**Structure Decision**: Single Python library repo; updates focus on root-level tooling files plus
supporting docs/tests already present in Flowpipe.

## Complexity Tracking

No constitutional violations identified; tracking table not required for this feature.

## Phase 0 – Research Plan

1. Catalog existing Black/isort hook behavior to ensure Ruff parity (line length, import sections).
2. Evaluate official Ruff pre-commit hooks for formatter + lint support and confirm arguments
   needed for auto-fix/import ordering.
3. Validate contributors’ tooling expectations (Python version, install steps) and document any
   delta in `research.md`.

*Deliverable*: `specs/001-ruff-formatting/research.md` summarizing decisions, rationales, and
rejected alternatives (completed).

## Phase 1 – Design & Contracts Plan

1. Model affected configuration/doc entities in `data-model.md`.
2. Describe contributor/CI interactions in `contracts/tooling.yaml` using a simple OpenAPI schema.
3. Produce a `quickstart.md` giving installation + verification steps for Ruff-only hooks.
4. Update agent context via `.specify/scripts/powershell/update-agent-context.ps1 -AgentType codex`
   so future agents know tooling choices.
5. Re-run Constitution Check to confirm no violations introduced (done; status PASS).

## Phase 2 – Upcoming Work (Planning Only)

- Update `.pre-commit-config.yaml` to remove Black/isort hooks and add Ruff equivalents.
- Ensure `pyproject.toml` (or `ruff.toml`) declares only necessary overrides (target version, minimal
  customizations).
- Refresh documentation (`README.md`, `contributing.md`, release notes) referencing Ruff.
- Adjust CI scripts/workflows to invoke the same `pre-commit` hooks, ensuring parity with local dev.
- Validate by running `pre-commit run --all-files` and pytest to guarantee no regressions.

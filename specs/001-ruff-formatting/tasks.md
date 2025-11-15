---
description: "Task list for adopting Ruff as the sole formatting/import tool"
---

# Tasks: Adopt Ruff Formatting Hooks

**Input**: Design artifacts from `/specs/001-ruff-formatting/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Tests**: Not explicitly requested; verification relies on `pre-commit run --all-files` and existing pytest suites.
**Organization**: Tasks are grouped by user story (US1–US3) so each slice remains independently testable.

## Format: `[ID] [P?] [Story] Description`

- `[P]` indicates the task can run in parallel (different files, no blocking dependencies).
- `[US#]` labels tie work to the user stories defined in the specification.
- All descriptions include the precise file or directory to touch.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the baseline dependency set required before modifying hooks or documentation.

- [x] T001 Update `pyproject.toml` and `poetry.lock` to remove `black`/`isort` dev dependencies and add `ruff` under `[tool.poetry.group.dev.dependencies]`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Centralize formatter configuration inside Ruff before story-specific implementation begins.

- [x] T002 Define the `[tool.ruff]` configuration (line length, target version, minimal rule toggles) and delete `[tool.black]`/`[tool.isort]` sections inside `pyproject.toml`.

---

## Phase 3: User Story 1 – Maintain formatting via Ruff (Priority: P1) 🎯 MVP

**Goal**: Contributors run Ruff automatically through pre-commit, ensuring only Ruff enforces formatting/import ordering.
**Independent Test**: After tasks complete, running `pre-commit run --all-files` must display only `ruff`/`ruff-format` hooks and exit cleanly once issues are resolved.

### Implementation

- [x] T003 [US1] Replace the Black/isort repos in `.pre-commit-config.yaml` with the official `astral-sh/ruff-pre-commit` hooks (`ruff` with `--fix` and `ruff-format`) so only Ruff enforces style before commits.

- [x] T004 [P] [US1] Refresh `.flake8` comments/ignores to reference Ruff’s formatting expectations (e.g., keep `E203/W503` rationale) so no references to Black/isort remain in lint configuration.

**Checkpoint**: User Story 1 complete when `pre-commit run --all-files` reforms code using Ruff only, and editor/on-save tooling matches those rules.

---

## Phase 4: User Story 2 – Document new workflow (Priority: P2)

**Goal**: Contributors understand Ruff is the sole formatter/import organizer and know how to run it locally.
**Independent Test**: A new contributor following the updated docs can install Ruff (via pre-commit) and reproduce CI formatting locally without confusion.

### Implementation

- [x] T005 [P] [US2] Update `README.md` badges/instructions to highlight Ruff (swap the Black badge, mention Ruff-driven formatting commands).
- [x] T006 [P] [US2] Rewrite the formatting guidance in `contributing.md` to describe installing Ruff via pre-commit, running `pre-commit run --all-files`, and removing all Black/isort references.
- [x] T007 [P] [US2] Author `docs/ruff-formatting.md` (and link it from `docs/index.rst`) detailing installation, troubleshooting stale hooks, and explaining how other tools can inspect graph data using Ruff-formatted code.

**Checkpoint**: User Story 2 complete when all contributor-facing docs consistently reference Ruff commands and onboarding steps.

---

## Phase 5: User Story 3 – Keep CI & historical compatibility (Priority: P3)

**Goal**: CI enforces Ruff just like local hooks without breaking existing workflows or Python support.
**Independent Test**: GitHub Actions (or equivalent CI) run `pre-commit` Ruff hooks on Python 3.8+ and fail the build if Ruff reports issues.

### Implementation

- [x] T008 [US3] Add `.github/workflows/pre-commit.yml` that leverages `pre-commit/action@v3` to run the Ruff hooks on every push and pull request.
- [x] T009 [P] [US3] Insert a `poetry run pre-commit run --all-files --hook-stage manual ruff ruff-format` step near the start of `.github/workflows/pytest.yml` so test pipelines verify Ruff compliance using the existing tooling stack.

**Checkpoint**: User Story 3 complete when CI pipelines fail on Ruff violations and still run on the documented Python versions without extra custom scripts.

---

## Phase N: Polish & Cross-Cutting Concerns

- [x] T010 Create `docs/release-notes.md` (and reference it from `README.md` or docs navigation) summarizing the Ruff migration and providing upgrade guidance for downstream consumers.

---

## Dependencies & Execution Order

- **Phase sequencing**: Complete Setup (T001) → Foundational (T002) → US1 → US2 → US3 → Polish.
- **User story dependencies**:
  - US1 (P1) depends on T001–T002.
  - US2 (P2) depends on US1, since documentation must describe the finalized tooling.
  - US3 (P3) depends on US1 (CI must run the new hooks) but can proceed in parallel with US2 once Ruff is configured.
- **Cross-cutting**: Polish tasks run last to capture release/migration guidance once all stories stabilize.

## Parallel Opportunities

- Within **US1**, T004 and T005 modify independent files and can run in parallel after T003.
- Within **US2**, tasks T006–T008 touch different docs and can be parallelized to speed authoring.
- In **US3**, T009 and T010 affect different workflow files; they can be developed concurrently once T003 completes.

## Implementation Strategy

1. **MVP (US1 only)**: Execute T001–T005 to switch local tooling to Ruff; verify `pre-commit run --all-files` succeeds.
2. **Incremental Delivery**: Layer US2 documentation updates (T006–T008), ensuring contributors understand the new workflow.
3. **Full Enforcement**: Finish with US3 CI tasks (T009–T010) so pipelines gate on Ruff.
4. **Polish**: Publish migration notes (T011) and update contributor templates (T012), then run the full verification commands described in the plan.

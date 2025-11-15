<!--
Sync Impact Report
Version change: 0.0.0 → 1.0.0
Modified principles:
- [PRINCIPLE_1_NAME] → Framework-Only Scope
- [PRINCIPLE_2_NAME] → Plain Python Simplicity
- [PRINCIPLE_3_NAME] → Portable Graph Serialization
- [PRINCIPLE_4_NAME] → Test-Driven Total Coverage
- [PRINCIPLE_5_NAME] → Stable APIs & Dual-Python Support
Added sections:
- Engineering Constraints
- Development Workflow & Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
Follow-up TODOs:
- None
-->
# Flowpipe Constitution

## Core Principles

### I. Framework-Only Scope
Flowpipe ships only the graph, node, plug, and evaluation framework. Core code MUST remain
domain-agnostic: contributions MAY NOT add business-specific node implementations, external
service wrappers, or bundled workflows. Examples and docs can demonstrate user-defined
nodes, but the runtime stays a thin framework so teams own their node libraries. Rationale:
the project’s value is the reusable framework, not pre-baked logic, which keeps Flowpipe
lightweight.

### II. Plain Python Simplicity
Flowpipe MUST run with normal Python tooling and never require bespoke environments,
background services, or infrastructure. New dependencies MUST be justified, pure-Python
when possible, and optionalized if they raise the project’s footprint. APIs MUST embrace
idiomatic Python constructs (classes, decorators, dataclasses where compatible) so users can
work inside familiar workflows. Rationale: simplicity keeps adoption friction low and honors
Flowpipe’s lightweight promise.

### III. Portable Graph Serialization
Graphs and nodes MUST stay serializable so they can execute remotely (render farms, job
queues, services). State belongs in plugs and metadata; hidden runtime state is forbidden.
Node metadata MUST capture everything remote evaluators need, and serialization formats
must stay stable so external converters—documented but not maintained here—can rebuild
graphs. Rationale: serialization is the bridge that lets Flowpipe stay framework-only yet run
anywhere.

### IV. Test-Driven Total Coverage
Every change follows red-green-refactor: author tests that fail, implement code, refactor with
green tests. Coverage MUST remain at 100% with pytest across supported Python versions.
New features require targeted unit tests plus higher-level coverage (integration/functional)
when behavior spans nodes/graphs. Skipping tests or marking `# pragma: no cover` demands
documented justification. Rationale: Flowpipe is engineered test-first, and exhaustive tests
ensure safe serialization and remote execution.

### V. Stable APIs & Dual-Python Support
The public API MUST remain backward compatible for Python 3.7+ consumers until
governance explicitly retires that guarantee. Deprecations require a migration path and
semantic versioning (MAJOR for breaking changes, MINOR for backward-compatible features,
PATCH for fixes). Metadata in `pyproject.toml`, docs, and release notes MUST stay in sync so
downstream automation remains trustable. Rationale: pipelines depend on Flowpipe stability.

## Engineering Constraints

- Repository content MUST stay focused on framework modules (`flowpipe/*`), documentation,
  and examples. Example nodes remain under `examples/` and never bleed into installable
  packages.
- Serialization requirements MUST be met by keeping plug payloads JSON/pickle friendly, and
  by guarding against implicit references (open file handles, live connections, global singletons).
- Tooling MUST use Black formatting and Google-style docstrings; lint/test hooks in
  `.pre-commit-config.yaml` MUST remain green before merge.
- Documentation MUST accompany new behaviors, covering how to keep nodes simple,
  serialize metadata, and run graphs locally versus remotely. Conversion guides live in docs,
  not in runtime code.
- Releases follow the documented recipe (update `pyproject.toml` + `docs/conf.py`, tag, publish)
  so PyPI consumers get reproducible artifacts with matching metadata.

## Development Workflow & Quality Gates

1. **Specification First**: Each feature starts with `specs/[feature]/spec.md`, capturing independent
   user stories, serialization considerations, and backward-compatibility notes.
2. **Implementation Plan**: Plans must document how the work obeys every core principle,
   especially framework scope, serialization, and TDD coverage expectations.
3. **Task Breakdown**: Tasks are grouped per user story so increments stay independently
   deliverable and testable. Each task references precise paths and required tests.
4. **Testing Discipline**: Contributors run pre-commit hooks plus pytest across supported Python
   versions. Pull requests link coverage diffs proving 100% coverage is intact.
5. **Serialization Proof**: Features that touch graph/node data include reproduction steps (docs
   or tests) showing the new metadata serializes/deserializes cleanly without custom runtimes.

## Governance

- This constitution governs every Flowpipe contribution. Conflicting practices defer to this file.
- Amendments require: (a) an issue outlining the change and rationale, (b) agreement from at
  least two maintainers, (c) synchronized updates to dependent templates/docs, and (d) a
  recorded version bump with dates.
- Version bumps follow semantic rules described in Principle V. Ratification date records when
  v1.0.0 was adopted; Last Amended reflects the latest accepted change.
- Compliance Review: Every PR must cite how it satisfies each principle (link to plan/spec
  sections). Reviews block until gaps are resolved or explicitly deferred with TODOs noted here.

**Version**: 1.0.0 | **Ratified**: 2025-11-14 | **Last Amended**: 2025-11-14

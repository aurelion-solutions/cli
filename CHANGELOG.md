# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.10.0] - 2026-05-12

### Changed

- **`al employees list` and `al persons list` accept `--limit` and `--offset` (Phase 20 M-C).** Both commands now pass `limit` (default 1000, 1-1000) and `offset` (default 0) to the kernel endpoint as query parameters, matching the pagination contract. The response is the full kernel envelope `{items, total, limit, offset}` printed verbatim.
- Phase 19 Step A2: `al reconciliation` command renamed to `al inventory-reconcile`
- REST endpoint updated to `/api/v0/inventory-reconciles/runs`

## [0.9.0] - 2026-05-12

### Added

- Phase 18 Native Pipeline Orchestrator CLI surface
- `al pipelines list [--format text|json] [--base-url URL]` — GET `/api/v0/pipelines`; prints one line per pipeline (name, version, step_count, trigger count)
- `al pipelines show NAME [--format text|json] [--base-url URL]` — GET `/api/v0/pipelines/{name}`; prints header block, triggers, and steps; 404 → human-readable error
- `al pipelines runs list [--pipeline NAME] [--status STATUS]... [--limit N] [--offset N] [--format text|json] [--base-url URL]` — GET `/api/v0/pipeline-runs`; `--status` repeatable; pagination delegated to API
- `al pipelines runs get RUN_ID [--format text|json] [--base-url URL]` — GET `/api/v0/pipeline-runs/{run_id}`; `RUN_ID` is UUID (Typer-validated); 404 → human-readable error
- `al pipelines run NAME [--args JSON] [--version N] [--format text|json] [--base-url URL]` — POST `/api/v0/pipeline-runs`; `--args` must be a JSON object (exit 2 on invalid); omits `pipeline_version` when `--version` not supplied; treats 200 (idempotent dedupe) and 201 (fresh insert) as success; 404 → `Pipeline not loaded`, 422 with detail → `Invalid args: <detail>`, other errors → generic API error
- `al pipelines runs cancel RUN_ID [--format text|json] [--base-url URL]` — POST `/api/v0/pipeline-runs/{run_id}/cancel`; 404 → `Pipeline run not found`, 409 → kernel detail verbatim
- `al pipelines runs retry RUN_ID [--format text|json] [--base-url URL]` — POST `/api/v0/pipeline-runs/{run_id}/retry`; 404 → `Pipeline run not found`, 409 → kernel detail verbatim; output includes `retry_of_run_id` field

### Changed

- CLI test suite consolidated: 30 trivial files merged into 4 parametrized files, 143 tests preserved, file count 53 → 27

### Removed

- `al lake migrate-from-pg` command and `LakeMigrationClient` retired (kernel `engines/lake_migration` slice retired in Phase 17 Step 13). `al lake status`, `al lake compact`, and `al datalake` are unaffected.
- `--event-type` flag from `al logs buffer` — the underlying `GET /api/v0/log-buffer` endpoint no longer accepts an `event_type` filter parameter (Phase 17 Step 4).

## [0.1.5] - 2026-04-27

### Added

- Phase 15 Data Lake Migration complete (20/20 milestones)
- `al lake status [--base-url URL]` — calls `GET /api/v0/lake/status`; prints catalog URI, warehouse URI, storage provider, and per-table snapshot metadata as indented JSON
- `al lake compact [--table ...] [--retention-days N] [--orphan-older-than-hours N] [--target-file-size-mb N] [--base-url URL]` — calls `POST /api/v0/lake/compaction`
- `al lake migrate-from-pg [--dataset all|access_artifacts|access_facts] [--batch-size N] [--resume <run_id>] [--poll-interval N]` — PG → Iceberg migration client; polls until terminal
- `al datalake batches list [--limit INT] [--cursor STR] [--base-url URL]` — calls `GET /api/v0/datalake/batches`; prints paginated batch list as indented JSON
- `al/lake/` package with HTTP client and Typer subapp

## [0.1.4] - 2026-04-26

### Added

- `al llm profile list` — GET `/api/v0/llm/execution-profiles`; prints one profile per line (`id  name  model=<model_id>`). (Phase 14 Step 9)
- `al llm profile show <id>` — GET `/api/v0/llm/execution-profiles/{id}`; prints profile as indented JSON. (Phase 14 Step 9)
- `al llm profile create --name STR --model-id UUID [--param-overrides JSON|@path]` — POST `/api/v0/llm/execution-profiles`; prints created profile as JSON. (Phase 14 Step 9)
- `al llm profile update <id> [--name STR] [--param-overrides JSON|@path]` — PATCH `/api/v0/llm/execution-profiles/{id}`; sends only supplied fields (no phantom nulls); `--param-overrides` replaces the dict. (Phase 14 Step 9)
- `al llm profile delete <id> --yes` — DELETE `/api/v0/llm/execution-profiles/{id}`; requires `--yes` to confirm; exits 1 without it. (Phase 14 Step 9)
- `al sod apply <file> [--created-by TEXT] [--dry-run]` — config-as-code idempotent upsert of SoD rules from YAML or JSON; capabilities referenced by slug; prints diff summary on success; `--dry-run` prints resolved payload without sending

### Changed

- `al inventory access-facts list`: `--action` flag renamed to `--action-slug`. **Breaking** for scripts using the old flag. (Phase 12 Step 13)
- `al inventory artifact-bindings list`: `--access-fact`, `--resource`, `--account` flags replaced with `--target-type` and `--target-id`
- `al inventory artifacts list`: renamed `--source-kind` flag to `--artifact-type`. **Breaking** for scripts using the old flag. (Phase 12 Step 7)

### Added

- `al sod evaluate <subject_id> [--at ISO8601]` — POST `/sod/evaluate`; omitting `--at` lets the server default to `now(UTC)`. (Phase 13 Step 17)
- `al sod what-if <subject_id> [--override CAP_ID:SCOPE_KEY_ID:SCOPE_VALUE_OR_NULL:APP_UUID ...]` — POST `/sod/what-if` with synthetic capability overrides; `--override` is repeatable; literal `null` (case-insensitive) for scope_value sends JSON `null`; malformed override exits 2. (Phase 13 Step 17)
- `al sod resolve-capabilities [--file PATH]` — POST `/sod/resolve-capabilities`; accepts `{"sources": [...]}` or top-level list; reads stdin when `--file` is omitted. (Phase 13 Step 17)
- `al scan run [--triggered-by manual|api|schedule] [--scope-subject UUID] [--scope-application UUID]` — two-step: POST `/scan-runs` then POST `/scan-runs/{id}/run`; orphan pending run left as-is on step-2 failure. (Phase 13 Step 17)
- `al scan list [--status] [--triggered-by] [--scope-subject UUID] [--scope-application UUID] [--limit INT] [--offset INT]` — GET `/scan-runs` with optional query params; default limit 50. (Phase 13 Step 17)
- `al findings list [--scan-run INT] [--rule INT] [--severity] [--status] [--kind] [--subject UUID] [--limit INT] [--offset INT]` — GET `/findings` with audit-style filters; default limit 50. (Phase 13 Step 17)
- `al feedback post --kind KIND --message TEXT [--rule INT] [--mapping INT] [--finding INT] [--subject UUID] [--payload-file PATH]` — POST `/feedbacks`; at least one of `--rule`, `--mapping`, `--finding` required client-side (exits 2 if missing). (Phase 13 Step 17)
- Exit code 2 introduced for client-side validation failures (`--override` parsing, missing target FK for feedback, malformed JSON file). Exit code 1 remains for API/connection/timeout errors.
- `al reconciliation run --application-id <UUID>` — triggers artifact-first reconciliation and prints the eight-field run summary; exit code 0 on success, non-zero on error
- `al inventory actions list` and `al inventory action <slug>` — read-only commands over the `GET /actions` and `GET /actions/{slug}` endpoints. No filters, no pagination — the vocabulary is 7 seeded slugs. Reference docs live at `docs/cli/inventory/actions.md`.

### Removed

- `al app reconcile` no longer prints `Roles:` and `Privileges:` summary lines. The `ReconciliationResult` response shape dropped `roles` / `privileges` fields as part of Phase 12 Step 1 (kernel). CLI output now shows only `Accounts:`.

## [0.1.1] - 2026-04-22

### Added

- **`al events tail`** and **`al logs tail`** — thin clients over the new platform read endpoints added in Phase 11 Step 5.

## [0.1.0] - 2026-04-18

### Added

- Phase 8 CLI surface for Remote Resources Normalization (Steps 1–16 + Step 17 parity add-ons)
- `al inventory customers list [--plan <tier>] [--locked]` — list customer entities
- `al inventory subjects list [--kind <k>] [--status <s>]` — list subjects with kind/status filters
- `al inventory subject <id>` — show subject merged with its attributes (client-side merge of two GETs)
- `al inventory threat-facts {list,get,upsert}` subcommands with `--subject` / `--min-risk-score` filters; `upsert` accepts repeatable `--indicator`
- `al inventory usage-facts {list,get,create}` subcommands; `list` supports `--subject`, `--resource`, `--access-fact`, `--since`, `--limit`; `create` requires `--access-fact`, `--last-seen`, `--usage-count`, `--window-from` and optionally `--window-to`
- `al inventory ownership-assignments {list,get,create,delete}` subcommands with `--subject`, `--resource`, `--account`, `--kind` filters; `create` enforces XOR `--resource`/`--account` client-side before hitting the API
- `al inventory initiatives {list,get,create,update}` subcommands with `--access-fact` / `--type` filters
- `al inventory artifact-bindings {list,get}` subcommands with `--artifact`, `--access-fact`, `--resource`, `--account` filters (read-only)
- `al inventory access-facts {list,get}` subcommands with `--subject`, `--resource`, `--account`, `--action`, `--effect`, `--valid-at` filters (read-only)
- `al inventory artifacts {list,get}` subcommands with `--application`, `--source-kind`, `--limit` filters (read-only audit surface)
- `al inventory resources {list,get,create,update,attributes,add-attribute,remove-attribute}` subcommands with application/kind/privilege-level/environment/data-sensitivity filters
- `al inventory accounts {list,get,update}` commands. Supports filters `--application`, `--status`, `--subject` on list; PATCH of `status` and `subject_id` on update.
- al app create gains required --code option; code is included in POST payload and printed in output
- Phase 5 Identity Core Domain CLI surface (Person, Employee, EmployeeRecord, NHI)
- al persons list, get, attributes (read-only person operations)
- al employees list, get, attributes (read-only employee operations)
- al employee-records list, get, attributes (read-only employee record operations)
- al nhi list, get, create, attributes, add-attribute, remove-attribute
- al logs read (--limit) for reading recent platform logs via configured log provider
- al datalake batches create, get, data, delete for lake batch operations
- al secrets list, create, get, delete for secret management
- al secrets provider list, create, get, delete for provider CRUD
- al app list for listing applications
- al app create and al app delete for application lifecycle
- al app subcommand with app reconcile run for triggering reconciliation

### Deferred (parked, not in scope)

- `al policy evaluate --rule-pack <path>` — parked until a future Rule Authoring phase; kernel `POST /policy/evaluate` has no sink for an inline rule pack today
- Aggregate counts (accounts / access-facts / initiatives) in `al inventory subject <id>` — parked until first downstream consumer materialises (likely a UI/dashboard phase)

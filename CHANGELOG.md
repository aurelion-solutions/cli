# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

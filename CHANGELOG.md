# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.7.0] - 2026-06-07

### Added
- `get_work_package` gained an `include` param: `include=["children","relations"]` embeds full subtask details and the relation list in the same response, collapsing the old three-call pattern (`get_work_package` + `list_children` + `get_relations`) into one. Values are validated (`validators.validate_include` + `ALLOWED_INCLUDES`); unknown values raise. Tool count unchanged (44).
- `get_work_package` now always returns `parent_id` + `parent_subject` (extracted from HAL `_links.parent`, no extra API call; both `null` for a root work package) via new pure `formatters._parent_fields`.

### Changed
- Extracted shared work package fetchers into new `server/wp_helpers.py` (`_fetch_children`, `_fetch_relations`); `list_children` and `get_relations` are now thin wrappers over them (DRY), and `get_work_package` reuses them for its `include` expansions. `list_children.total` now reflects the count returned (≤100) rather than the API's full count — the returned items are identical.

## [0.6.0] - 2026-06-07

### Added
- `delete_work_package(wp_id)` — permanently delete a work package (API v3 `DELETE /work_packages/{id}`); irreversible, double-confirm convention in docstring (mirrors `delete_news`). Tool count 41 → 44.
- `bulk_update_work_packages(ids, …)` and `bulk_create_work_packages(project, items)` — apply one shared field-set across many work packages, or create many in one call. Continue-on-error: a failed item never aborts the rest; result is an envelope `{updated|created, failed, ok_count, fail_count, total}` — read `failed`. New `server/tools_bulk.py` + pure `server/bulk_helpers.py` (`summarize_bulk`). `bulk_create` is flat (per-item `parent_id` may point at an existing work package; no intra-call sibling refs).
- Name-based params (resolve name → ID at call time, alongside existing `*_id`): `create_work_package` accepts `type` (project-scoped) and `priority`; `update_work_package` accepts `status` and `priority`. Passing both a name and its `*_id` raises. New `server/resolvers.py` (`match_by_name`, `resolve_status_id`, `resolve_priority_id`, `resolve_type_id`).
- `update_work_package` gained a `priority`/`priority_id` link (previously had neither).
- `list_types` accepts an optional `project` argument → queries `/projects/{id}/types` (only types enabled in that project) to avoid 422 when creating a work package with a disabled type. Without it, behaviour is unchanged (global `/types`). No new tool.
- Scrum type taxonomy skill guidance: new `skills/openproject-manager/references/work-package-hierarchy.md` teaches Epic→Story→Task hierarchy, name-based type auto-mapping (ask-once on ambiguity), guided create recipes, and advisory parent-child validation. Routed for "tạo epic/story/task", "breakdown epic", "dựng backlog" intents; cross-linked from project-manager and coder personas.

### Changed
- `update_work_package.lock_version` is now optional: when omitted the tool fetches the current `lockVersion`, and on HTTP 409 it refetches and retries the PATCH once (kills the lock-conflict storm from parent rollups). Trade-off: an auto-retry can overwrite a concurrent edit made between attempts — acceptable for single-actor use, documented in the docstring. New `op_client.patch_wp_with_lock` + typed `op_client.ConflictError`.
- Test command now includes `httpx` (`uv run --with pytest --with httpx pytest -q tests/`) since the suite now imports `op_client` for the lock-retry unit tests.

### Fixed
- Stale tool count in `CLAUDE.md` (38 → 41) and its verify command (added missing `tools_notifications` import).

## [0.5.0] - 2026-06-07

### Added
- `list_activities(wp_id)` — read a work package's comments and change history (API v3 `/work_packages/{id}/activities`); distinguishes comments from field changes.
- Custom fields on work packages: `get_work_package` now returns `custom_fields`; `create_work_package` and `update_work_package` accept a `custom_fields` param (by field ID) — scalar fields set at top level, link-type fields (user/version/list) via href. New pure `server/custom_fields.py` (`extract_custom_fields`, `apply_custom_fields`) with unit tests.
- Personal notifications: `list_notifications` (unread by default) and `mark_notification_read` (API v3 `/notifications`, mark via `read_ian`). New `server/tools_notifications.py`. Requires OpenProject ~12.1+.
- `_fmt_activity` and `_fmt_notification` formatters + unit tests.

## [0.4.0] - 2026-06-07

### Added
- News tools: `list_news`, `get_news`, `create_news`, `update_news`, `delete_news` — full CRUD over the API v3 News endpoint (`/api/v3/news`); routed under project-manager and admin personas. Writes confirm-first; `delete_news` double-confirms. Requires the "manage news" permission (403 otherwise).
- `_fmt_news` formatter + unit test.

## [0.3.1] - 2026-06-07

### Fixed
- `POST` writes are no longer retried on `429`/`5xx`, preventing duplicate creates (relations, work packages, time entries, comments, members) when a response is lost after a successful write. Idempotent `GET`/`PATCH`/`DELETE` still retry.

### Added
- Relation guards in `create_relation`: rejects self-relation, duplicate (either direction), and direct 2-node cycles (`blocks`/`precedes` reverse) before hitting the API, via a new pure `server/validators.py` (`validate_relation`).
- Re-parenting: `update_work_package(parent_id=...)` moves an existing work package under a new parent.
- Clearer `404` errors that name the request path.
- Coder skill guidance: relation direction, single-direction rule, scheduling side-effects, same-project parent, dedupe-before-create, bulk-confirm, and truncation notes.
- Unit tests for `validate_relation`.

## [0.3.0] - 2026-06-07

### Added
- Persona-aware skill: one router `SKILL.md` + `references/{member,project-manager,coder,admin,reporting}.md`; role detection via intent + `whoami` roles.
- Coder tools: `list_children`, `get_relations`, `create_relation`; subtasks via `create_work_package(parent_id=...)`.
- Manager tools: `list_versions`, `report_workload`, `report_status_board`, `report_time`, `report_portfolio`.
- Member tool: `my_time_summary` (hours grouped by project and work package).
- Admin tools: `list_users`, `get_user`, `list_roles`, `create_project`, `update_project` (incl. archive), `add_member`, `update_member`, `remove_member` — confirm-first, double-confirm for destructive.
- New filters on `list_work_packages`: `type_id`, `version_id`, `assignee_id`, `due_within_days`.
- Reporting capability: CSV export + professional HTML reports from report-tool JSON.
- Unit tests for pure helpers; CI test job.

### Changed
- Split `server/server.py` into a package (config, op_client, formatters, app, tools_*) for maintainability; behavior of the original 16 tools unchanged.
- Client now surfaces HTTP 403 (insufficient permission) with a clear message.

## [0.2.1] - 2026-06-07

### Changed
- Read `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` from the environment; `.mcp.json` no longer contains secrets and is committed to the repo (removed `.mcp.json.example`).
- Added `.claude-plugin/marketplace.json` for direct install via `/plugin marketplace add`.
- Rewrote the README in English and generalized the plugin for any OpenProject instance (removed the hardcoded URL).
- Added an "AI agent quick setup" flow — paste a link and the agent self-installs.

### Added
- Project health files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue/PR templates, and `.editorconfig`.
- CI workflow: ruff lint, ruff format check, Python syntax check, and JSON config validation.

## [0.2.0] - 2026-06-07

### Changed
- Separated secrets from git; shared HTTP client (connection reuse); one retry on `429`/`5xx` honoring `Retry-After`; clearer `401` errors; logging to stderr.
- Added the MIT license, this changelog, and ruff configuration.

## [0.1.0] - 2026-06-07

### Added
- Python MCP server (FastMCP) for OpenProject API v3 with 16 tools — work packages, projects/members, metadata, time tracking, and reports.
- `openproject-manager` skill with workflow guidance.

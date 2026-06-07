# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project adheres to
[Semantic Versioning](https://semver.org/).

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

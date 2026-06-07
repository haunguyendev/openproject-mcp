# Codebase Summary — openproject-mcp

## Overview

The openproject-mcp project is a single-file MCP server (via PEP 723) split into modular sub-files for maintainability. All Python files are under `server/`, target <200 LOC for optimal context management (a few tool modules exceed it: `tools_work_packages.py` 272, `tools_reports.py` 226, `tools_admin.py` 205).

**Total lines of code (server/):** ~1,841 LOC across 18 files  
**Total tools:** 44 MCP tools across 9 tool modules  
**Test coverage:** Pure helpers tested (formatters, validators)  
**CI pipeline:** Lint, format, syntax, JSON validation, unit tests

## Module Breakdown

| File | LOC | Responsibility |
|------|-----|---|
| `server.py` | 47 | Entry point; imports tools_* for @mcp.tool() registration; logs startup info; calls `mcp.run()` |
| `app.py` | 5 | Shared FastMCP("openproject") instance for tool registration |
| `config.py` | 19 | Environment variables (OPENPROJECT_URL, OPENPROJECT_API_KEY, OPENPROJECT_TIMEOUT_SECONDS); stderr logging |
| `op_client.py` | 131 | Shared httpx.Client; Basic Auth (user "apikey", pass = token); `_req` with idempotent retry; typed `ConflictError` (409); `patch_wp_with_lock` (auto lockVersion + 409 retry-once); `_collection` pagination; clear error messages |
| `formatters.py` | ~90 | HAL+JSON trimming helpers: `_fmt_wp`, `_fmt_news`, `_fmt_activity`, `_fmt_notification`; `_href_id`, `_link_title`; time conversion; `_out` wrapper |
| `validators.py` | 75 | Pure stdlib: `validate_relation()` guards (rejects self, duplicate, direct cycles); `RELATION_TYPES` canonical list |
| `resolvers.py` | 51 | Name→ID resolution: pure `match_by_name` (case-insensitive, ambiguous/not-found guards) + `resolve_status_id` / `resolve_priority_id` / `resolve_type_id(name, project)` |
| `custom_fields.py` | ~60 | Pure stdlib: `extract_custom_fields()` (read) + `apply_custom_fields()` (write) for work package `customFieldN` (scalar + link-type) |
| `bulk_helpers.py` | 18 | Pure stdlib: `summarize_bulk()` builds the bulk result envelope (updated/created, failed, ok/fail/total counts) |
| `tools_work_packages.py` | 272 | list_work_packages, get_work_package (incl. custom_fields), create_work_package (type/priority by name), update_work_package (optional lock_version + auto-retry, status/priority by name), add_comment, list_activities, delete_work_package |
| `tools_bulk.py` | 153 | bulk_update_work_packages (shared fields, continue-on-error, reuses patch_wp_with_lock), bulk_create_work_packages (flat, per-item resolve) |
| `tools_projects.py` | 118 | list_projects, list_project_members, list_versions, list_types, list_statuses, list_priorities, whoami |
| `tools_coder.py` | 100 | list_children, get_relations, create_relation (uses validators + prefetch) |
| `tools_time.py` | 123 | log_time, list_time_entries, my_time_summary |
| `tools_reports.py` | 226 | report_overdue, report_my_tasks, report_project_progress, report_workload, report_status_board, report_time, report_portfolio (CSV + HTML export) |
| `tools_news.py` | 104 | list_news, get_news, create_news, update_news, delete_news (v0.4.0) |
| `tools_notifications.py` | ~40 | list_notifications (unread default), mark_notification_read (v0.5.0; needs OpenProject ~12.1+) |
| `tools_admin.py` | 205 | list_users, get_user, list_roles, create_project, update_project, add_member, update_member, remove_member; confirm-first, double-confirm destructive |

## Tool Inventory by Role

### Member (5 tools)
- `list_work_packages` — filter by status, assignee, due
- `get_work_package` — fetch single item
- `add_comment` — add note to work package
- `list_time_entries` — view logged hours
- `my_time_summary` — hours grouped by project/package

### Project Manager (14 tools)
- `list_projects`, `list_project_members`, `list_versions`, `list_types` (optional `project` → project-scoped types, avoids 422 on disabled types), `list_statuses`, `list_priorities` — metadata
- `create_work_package` (type/priority by name), `update_work_package` (optional lock_version + auto 409 retry; status/priority by name) — task management
- `delete_work_package` — permanent delete (irreversible, double-confirm)
- `bulk_update_work_packages`, `bulk_create_work_packages` — batch ops (continue-on-error)
- `create_news`, `update_news`, `delete_news` — project news
- `report_workload`, `report_status_board`, `report_time`, `report_portfolio` — analytics

### Coder (6 tools)
- `create_work_package` (with parent_id, type by name) — subtasks
- `bulk_create_work_packages` — batch subtasks under existing parent
- `list_children` — view task hierarchy
- `get_relations` — dependency map
- `create_relation` — add links (with guards)
- `update_work_package` (with parent_id) — re-parent

### Admin (8 tools)
- `list_users`, `get_user`, `list_roles` — user management
- `create_project`, `update_project` — project admin
- `add_member`, `update_member`, `remove_member` — member admin

### Reporting (7 tools)
- `report_overdue` — overdue tasks by project
- `report_my_tasks` — my task summary
- `report_project_progress` — progress by type/status
- `report_workload` — member load
- `report_time` — time tracking summary
- `whoami` — identity check

### News (5 tools)
- `list_news`, `get_news`, `create_news`, `update_news`, `delete_news`
- Requires "manage news" permission; write tools confirm; delete double-confirms
- New in v0.4.0

## Request Flow

```
Claude (natural language)
  ↓
MCP Client (Claude Code / Desktop / Cowork)
  ↓
stdio → FastMCP.run() → @mcp.tool() dispatcher
  ↓
tools_*.py function (validates input, calls op_client)
  ↓
op_client._req() (HTTP Basic Auth, retry logic, error handling)
  ↓
OpenProject REST API v3 (/api/v3/work_packages, /api/v3/projects, etc.)
  ↓
formatters._fmt_* (trim JSON, extract url, format dates)
  ↓
MCP response → Claude (parsed by AI, user sees result)
```

## HTTP Client Design

**`op_client.py` exports:**
- `_req(method, path, **kwargs)` — low-level request with:
  - Basic Auth header: username "apikey", password = `API_KEY`
  - Single retry on 429 (Retry-After) and 5xx — **except POST** (prevents duplicate creates)
  - Clear 401/403/404 errors
  - Timeout per `config.TIMEOUT`
- `_collection(path, **params)` — paginated GET with offset/limit
- Shared `httpx.Client` for connection reuse

**Idempotency model:**
- GET/PATCH/DELETE retry on transient failures
- POST never retry (write-once semantics)
- Optimistic locking: `update_work_package` auto-fetches `lockVersion` when omitted and retries once on 409 (`op_client.patch_wp_with_lock` + typed `ConflictError`); bulk update reuses the same path

## Tool Design Conventions

1. **Naming:** Verb-first, clear English, no abbreviations
   - ✅ `create_work_package`, `list_projects`, `report_overdue`
   - ❌ `mk_wp`, `ls_proj`, `ovd_rpt`

2. **Docstrings (Vietnamese):** Describe every parameter + return value; Claude reads these to learn tool usage

3. **Parameters:** Explicit, no magic values; `required=True` in schema

4. **Return value:** Trimmed JSON + `url` field for direct OpenProject link
   ```python
   {
     "id": 123,
     "subject": "Fix login bug",
     "project": {"id": 42, "name": "Website"},
     "status": {"name": "In Progress"},
     "url": "https://openproject.example.com/work_packages/123"
   }
   ```

5. **Write confirmation:** Use `skill` (bundled persona router) to confirm before mutating

6. **Error messages:** Clear, actionable, no stack traces

## Testing

| File | Lines | Tests | Notes |
|------|-------|-------|-------|
| `test_formatters.py` | 16 lines | 16 unit tests | Pure helpers: `_fmt_wp`, `_href_id`, time conversion |
| `test_validators.py` | 2,907 lines | 16 tests | `validate_relation` guards: self, duplicate, cycles |

**Run tests:**
```bash
uv run --with pytest --with httpx pytest -q tests/
```

**Coverage:** Pure helpers only; integration tests via manual API calls recommended.

## CI/CD Pipeline

**File:** `.github/workflows/ci.yml`

**Jobs:**
1. **Lint & syntax** (runs on push + PR)
   - `uvx ruff check server/` — style lint
   - `uvx ruff format --check server/` — format check
   - `python -m py_compile server/*.py` — syntax validation
   - JSON config validation (`.mcp.json`, `.claude-plugin/*.json`)

2. **Tests** (runs on push + PR)
   - `uv run --with pytest --with httpx pytest -q tests/`
   - Must pass before merge

**Versioning checklist** (manual, before release):
1. Update `__version__` in `server/server.py`
2. Update version in `.claude-plugin/plugin.json`
3. Update version in `.claude-plugin/marketplace.json`
4. Add CHANGELOG entry under `[VERSION] - YYYY-MM-DD`
5. Commit + tag: `git tag vX.Y.Z && git push --tags`

## Code Style

- **Language:** Python 3.10+
- **Format:** `ruff format server/` (line length 100, consistent indentation)
- **Lint:** `ruff check server/` (no unused imports, clear variable names)
- **Docstrings:** Vietnamese (project convention; tool docstrings teach Claude)
- **Comments:** Explain "why," not "what"; code is self-documenting
- **File size:** <230 LOC per file (hard limit: 1,361 total / 13 files = ~105 LOC avg)

## Security Model

1. **No secrets in repo**
   - `.mcp.json` declares runtime; credentials from env only
   - Verify no keys leaked: `git grep -iE "api[_-]?key.*[a-f0-9]{40}"`

2. **HTTP Basic Auth**
   - Username: `"apikey"` (constant)
   - Password: `API_KEY` (from env)
   - Never logged; never in tool output

3. **Permission checks**
   - Tools fail with 403 Forbidden if user lacks role (e.g., "manage news" for news tools)
   - Clear error message: "Insufficient permission"

4. **Optimistic locking**
   - Write tools require current `lockVersion`
   - Concurrent edits rejected (409 Conflict)
   - User sees: "Task was edited concurrently; refresh and try again"

## Dependency Management

**Declared via PEP 723 in `server/server.py`:**
```python
# requires-python = ">=3.10"
# dependencies = [
#     "mcp>=1.2.0",
#     "httpx>=0.27",
# ]
```

**Install/run:**
```bash
uv run --script server/server.py
```

No `requirements.txt`, no virtualenv, no `pip install` — `uv` handles it.

## Recent Changes

- **v0.6.0** — WP write ergonomics: `delete_work_package`; `bulk_update_work_packages` + `bulk_create_work_packages` (`tools_bulk.py`, `bulk_helpers.py`); name params for status/type/priority (`resolvers.py`); `update_work_package` optional lock_version + auto 409 retry-once (`patch_wp_with_lock`, `ConflictError`). 41 → 44 tools.
- **v0.5.0** — Activities, custom fields, notifications (`tools_notifications.py`, `custom_fields.py`)
- **v0.4.0** — News tools added (list, get, create, update, delete news)
- **v0.3.1** — Relation guards, idempotent POST, re-parenting, coder skill guidance
- **v0.3.0** — Persona routing, admin + reporting tools, test + CI

## Next Steps

See `project-roadmap.md` for planned work:
- Polish news workflow (bulk operations)
- Broader cycle detection in relations
- Cross-project hierarchy support

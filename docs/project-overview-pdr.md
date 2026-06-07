# OpenProject MCP — Project Overview & Requirements

## Executive Summary

**openproject-mcp** is an MCP (Model Context Protocol) server and Claude plugin that bridges Claude AI with self-hosted OpenProject instances. It enables natural-language project management through a comprehensive set of tools for work packages, projects, members, time tracking, and reporting.

**Version:** 0.6.0  
**Status:** Stable, active development  
**License:** MIT

## Problem Statement

Project managers and team members waste time toggling between OpenProject UIs and their AI assistant. They want to ask Claude things like:
- *"What's overdue in the Website project?"*
- *"Create a task and assign it to Nam, due Friday"*
- *"How many hours did I log this week?"*

Without context switching to OpenProject's web interface. This plugin solves that by making OpenProject's full REST API v3 queryable via natural language.

## Target Users

1. **Team Members** — track tasks, log time, request reports
2. **Project Managers** — manage members, versions, progress, workload
3. **Developers** — query work packages, manage relations, create subtasks (via coder persona)
4. **Admins** — create/archive projects, manage users and roles

## Scope

### Functional Requirements

44 MCP tools across 4 personas, grouped by area:

| Area | Tools | Count |
|------|-------|-------|
| Work packages | list, get, create, update, add_comment, list_activities | 6 |
| Projects & metadata | list_projects, list_project_members, list_versions, list_types, list_statuses, list_priorities, whoami | 7 |
| Coder | list_children, get_relations, create_relation | 3 |
| Time tracking | log_time, list_time_entries, my_time_summary | 3 |
| Reports | report_overdue, report_my_tasks, report_project_progress, report_workload, report_status_board, report_time, report_portfolio | 7 |
| News | list_news, get_news, create_news, update_news, delete_news | 5 |
| Notifications | list_notifications, mark_notification_read | 2 |
| Admin | list_users, get_user, list_roles, create_project, update_project, add_member, update_member, remove_member | 8 |

**Notable behaviors:**
- Write tools confirm before mutating; destructive admin actions double-confirm
- Optimistic locking via `lockVersion` prevents concurrent-edit conflicts
- Relations use validation guards (reject self, duplicate, direct 2-node cycles)
- POST (create) ops are not retried on transient errors to prevent duplicates
- Tool results are trimmed JSON + `url` for direct access

### Non-Functional Requirements

- **Dependency-Light:** Only `mcp` and `httpx`, declared inline via PEP 723, run via `uv run --script`
- **Resilient:** Single HTTP client with retry on 429/5xx (except POST), clear auth failure messages
- **No secrets in repo:** Credentials read from environment, never committed
- **Low latency:** Shared connection, single module per area, <230 LOC per file (target <200)
- **Secure:** Basic Auth (username "apikey"), permission checks (403 errors caught), no key logging
- **Testable:** Pure helpers tested; CI validates syntax, format, tests, JSON configs

## Success Criteria

1. All 44 tools callable via Claude (Claude Code, Desktop, Cowork)
2. Tools work against any self-hosted OpenProject instance (API v3)
3. No credentials leaked in logs, output, or committed files
4. Retry logic prevents duplicate creates; concurrent edits detected via lockVersion
5. Write operations are safe (confirm-first, double-confirm destructive)
6. Response time <3s for typical queries (list, get, report)
7. Test coverage for pure helpers (formatters, validators) ≥80%
8. CI passes on every push (lint, format, syntax, JSON, tests)

## Architecture Overview

```
Claude Client
    ↓ (MCP protocol over stdio)
FastMCP Server (server.py)
    ├── config.py (env vars, logging)
    ├── app.py (shared FastMCP instance)
    ├── op_client.py (HTTP client, retry, auth)
    ├── formatters.py (JSON trimming, helpers)
    ├── validators.py (relation guards)
    ├── tools_*.py (9 modules, 44 tools registered)
    └── logs → stderr (stdout reserved for MCP protocol)
    ↓ (HTTP Basic Auth)
OpenProject REST API v3
```

**Key design principles:**
- Single-file-server ethos: no virtualenv, PEP 723 metadata
- Module split for maintainability: each <230 LOC
- Tool registration via `@mcp.tool()` side effects
- Shared client instance for connection reuse
- Vietnamese docstrings (project convention; Claude reads them to learn tool usage)

## Technical Constraints

- **Python 3.10+** (per PEP 723)
- **OpenProject API v3** (REST, JSON, HAL links)
- **HTTP Basic Auth:** username "apikey", password = token
- **Stdio transport:** stdout for protocol, stderr for logs
- **Dependency freeze:** mcp ≥1.2.0, httpx ≥0.27; no vendored code
- **Idempotency:** GET/PATCH/DELETE retry on 429/5xx; POST never retry
- **Permissions:** Tools fail gracefully with 403 Forbidden (insufficient role)

## Acceptance Criteria

- [ ] Server starts, connects to OpenProject, runs all 44 tools
- [ ] `whoami` identifies user; token validation on 401
- [ ] Write tools confirm before action; destructive actions double-confirm
- [ ] Concurrent edits rejected (optimistic locking via lockVersion)
- [ ] Relation creation guards against self-relation, duplicate, cycles
- [ ] No API keys in stdout, logs, or committed files
- [ ] CI passes: lint, format, syntax, JSON validation, unit tests
- [ ] README covers install (Claude Code, Desktop), env setup, usage examples
- [ ] Skill routes by persona and provides per-role guidance
- [ ] Response times <3s for typical queries (observed over 10 runs)

## Version History

- **v0.4.0** (2026-06-07): Added news CRUD tools (list, get, create, update, delete)
- **v0.3.1** (2026-06-07): Relation/hierarchy hardening (idempotent POST, validation guards, re-parenting)
- **v0.3.0** (2026-06-07): Persona-aware skill + coder/manager/reporting tools + admin panel
- **v0.2.1** (2026-06-07): Secrets-out (env vars only), added CI/community files
- **v0.2.0** (2026-06-07): Modularized server, retry + clear errors, logging
- **v0.1.0** (2026-06-07): Initial MCP server with 16 tools

## Open Questions

None — all requirements defined.

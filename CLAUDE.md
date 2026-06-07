# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

An **MCP server + Claude Code plugin** that connects Claude to any self-hosted **OpenProject** via its REST API v3. A single, dependency-light Python server (FastMCP, PEP 723 inline deps, run by `uv run --script`) exposing **38 tools** across member / project-manager / coder / admin roles, plus a persona-routing skill.

## Commands

```sh
# Run the server (normally launched by the MCP host, not by hand)
uv run --script server/server.py

# Lint & format (run before every commit)
uvx ruff check server/
uvx ruff format server/

# Syntax check
python3 -m py_compile server/*.py

# Tests (pure helpers only — no network, no mcp host)
uv run --with pytest pytest -q tests/

# Verify tool registration (expect 38)
cd server && OPENPROJECT_URL="" OPENPROJECT_API_KEY="" \
  uv run --with mcp --with httpx python3 -c \
  "import app, tools_admin, tools_coder, tools_news, tools_projects, tools_reports, tools_time, tools_work_packages, asyncio; print(len(asyncio.run(app.mcp.list_tools())))"
```

## Architecture

- Communicates over **stdio**; all logging goes to **stderr** (stdout is reserved for the MCP protocol).
- Auth: HTTP Basic, username `apikey`, password = API token (handled in `op_client.py`).
- `server/server.py` imports each `tools_*.py` module for its `@mcp.tool()` registration side-effect onto the shared `app.mcp` instance.
- Tools return **trimmed JSON** (only useful fields + a `url`), shaped by `formatters.py`.
- `op_client._req` retries once on `429`/`5xx` **except POST** (POST is non-idempotent — retrying risks duplicate creates).
- Writes use optimistic locking: fetch `lockVersion` via `get_work_package` before `update_work_package`.

Module map and the full 38-tool inventory live in `docs/codebase-summary.md`; request flow and auth/idempotency design in `docs/system-architecture.md`.

## Conventions

- **Single-file-server ethos:** keep dependencies to `mcp` + `httpx` only, declared via PEP 723 inline metadata in `server/server.py`. Do not introduce a virtualenv or extra runtime deps.
- **File size:** keep each module under ~200 LOC; split by concern (a new tool area → a new `tools_<area>.py`).
- **Naming:** Python `snake_case`; descriptive module names.
- **Tool docstrings and code comments are written in Vietnamese** — this is intentional. Claude reads tool docstrings to learn how to call each tool, so document **every** parameter. Match the existing style when adding tools.
- **Tool design:** clear verb names, documented params, trimmed JSON result including a `url` for direct access.

## Adding a tool

1. Add the `@mcp.tool()` function to the relevant `server/tools_<area>.py` (or a new module).
2. If new, import the module in `server/server.py` so it registers.
3. Reuse `op_client._req` / `_collection` and `formatters` helpers; pre-validate writes (see `validators.py`) before hitting the API.
4. Update the persona skill: add the tool to `skills/openproject-manager/references/<role>.md`.
5. Update the tool count in `README.md`, `docs/codebase-summary.md`, and the verify command above.

## Versioning (SemVer)

Bump in **all** of these together, then add a `CHANGELOG.md` entry:
`server/server.py` (`__version__`) · `.claude-plugin/plugin.json` · `.claude-plugin/marketplace.json` · `README.md` (version badge).
Before committing, confirm no stale version: `git grep -n "<old-version>" -- . ':(exclude)plans/*' ':(exclude)CHANGELOG.md'`.

## Security

- **No secrets in the repo.** Credentials come from the environment (`OPENPROJECT_URL`, `OPENPROJECT_API_KEY`); `.mcp.json` only declares how to run. Never commit tokens or `.env` files.
- Keys must never be printed to logs or tool output.

## Pre-PR checklist

`ruff check` + `ruff format --check` clean · `py_compile` clean · `pytest` green · tool count correct · version consistent across the 4 spots + CHANGELOG · no secrets.

## Documentation

`./docs` is the source of truth — keep it current when behavior changes:

- `docs/project-overview-pdr.md` — purpose, requirements, scope
- `docs/codebase-summary.md` — module map + tool inventory
- `docs/code-standards.md` — conventions and commands
- `docs/system-architecture.md` — request flow, auth, idempotency
- `docs/deployment-guide.md` — install, config, troubleshooting
- `docs/project-roadmap.md` — shipped vs planned

Plans live in `plans/`, reports in `plans/reports/`. Do not commit `plans/` with feature changes.

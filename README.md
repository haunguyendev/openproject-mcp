# OpenProject MCP

> Manage your self-hosted **OpenProject** with AI — view, create and update work packages, assign people, log time, and get progress reports, all from natural language.

[![CI](https://github.com/haunguyendev/openproject-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/haunguyendev/openproject-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP server](https://img.shields.io/badge/MCP-server-purple.svg)](https://modelcontextprotocol.io/)
![Version](https://img.shields.io/badge/version-0.3.1-green.svg)

An [MCP](https://modelcontextprotocol.io/) server + plugin that connects Claude (Claude Code, Claude Desktop, Cowork) to any self-hosted OpenProject instance via its [REST API v3](https://www.openproject.org/docs/api/). Ask Claude things like *"what's overdue in project Website?"* or *"create a task and assign it to Nam, due Friday"* and it calls the right API for you.

## Table of Contents

- [Quick Setup with an AI Agent](#quick-setup-with-an-ai-agent)
- [Features](#features)
- [Tools](#tools)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
  - [1. Get an API token](#1-get-an-api-token)
  - [2. Install for Claude Code](#2-install-for-claude-code)
  - [3. Install for Claude Desktop](#3-install-for-claude-desktop)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Quick Setup with an AI Agent

Already in Claude Code (or any MCP-capable agent)? Skip the manual steps — **copy the prompt below**, paste it to your agent, and it will install and configure everything for you:

```text
Install the OpenProject MCP plugin for me. Read the setup guide at
https://raw.githubusercontent.com/haunguyendev/openproject-mcp/master/README.md
then ask me for my OpenProject URL and API token, set the OPENPROJECT_URL and
OPENPROJECT_API_KEY environment variables, install the plugin, and verify the
connection by calling the whoami tool.
```

The agent fetches the instructions from that link, asks you for your OpenProject URL and API token (the only things it needs from you), runs the install commands, and confirms the connection works. Prefer to do it by hand? Follow the [Quick Start](#quick-start) below.

## Features

- **33 tools across 4 roles** — member, project manager, coder, and admin — covering work packages, projects, members, versions, relations, time tracking, reports, and administration.
- **Works anywhere Claude runs** — Claude Code (plugin/marketplace), Claude Desktop, and Cowork.
- **Any OpenProject** — point it at your own instance with two environment variables.
- **Safe writes** — the bundled skill confirms before creating/updating anything and uses optimistic locking (`lockVersion`) to avoid clobbering concurrent edits.
- **Resilient** — shared HTTP connection, one automatic retry on `429`/`5xx` (honoring `Retry-After`), and clear messages on auth failure.
- **No secrets in the repo** — credentials are read from your environment, never committed.

## Tools

The bundled skill routes these by role (member / project manager / coder / admin).

| Area | Tools |
|---|---|
| Work packages | `list_work_packages` (filter by project/status/assignee/type/version/due), `get_work_package`, `create_work_package` (subtask via `parent_id`), `update_work_package`, `add_comment` |
| Projects & metadata | `list_projects`, `list_project_members`, `list_versions`, `list_types`, `list_statuses`, `list_priorities`, `whoami` |
| Coder | `list_children`, `get_relations`, `create_relation` |
| Time tracking | `log_time`, `list_time_entries`, `my_time_summary` |
| Reports | `report_overdue`, `report_my_tasks`, `report_project_progress`, `report_workload`, `report_status_board`, `report_time`, `report_portfolio` |
| Admin | `list_users`, `get_user`, `list_roles`, `create_project`, `update_project`, `add_member`, `update_member`, `remove_member` |

Write tools always require confirmation in the skill; destructive admin actions (archive project, remove member) double-confirm.

## Requirements

- **[`uv`](https://docs.astral.sh/uv/)** — runs the server and auto-installs its dependencies (`mcp`, `httpx`) from the inline [PEP 723](https://peps.python.org/pep-0723/) metadata. No manual `pip install` needed.

  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- An **OpenProject instance** (self-hosted or cloud) and a personal **API token**.

## Quick Start

### 1. Get an API token

In OpenProject: **avatar → My account → Access tokens → API → Generate**. Copy the token.

### 2. Install for Claude Code

**Try it without installing:**

```sh
claude --plugin-dir /path/to/openproject-mcp
```

**Install from the marketplace (recommended for teams)** — this repo is also a plugin marketplace:

```
/plugin marketplace add haunguyendev/openproject-mcp
/plugin install openproject-mcp@promete-plugins
```

The plugin reads your credentials from the environment, so provide them with **either** of these options:

**Option A — export in your shell** (e.g. in `~/.zshrc` or `~/.bashrc`):

```sh
export OPENPROJECT_URL="https://your-openproject.example.com"
export OPENPROJECT_API_KEY="your-api-token"
```

Open a new terminal (or `source ~/.zshrc`) so the variables are in scope before you launch `claude`.

**Option B — Claude Code settings** (keeps your global shell clean). Add an `env` block to `~/.claude/settings.local.json` — the `.local.json` file is git-ignored, so it's the safe place for secrets:

```json
{
  "env": {
    "OPENPROJECT_URL": "https://your-openproject.example.com",
    "OPENPROJECT_API_KEY": "your-api-token"
  }
}
```

Claude Code applies these to the session and passes them down to the MCP server. Avoid putting the API key in a project-level `.claude/settings.json`, which can be committed by mistake.

Then run `claude`. Verify with `/mcp` — the `openproject` server should show **connected** — then ask *"Who am I on OpenProject?"*. The first start is a little slow while `uv` downloads dependencies.

### 3. Install for Claude Desktop

Desktop apps don't inherit your shell environment, so set the values inline. Open **Settings → Developer → Edit Config** and add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "--script", "/absolute/path/to/openproject-mcp/server/server.py"],
      "env": {
        "OPENPROJECT_URL": "https://your-openproject.example.com",
        "OPENPROJECT_API_KEY": "your-api-token",
        "OPENPROJECT_TIMEOUT_SECONDS": "30"
      }
    }
  }
}
```

> If `uv` isn't on the app's `PATH`, replace `"command": "uv"` with its absolute path (find it with `which uv`).

Restart the app and ask *"Who am I on OpenProject?"* → Claude calls `whoami`.

## Configuration

| Variable | Description | Required | Default |
|---|---|:---:|---|
| `OPENPROJECT_URL` | Base URL of your OpenProject instance | ✅ | — |
| `OPENPROJECT_API_KEY` | Personal API token | ✅ | — |
| `OPENPROJECT_TIMEOUT_SECONDS` | Per-request timeout | | `30` |

> OpenProject API v3 authenticates with HTTP Basic Auth using username `apikey` and the token as the password — the server handles this for you.

## Usage Examples

- *"What do I need to do today?"* / *"Which of my tasks are due soon?"*
- *"Is anything overdue in the Website project?"*
- *"Create a task 'Fix login bug' in project ABC, assign it to Nam, due Friday."*
- *"Move task #123 to In progress and log 2 hours."*
- *"Give me a progress report for project XYZ."* / *"How many hours did I log this week?"*

## How It Works

- A single Python file (`server/server.py`) built on **FastMCP**, with dependencies declared inline via **PEP 723** and run by `uv run --script` — no virtualenv to manage.
- Communicates over **stdio**; logs go to `stderr` so they never corrupt the MCP protocol stream on `stdout`.
- Each tool maps to OpenProject **API v3** endpoints and returns trimmed JSON with only the useful fields plus a `url` to open the item directly.
- Write tools require the current `lockVersion` (fetched via `get_work_package`) to prevent lost updates.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401 Unauthorized` | Token is wrong or expired — generate a new one (My account → Access tokens → API). |
| `openproject` not in `/mcp` | Ensure `uv` is installed and on `PATH`; for the plugin, confirm `OPENPROJECT_URL`/`OPENPROJECT_API_KEY` are set — either exported in the shell that launched Claude (Option A) or in `~/.claude/settings.local.json` (Option B). |
| Server won't start | Check the `uv` path with `which uv` and update `"command"` accordingly. |
| Slow first run | Normal — `uv` is downloading `mcp` and `httpx`; later runs are fast. |

## Security

- The repo contains **no API keys** — `.mcp.json` only declares how to run the server; credentials come from the environment.
- Keys are never printed to logs or tool output.
- If a key is ever exposed (pasted into a chat, committed by mistake), revoke it immediately at **My account → Access tokens** and generate a new one.
- Verify no secret leaked before pushing: `git grep -iE "api[_-]?key.*[a-f0-9]{40}" $(git rev-list --all)` should return nothing.
- To report a vulnerability, see [SECURITY.md](SECURITY.md).

## Development

```sh
uvx ruff check server/    # lint
uvx ruff format server/   # format
```

Tool-design conventions: clear verb names, docstrings that describe every parameter (Claude reads them to learn how to call the tool), and trimmed JSON results that include a `url` for direct access.

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and conventions, and please follow the [Code of Conduct](CODE_OF_CONDUCT.md). In short:

1. Keep the server a single, dependency-light file (PEP 723 inline metadata).
2. Run `uvx ruff check server/` and `uvx ruff format server/` before opening a PR.
3. Describe the OpenProject API endpoints your change touches.

## License

[MIT](LICENSE) © 2026 haunguyendev

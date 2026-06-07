# Code Standards — openproject-mcp

## File Organization

### Directory Structure
```
server/
├── server.py              # Entry point, version, main()
├── app.py                 # Shared FastMCP instance
├── config.py              # Env vars, logging
├── op_client.py           # HTTP client, auth, retry, pagination
├── formatters.py          # JSON trimming, time conversion
├── validators.py          # Relation guards
├── tools_work_packages.py # WP CRUD + comments
├── tools_projects.py      # Projects, members, metadata
├── tools_coder.py         # Hierarchy, relations
├── tools_time.py          # Time tracking
├── tools_reports.py       # 7 report tools
├── tools_news.py          # News CRUD
└── tools_admin.py         # Users, roles, admin actions

tests/
├── test_formatters.py     # Unit tests for formatters
└── test_validators.py     # Unit tests for validators

skills/openproject-manager/
├── SKILL.md               # Router, persona routing logic
└── references/
    ├── member.md
    ├── project-manager.md
    ├── coder.md
    ├── admin.md
    └── reporting.md
```

### File Naming Conventions

- **Python files:** `snake_case` with purpose-driven names
  - ✅ `tools_work_packages.py` (clear: work package tools)
  - ✅ `op_client.py` (clear: OpenProject client)
  - ❌ `wp.py` (unclear abbreviation)

- **Markdown files:** `kebab-case` for docs, descriptive names
  - ✅ `code-standards.md` (clear purpose)
  - ✅ `system-architecture.md` (self-documenting)

### File Size Limits

- **Target:** <200 LOC per file
- **Hard limit:** <230 LOC per file
- **Rationale:** Optimal LLM context window, easier navigation, single responsibility

**Current status:**
- All files under 230 LOC
- Average: ~105 LOC (1,361 total / 13 files)
- Largest: `tools_reports.py` (226 LOC) — near limit but justified by 7 report tools

## Naming Conventions

### Python Naming

| Entity | Style | Example |
|--------|-------|---------|
| Module | snake_case | `tools_work_packages.py` |
| Class | PascalCase | `HTTPError` (not used; keep minimal) |
| Function | snake_case | `list_work_packages`, `_fmt_wp` |
| Constant | UPPER_SNAKE_CASE | `API_KEY`, `BASE_URL` |
| Private | Leading underscore | `_req()`, `_collection()`, `_fmt_wp()` |

### MCP Tool Naming

All tools are public functions with `@mcp.tool()` decorator. Naming:
- **Verb-first:** `create_`, `list_`, `get_`, `update_`, `delete_`, `log_`, `report_`
- **Clear English:** No abbreviations (❌ `mk_`, ✅ `create_`)
- **Singular/plural:**
  - Singular: `get_work_package`, `get_user`, `get_news`
  - Plural: `list_work_packages`, `list_users`, `list_news`
- **Compound:** `create_relation`, `add_comment`, `add_member`, `remove_member`

**All 41 tools:**
- `list_work_packages`, `get_work_package`, `create_work_package`, `update_work_package`, `add_comment`, `list_activities`
- `list_projects`, `list_project_members`, `list_versions`, `list_types`, `list_statuses`, `list_priorities`, `whoami`
- `list_children`, `get_relations`, `create_relation`
- `log_time`, `list_time_entries`, `my_time_summary`
- `report_overdue`, `report_my_tasks`, `report_project_progress`, `report_workload`, `report_status_board`, `report_time`, `report_portfolio`
- `list_news`, `get_news`, `create_news`, `update_news`, `delete_news`
- `list_notifications`, `mark_notification_read`
- `list_users`, `get_user`, `list_roles`, `create_project`, `update_project`, `add_member`, `update_member`, `remove_member`

## Docstring Standard

**Language:** Vietnamese (project convention)  
**Scope:** Every parameter and return value must be documented

### Format

```python
@mcp.tool()
def create_work_package(
    project_id: int,
    subject: str,
    type_id: int = None,
    parent_id: int = None,
    status_id: int = None,
) -> dict:
    """Tạo một work package mới.
    
    project_id (int): ID của dự án chứa task này.
    subject (str): Tiêu đề task.
    type_id (int, optional): ID loại task (Task, Bug, Feature, ...). Mặc định từ dự án.
    parent_id (int, optional): ID task cha (tạo subtask).
    status_id (int, optional): ID trạng thái ban đầu.
    
    Returns: dict chứa ID, subject, status, project, url của task mới được tạo.
    """
```

### Rationale

Claude reads tool docstrings to understand:
- Parameter meaning
- Optional vs required
- Expected types
- Return shape

Clear docstrings = better tool usage by AI.

## Parameter & Return Value Conventions

### Input Parameters

1. **Always explicit:** No magic defaults
   ```python
   # ✅ Good: clear what's required
   def create_work_package(project_id: int, subject: str, ...) -> dict:
   
   # ❌ Bad: magic number
   def create_work_package(project_id: int = 1, subject: str = "") -> dict:
   ```

2. **Type hints:** Use for clarity (Claude reads them)
   ```python
   # ✅ Good
   def list_work_packages(
       project_id: int = None,
       status_id: int = None,
       limit: int = 100,
   ) -> dict:
   
   # ❌ Bad: no types
   def list_work_packages(project_id, status_id, limit):
   ```

3. **Optional params:** Use `= None` for optional, document in docstring
   ```python
   def log_time(
       work_package_id: int,
       hours: float,
       spent_on: str = None,  # YYYY-MM-DD, defaults to today
   ) -> dict:
   ```

### Return Values

**Always return trimmed JSON dict with `url` field:**

```python
# ✅ Good: minimal fields + url
return {
    "id": 123,
    "subject": "Fix login bug",
    "status": {"id": 1, "name": "New"},
    "project": {"id": 42, "name": "Website"},
    "url": "https://openproject.example.com/work_packages/123"
}

# ❌ Bad: too much data
return raw_api_response  # 50+ fields

# ❌ Bad: no link
return {"id": 123, "subject": "..."}
```

**For lists, return paginated results:**
```python
{
    "items": [...],
    "total": 42,
    "limit": 20,
    "offset": 0
}
```

## Error Handling

### Clear Error Messages

Use `ValueError`, `RuntimeError` with user-friendly text:

```python
# ✅ Good: actionable message
if response.status_code == 401:
    raise ValueError("OpenProject API key is invalid or expired. "
                     "Generate a new one at: My account → Access tokens → API")

# ✅ Good: context
if response.status_code == 404:
    raise ValueError(f"Work package {work_package_id} not found "
                     f"(api path: /api/v3/work_packages/{work_package_id})")

# ❌ Bad: vague
if not api_key:
    raise RuntimeError("Missing API key")

# ❌ Bad: stack trace
try:
    ...
except Exception as e:
    raise Exception(f"Error: {str(e)}")  # loses context
```

### Permission Checks

OpenProject returns 403 Forbidden for insufficient role. Catch + translate:

```python
if response.status_code == 403:
    raise ValueError("Insufficient permission. "
                     "This action requires 'manage news' role. "
                     "Ask your admin to grant the role.")
```

## Import Organization

```python
# Standard library (alphabetical)
import json
import logging
import os
import sys
from typing import Any, Optional

# Third-party (alphabetical)
import httpx
from mcp.server.fastmcp import FastMCP

# Local
from app import mcp
from config import API_KEY, BASE_URL
from op_client import _req, _collection
from formatters import _fmt_wp
```

## Code Comments

**Rule:** Explain "why," not "what." Code is self-documenting.

```python
# ✅ Good: explains decision
# Retry GET/PATCH/DELETE on transient failure, but NOT POST.
# POST is write-once; retrying risks duplicate creates (task, relation, entry).
# Client must handle 429/5xx for writes via skill confirmation.
if method != "POST" and should_retry:
    # retry logic

# ❌ Bad: obvious from code
# Loop through users
for user in users:
    # Process user
    process(user)
```

## Tools Module Structure

Each `tools_*.py` follows this pattern:

```python
"""Tính năng: [describe area in Vietnamese].

Liệt kê tất cả các tool được đăng ký dưới đây.
"""

from app import mcp
from op_client import _req, _collection
from formatters import _fmt_wp
from validators import validate_relation


@mcp.tool()
def tool_1(...) -> dict:
    """[Docstring in Vietnamese describing tool and all params]"""
    # Implementation
    pass


@mcp.tool()
def tool_2(...) -> dict:
    """[Docstring in Vietnamese describing tool and all params]"""
    # Implementation
    pass
```

**Side effect:** Importing `tools_*.py` in `server.py` registers all tools via `@mcp.tool()`.

## Testing Standards

### Unit Tests (Pure Helpers)

Only test pure functions with no side effects:

```python
# ✅ Good: test formatter
def test_fmt_wp_includes_url():
    api_response = {"id": 1, "subject": "Test", "_links": {"self": {"href": "/api/v3/work_packages/1"}}}
    formatted = _fmt_wp(api_response)
    assert formatted["url"] == "https://openproject.example.com/work_packages/1"
```

### Integration Tests (Manual)

Test tools with live OpenProject instance:
```bash
# Set env vars
export OPENPROJECT_URL="https://..."
export OPENPROJECT_API_KEY="..."

# Start server
uv run --script server/server.py

# Test with MCP client (Claude Code, Desktop, or raw stdio)
```

### Run Tests

```bash
# Lint
uvx ruff check server/

# Format check
uvx ruff format --check server/

# Syntax
python -m py_compile server/*.py

# Unit tests
uv run --with pytest pytest -q tests/
```

## Versioning & Release Checklist

Before releasing a new version:

1. **Update version in 4 places:**
   - `server/server.py` — `__version__ = "X.Y.Z"`
   - `.claude-plugin/plugin.json` — `"version": "X.Y.Z"`
   - `.claude-plugin/marketplace.json` — `"version": "X.Y.Z"`
   - `README.md` — Version badge (if applicable)

2. **Update CHANGELOG.md:**
   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD

   ### Added
   - Feature description

   ### Fixed
   - Bug fix description

   ### Changed
   - API/behavior change
   ```

3. **Commit + tag:**
   ```bash
   git add server/server.py .claude-plugin/ CHANGELOG.md README.md
   git commit -m "chore: release v0.4.0"
   git tag v0.4.0
   git push origin master --tags
   ```

4. **CI validates** (all checks must pass):
   - Lint + format
   - Syntax check
   - JSON validation
   - Unit tests

## Security Standards

1. **No secrets in code**
   - Never hardcode API keys, URLs (except examples in README)
   - All credentials from environment
   - Verify: `git grep -iE "api[_-]?key.*[a-f0-9]{40}"`

2. **No key logging**
   - `config.py` logs: "`api_key_set=True/False`", never the actual key
   - Audit all `log.info`, `print`, `return` statements with credentials

3. **Basic Auth header**
   - Username: `"apikey"` (hardcoded constant)
   - Password: `API_KEY` from env
   - Sent only over HTTPS (OpenProject enforces)

4. **Optimistic locking**
   - All PATCH writes require current `lockVersion`
   - Prevent lost updates in concurrent scenarios
   - `update_work_package(id, lock_version, ...)` signature

5. **Permission-aware**
   - Tools fail gracefully with 403 Forbidden
   - Do NOT strip 403; let user see "Insufficient permission"
   - Guides like "Ask admin to grant 'manage news' role"

## Convention Summary Table

| Aspect | Standard | Example |
|--------|----------|---------|
| File size | <230 LOC | Current: 1,361 / 13 = ~105 avg |
| Tool naming | verb-first, lowercase | `create_work_package` |
| Docstrings | Vietnamese, all params | See `tools_*.py` |
| Return JSON | Trimmed + `url` | `{"id": 123, "url": "...", ...}` |
| Error messages | Clear, actionable | `"API key invalid. Generate new one at: ..."` |
| Comments | Explain "why" | `# Retry GET/PATCH/DELETE, not POST (write-once)` |
| Imports | Organized by source | stdlib → third-party → local |
| Version bumps | 4 places | server.py, plugin.json×2, README |
| Testing | Pure helpers only | formatters, validators |
| Security | Env vars, no logging keys | `api_key_set=bool`, not the key |

## Linting & Formatting

**Formatter:** `ruff format`
```bash
uvx ruff format server/
```

**Linter:** `ruff check`
```bash
uvx ruff check server/
```

**Pre-commit:**
```bash
uvx ruff check server/ && uvx ruff format server/ && python -m py_compile server/*.py
```

Configuration in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
```

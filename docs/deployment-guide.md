# Deployment Guide — openproject-mcp

## Overview

openproject-mcp is a lightweight MCP server with no persistent state, no database, and no background processes. It runs on-demand via `uv run --script` and communicates over stdio.

**Installation paths:**
1. Claude Code (plugin, dev mode)
2. Claude Code (marketplace)
3. Claude Desktop (config file)
4. Claude Cowork (MCP server)

Each path reads credentials from environment; no hardcoded secrets.

## Prerequisites

- **`uv`** — installed and on `PATH`
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  Verify: `uv --version`

- **OpenProject instance** — self-hosted or cloud, API v3 enabled
  ```bash
  # Test connectivity
  curl -H "Authorization: Basic $(echo -n 'apikey:YOUR_TOKEN' | base64)" \
    https://your-openproject.example.com/api/v3/users/me
  ```

- **Personal API token** — from OpenProject
  - Log in to OpenProject
  - Avatar → My account → Access tokens → API → Generate
  - Copy token (40 hex characters)

## Installation Paths

### Path 1: Claude Code (Development Mode)

**Fastest for testing:**

```bash
# Clone or download openproject-mcp
git clone https://github.com/haunguyendev/openproject-mcp.git
cd openproject-mcp

# Set credentials in shell
export OPENPROJECT_URL="https://your-openproject.example.com"
export OPENPROJECT_API_KEY="your-40-char-token"

# Start Claude Code with the plugin
claude --plugin-dir $(pwd)
```

**Result:** The `openproject` server appears in `/mcp` list (connected).

**Verify:**
```
/mcp
# Output: openproject (connected)

/ask "Who am I on OpenProject?"
# Claude calls whoami tool, returns your name + roles
```

**Pros:**
- Instant iteration (no restart needed)
- Easy to edit code and test
- Full stderr logs visible in console

**Cons:**
- Plugin directory must be kept local
- Credentials in shell (export statement)

---

### Path 2: Claude Code (Marketplace Install)

**Recommended for teams:**

#### Step 1: Add Marketplace

```
/plugin marketplace add haunguyendev/openproject-mcp
```

#### Step 2: Install Plugin

```
/plugin install openproject-mcp@promete-plugins
```

#### Step 3: Set Credentials

**Option A — Shell export (global, all sessions):**

Edit `~/.zshrc` (or `~/.bashrc`):
```bash
export OPENPROJECT_URL="https://your-openproject.example.com"
export OPENPROJECT_API_KEY="your-40-char-token"
```

Reload: `source ~/.zshrc` (or open new terminal)

**Option B — Claude Code settings (project-safe):**

Edit `~/.claude/settings.local.json` (git-ignored):
```json
{
  "env": {
    "OPENPROJECT_URL": "https://your-openproject.example.com",
    "OPENPROJECT_API_KEY": "your-40-char-token"
  }
}
```

Claude Code applies these to every session.

#### Step 4: Verify

```
claude
/mcp
# Output: openproject (connected)

/ask "Who am I on OpenProject?"
```

**Pros:**
- Plugin auto-updates from marketplace
- Credentials in settings.local.json (git-ignored)
- Clean shell environment

**Cons:**
- Marketplace dependency
- Slower first startup (downloads dependencies)

---

### Path 3: Claude Desktop

**For macOS / Windows users:**

#### Step 1: Get Absolute Path

```bash
echo $(realpath ~/path/to/openproject-mcp/server/server.py)
# Output: /Users/username/openproject-mcp/server/server.py
```

#### Step 2: Open Desktop Config

- **macOS:** Settings → Developer → Edit Config
- **Windows:** Settings → Developer → Edit Config
- Opens `claude_desktop_config.json`

#### Step 3: Add MCP Server Entry

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "--script", "/absolute/path/to/openproject-mcp/server/server.py"],
      "env": {
        "OPENPROJECT_URL": "https://your-openproject.example.com",
        "OPENPROJECT_API_KEY": "your-40-char-token",
        "OPENPROJECT_TIMEOUT_SECONDS": "30"
      }
    }
  }
}
```

**Key points:**
- `command`: Must be `"uv"` (or full path to `uv` if not on `PATH`)
- `args`: Always `["run", "--script", "/absolute/path/..."]`
- `env`: Credentials inline (Desktop doesn't inherit shell env)
- Don't commit this file; it contains secrets

#### Step 4: Find `uv` Path (if needed)

If `uv` isn't on Desktop's `PATH`:

```bash
which uv
# Output: /Users/username/.cargo/bin/uv

# Use in config:
"command": "/Users/username/.cargo/bin/uv"
```

#### Step 5: Restart Desktop

Close and reopen Claude Desktop. The MCP server starts automatically.

**Verify:**
- Check "Developer" panel for MCP server status
- Ask: "Who am I on OpenProject?"

**Pros:**
- No terminal needed
- Credentials in Desktop (never in shell)
- Works offline-first (caches results)

**Cons:**
- Absolute paths (not portable across machines)
- No stderr logs visible (check Desktop dev console)
- Harder to restart server

---

### Path 4: Claude Cowork

**For shared team deployments:**

Cowork supports MCP servers via configuration. Contact your workspace admin to:

1. Add MCP server entry in Cowork's configuration
2. Set `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` as workspace environment variables
3. Restart Cowork service

For details, see Cowork's MCP documentation.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `OPENPROJECT_URL` | ✅ | — | `https://openproject.example.com` |
| `OPENPROJECT_API_KEY` | ✅ | — | `abcdef0123456789abcdef0123456789abcd1234` |
| `OPENPROJECT_TIMEOUT_SECONDS` | ❌ | `30` | `60` |

**Notes:**
- URLs must be HTTPS in production
- API key is 40 hex characters (from My account → Access tokens)
- Timeout applies per HTTP request; increase for slow networks

### Verifying Setup

```bash
# 1. Check uv is installed
uv --version

# 2. Check credentials are set
echo $OPENPROJECT_URL
echo $OPENPROJECT_API_KEY

# 3. Test API connectivity
curl -H "Authorization: Basic $(echo -n 'apikey:'"$OPENPROJECT_API_KEY" | base64)" \
  "$OPENPROJECT_URL/api/v3/users/me"
# Should return JSON with your user info

# 4. Start Claude Code / Desktop
# 5. Run /ask "Who am I on OpenProject?"
```

If step 3 fails with:
- **401 Unauthorized** — API key is wrong or expired
- **404 Not Found** — URL is incorrect
- **Connection refused** — OpenProject instance is down

---

## Troubleshooting

### MCP Server Not Appearing in `/mcp`

**Symptom:** `openproject` not listed

**Causes & fixes:**

| Cause | Fix |
|-------|-----|
| `uv` not on PATH | `which uv`; use full path in config |
| Env vars not set | Export in shell or add to Claude settings |
| Plugin dir path wrong | Use absolute path; avoid symlinks |
| Claude not restarted | Restart Claude Code / Desktop |

**Debug:**
```bash
# Check uv can run the server
uv run --script ~/openproject-mcp/server/server.py
# Should log: "openproject-mcp v0.4.0 — base_url=https://..., api_key_set=True"
# Press Ctrl+C to exit
```

---

### API Key Errors

**Symptom:** `401 Unauthorized`

**Fixes:**
1. Generate new token at: OpenProject → My account → Access tokens → API → Generate
2. Copy full 40-character token (no spaces, no quotes in shell)
3. Verify: `echo $OPENPROJECT_API_KEY` shows the full token
4. Restart Claude

**If you pasted the key in chat:** Revoke it immediately at My account → Access tokens; generate new one.

---

### Slow First Run

**Symptom:** 10+ seconds to start

**Cause:** `uv` downloading dependencies (`mcp`, `httpx`) on first run

**Fix:** Wait; subsequent runs are <1 second. To pre-warm:
```bash
uv run --script server/server.py
# Wait for "openproject-mcp v0.4.0..." log
# Ctrl+C
# Next run is fast
```

---

### Connection Timeout

**Symptom:** Requests hang, then fail with timeout

**Causes & fixes:**

| Cause | Fix |
|-------|-----|
| OpenProject is down | Check https://your-openproject.example.com in browser |
| Network is slow | Increase OPENPROJECT_TIMEOUT_SECONDS to 60 |
| Firewall blocks connection | Check network policy; allow `your-openproject.example.com:443` |

---

### Token Leaked in Logs

**Symptom:** API key appears in stderr or tool output

**This should NOT happen.** Report immediately:
1. Check log carefully (key should be replaced with `***`)
2. If key is exposed, revoke at My account → Access tokens
3. Report bug: GitHub issue with `[SECURITY]` tag (don't include key)

---

## Upgrading

### To a New Version

```bash
# If using git clone:
cd ~/openproject-mcp
git pull origin master
# Restart Claude Code / Desktop

# If using marketplace:
/plugin update openproject-mcp
# Restart Claude Code
```

### Breaking Changes

Check `CHANGELOG.md` before upgrading:
- v0.3.0 changed parameter names (e.g., `typeId` → `type_id`)
- v0.4.0 added news tools
- See CHANGELOG for migration guides

---

## Security Checklist

Before deploying to production:

- [ ] API key is **environment variable only** (not in config file, not in code)
- [ ] `OPENPROJECT_URL` uses **HTTPS** (not HTTP)
- [ ] Claude Desktop config file **is not committed** to git
- [ ] Shell env vars are **only in personal `~/.zshrc`**, not in project `.env`
- [ ] No API keys in chat history (if shared)
- [ ] Token **will be revoked** if ever exposed
- [ ] Audit permissions: user has role for operations intended

---

## Performance Tuning

### Typical Response Times

| Operation | Latency | Notes |
|-----------|---------|-------|
| `whoami` | <100ms | Simple API call |
| `list_work_packages` (100 items) | 200-500ms | Paginated |
| `get_work_package` | 100-200ms | Direct fetch |
| `create_work_package` | 300-800ms | API processing |
| `report_overdue` | 1-3s | Aggregates multiple calls |
| `report_portfolio` | 2-5s | Complex calculation |

**Tuning:**
- Increase `OPENPROJECT_TIMEOUT_SECONDS` if network is slow
- Use filters in `list_work_packages` to reduce data transfer
- Cache OpenProject metadata (types, statuses) if making many queries

---

## Backup & Recovery

**OpenProject MCP has no persistent state.** It reads/writes entirely through OpenProject API.

**No backup needed:** The server is stateless. Your data lives in OpenProject.

**Disaster recovery:** If the server fails:
1. Stop Claude
2. Delete `~/.claude/plugins/openproject` (if cached)
3. Reinstall via marketplace or git
4. Restart Claude
5. Everything works (data is in OpenProject)

---

## Monitoring & Logging

### Logs Location

| Client | Logs |
|--------|------|
| Claude Code | Console tab (visible in dev tools) |
| Claude Desktop | `~/Library/Logs/Claude Desktop/` (macOS) or similar (Windows) |
| Cowork | Workspace admin panel |

### Log Format

```
2026-06-07 15:30:45,123 INFO openproject-mcp: openproject-mcp v0.4.0 — base_url=https://..., api_key_set=True
2026-06-07 15:30:46,234 INFO openproject-mcp: GET /api/v3/work_packages/123 → 200
2026-06-07 15:30:47,345 INFO openproject-mcp: POST /api/v3/work_packages → 201
```

**Key fields:**
- Timestamp
- Level (INFO, WARNING, ERROR)
- Method + path (no secrets)
- Status code
- No API key, no auth header, no user data

---

## Support & Issues

- **Bug report:** GitHub Issues with `[BUG]` tag
- **Security issue:** Email maintainer (see SECURITY.md)
- **Feature request:** GitHub Discussions or Issues with `[FEATURE]`
- **Setup help:** GitHub Discussions or CONTRIBUTING.md

Include:
- `uv --version`
- OpenProject version
- Claude Code/Desktop version
- Error message (full, with context)
- Steps to reproduce

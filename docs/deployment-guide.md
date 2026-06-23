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

## Remote (Multi-User) Deployment

**For teams using Claude.ai web custom connectors with per-user OAuth authentication.**

This is a production deployment mode, distinct from the single-user paths above. Use this if you want:
- Multiple team members accessing the same OpenProject instance via Claude.ai web
- Each user authenticates to OpenProject independently (no shared API token)
- Admin safety: dangerous tools (delete, bulk ops) hidden by default

### Prerequisites

- **OpenProject instance** (self-hosted or cloud) with OAuth 2.0 support (standard)
- **OpenProject OAuth application** (client_id + client_secret)
  - Redirect URI: `https://claude.ai/api/mcp/auth_callback` (exact)
  - Scope: `api_v3`
- **Container runtime** (Docker, Kubernetes, etc.)
- **Reverse proxy** with HTTPS (Caddy, nginx, etc.)
- **Public HTTPS domain** for the MCP (e.g., `openproject-mcp.example.com`)

### Step 1: Create OpenProject OAuth Application

In OpenProject (admin):

1. Go to **Administration → OAuth applications → Create**
2. Enter:
   - Name: "Claude MCP" (or your choice)
   - **Redirect URI:** `https://claude.ai/api/mcp/auth_callback` (MUST be exact)
   - Scopes: Check `api_v3`
3. Save; note the **client_id** and **client_secret**

**Important:** The redirect URI is Claude's, not your MCP domain. OpenProject will send the auth code back to Claude, which forwards it to your MCP.

### Step 2: Deploy the MCP Container

Use the provided `Dockerfile`:

```bash
cd openproject-mcp
docker build -t openproject-mcp:0.8.0 .
docker run -d \
  --name openproject-mcp \
  -p 127.0.0.1:8000:8000 \
  -e MCP_TRANSPORT=http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e OPENPROJECT_URL=https://your-openproject.example.com \
  -e MCP_PUBLIC_URL=https://openproject-mcp.example.com \
  -e ALLOWED_HOSTS=openproject-mcp.example.com \
  -e ALLOWED_ORIGINS=openproject-mcp.example.com \
  openproject-mcp:0.8.0
```

Or use the provided `docker-compose.yml`:

```yaml
version: '3.8'
services:
  openproject-mcp:
    build: .
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      MCP_TRANSPORT: http
      MCP_HOST: 0.0.0.0
      MCP_PORT: 8000
      OPENPROJECT_URL: https://your-openproject.example.com
      MCP_PUBLIC_URL: https://openproject-mcp.example.com
      ALLOWED_HOSTS: openproject-mcp.example.com
      ALLOWED_ORIGINS: openproject-mcp.example.com
      # DO NOT set OPENPROJECT_API_KEY (each user authenticates via OAuth)
```

### Step 3: Reverse Proxy (HTTPS)

Deploy behind a reverse proxy to terminate TLS.

**Caddy (simplest; auto-TLS):**

Create `Caddyfile`:

```caddy
openproject-mcp.example.com {
    reverse_proxy 127.0.0.1:8000
    tls user@example.com
}
```

Run:

```bash
docker run -d \
  --name caddy \
  -p 80:80 -p 443:443 \
  -v ./Caddyfile:/etc/caddy/Caddyfile \
  caddy
```

**Nginx (with manual TLS):**

See `deploy/nginx.snippet` in the repo for a sample config.

### Step 4: Configure Claude.ai Web

In Claude.ai (web):

1. **Settings → Integrations → Add Custom MCP**
2. Enter:
   - **Name:** OpenProject
   - **MCP URL:** `https://openproject-mcp.example.com/mcp`
   - **Advanced settings:**
     - Client ID: (from OpenProject OAuth app)
     - Client Secret: (from OpenProject OAuth app)
3. Click **Connect**
4. You'll be redirected to OpenProject to log in
5. Authorize the OAuth application
6. You're now authenticated to use OpenProject MCP in Claude.ai

### Step 5: Test the Connection

Ask Claude: *"Who am I on OpenProject?"*

Claude will call the `whoami` tool. You should see your name and roles.

### Environment Variables Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `MCP_TRANSPORT` | ✅ | stdio | Set to `http` for remote multi-user |
| `OPENPROJECT_URL` | ✅ | — | Your OpenProject instance URL (HTTPS) |
| `MCP_HOST` | ❌ | 127.0.0.1 | Bind address (0.0.0.0 for Docker) |
| `MCP_PORT` | ❌ | 8000 | Bind port |
| `MCP_PUBLIC_URL` | ✅ | http://host:port | Public HTTPS URL of the MCP (for OAuth issuer) |
| `ALLOWED_HOSTS` | ✅ | — | CSV of reverse-proxy domains (DNS-rebinding protection) |
| `ALLOWED_ORIGINS` | ❌ | — | CSV of CORS origins for OAuth callback |
| `OP_MCP_ENABLE_ADMIN_DESTRUCTIVE` | ❌ | false | Set to `true` to show all 44 tools (default: 37 on http) |
| `OPENPROJECT_TIMEOUT_SECONDS` | ❌ | 30 | Per-request timeout |

**Critical:** Do NOT set `OPENPROJECT_API_KEY` in http mode (each user authenticates via OAuth).

### Security & Exposure

- **OAuth + per-request credential isolation:** Each user's Bearer token is validated per request; no shared keys
- **Firewall + rate-limit:** Recommend restricting to Anthropic IP ranges at the proxy (optional defense-in-depth)
- **Admin allowlist:** Dangerous tools (delete, archive project, bulk ops) are hidden by default
  - Non-technical team members can only see 37 safe tools
  - Admins can override with `OP_MCP_ENABLE_ADMIN_DESTRUCTIVE=true`
- **HTTPS only:** All traffic to/from MCP must be HTTPS (enforced by reverse proxy)
- **DNS-rebinding protection:** TransportSecuritySettings validates `Host` header + CORS origins

### Rollback

To roll back to single-user (stdio) mode:

1. Stop the container
2. Revert `MCP_TRANSPORT` to `stdio` (or omit it)
3. Set `OPENPROJECT_URL` + `OPENPROJECT_API_KEY`
4. Restart using single-user deployment path (Claude Code, Desktop, etc.)

No data migration needed; the stdio path is unchanged.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 401 Unauthorized | OAuth token expired or invalid | Re-authenticate via Claude.ai Settings → Integrations |
| Tool count is 37, want 44 | Admin restrictive mode on http | Set `OP_MCP_ENABLE_ADMIN_DESTRUCTIVE=true` (admin only) |
| "DNS rebinding blocked" | Reverse proxy hostname mismatch | Ensure `ALLOWED_HOSTS` matches reverse-proxy domain |
| Claude can't find MCP | URL wrong or proxy not running | Check `MCP_PUBLIC_URL` in Claude settings; verify reverse proxy is up |
| "No credential found" | User not authenticated | OAuth redirect didn't complete; re-authenticate in Claude.ai |

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

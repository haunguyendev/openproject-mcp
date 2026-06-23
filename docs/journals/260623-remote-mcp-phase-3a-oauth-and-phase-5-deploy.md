# Remote MCP Phase 3A (OAuth) + Phase 5 (deploy) — v0.8.0

**Date**: 2026-06-23
**Component**: HTTP transport, OAuth resource server, deploy artifacts
**Status**: Shipped (commits `fe32dee`, `a510973`, `0fa6f41`)
**Branch**: `feature/remote-multiuser-mcp`
**Plan**: `plans/260623-remote-mcp-multiuser-deploy/`

## What Happened

The Phase 1 A/B auth gate closed after a live test: a real OpenProject OAuth flow on
`manage.promete.ai` (via `spike/oauth_precheck.py`) issued an opaque `api_v3` token that
worked on `GET /api/v3/users/me` → **OAuth (Variant A) is feasible**. Research on Claude.ai
custom connectors then collapsed the design: the MCP does **not** need the planned
`oauth.py` proxy (authorize/callback/token). It is a thin OAuth 2.0 **Resource Server** —
it points Claude.ai at OpenProject as the Authorization Server and reuses the per-request
Bearer that Phase 2's `op_client` already reads. Phase 5 then packaged it for deploy.

## What Shipped

**Phase 3A — OAuth resource server (`fe32dee`):**
- `server/oauth_metadata.py` (NEW): pure builders for RFC 9728 protected-resource (`resource`
  = the `/mcp` endpoint) and RFC 8414 authorization-server metadata (issuer = MCP, but
  `authorization_endpoint`/`token_endpoint` = OpenProject's `/oauth/*`, PKCE `S256`, scope
  `api_v3`); `www_authenticate_header` (incl. `scope=api_v3`); `needs_challenge`.
- `server/http_app.py` (NEW): Starlette app — public `/.well-known/oauth-protected-resource`
  (also served at the `/mcp`-suffixed path) + `/.well-known/oauth-authorization-server`,
  and an `OAuthChallenge` ASGI wrapper that returns `401 + WWW-Authenticate` on the MCP mount
  when there is no Bearer and no env key. Mounts `mcp.streamable_http_app()`.
- `server/server.py`: http branch now serves the Starlette app via uvicorn (was
  `mcp.run("streamable-http")`); `config.py` gained `MCP_PUBLIC_URL`.

**Phase 5 — deploy + hardening (`a510973` feat, `0fa6f41` docs):**
- `Dockerfile` (uv python3.12-slim, non-root `mcp`, pre-warmed deps), `docker-compose.yml`
  (binds `127.0.0.1:8000` behind a reverse proxy), `.env.example`, `deploy/caddy.snippet`,
  `deploy/nginx.snippet`, `.gitignore` for `.env`.
- M2: `patch_wp_with_lock` is transport-aware — http surfaces a 409 immediately (no silent
  lost update), stdio keeps the single rollup retry. PEP723 floor → `mcp>=1.8.0`,
  starlette/uvicorn declared. Version → 0.8.0 (4 spots + CHANGELOG); 6 docs + README updated.

## Key Decisions

- **Resource Server, not OAuth proxy.** OpenProject issues directly-usable opaque tokens, so
  the MCP only advertises OpenProject as the AS and validates by *using* the token (no local
  `aud` check, no token storage, no refresh — Claude re-auths on 401). Far less code than the
  plan's `oauth.py`; the user approved the simplification.
- **OpenProject lacks discovery metadata** (`/.well-known/openid-configuration` and
  `/.well-known/oauth-authorization-server` both 404), so the MCP hosts the AS metadata
  pointing at OpenProject's existing `/oauth/*` endpoints (cross-host endpoints are RFC 8414 valid).
- **`resource` = the `/mcp` endpoint** (+ path-suffixed PRM), per review M-1 — the common
  cause of connector rejection is a resource that doesn't match the connector URL.
- **Challenge resolves the Phase-2 M-1**: multi-user (no env key) + no Bearer → 401; env key
  present → single-user fallback, no challenge (stdio/smoke unaffected).
- **M2 transport-aware**: honors both "no silent lost update" (http) and RÀNG BUỘC SỐ 1
  (stdio behavior unchanged) without diffing field-level conflicts.

## Notable

- Four code reviews across the plan (Phase 2/3A/4/5) all APPROVE. The one must-fix was Phase 5
  **H-1**: the Dockerfile left the uv cache root-owned + read-only while running non-root, so
  `uv run --script` died at startup with "Permission denied" (exit 2). Fixed by `chown`-ing
  `/opt/uv-cache` to `mcp` — `uv` writes its cache on every run. (Repo lesson: any uv-based
  image must give the runtime user a writable cache.)
- `docker build` is blocked by a local dev hook, so the image build/run still needs user
  verification; `docker compose config` validated clean.
- **Deploy-pending (not code):** the live Claude.ai handshake (HTTPS only); whether
  OpenProject/Doorkeeper accepts Claude's PKCE + RFC 8707 `resource` param; registering
  redirect URI `https://claude.ai/api/mcp/auth_callback` on the OpenProject OAuth app.
- All 5 phases shipped; stdio path unchanged (44 tools), http = 37; 76 tests green.

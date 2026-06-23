# Remote MCP Phase 1 spike verification + Phase 2 auth foundation (v0.8.0-dev)

**Date**: 2026-06-23 22:40
**Severity**: Medium (architectural gate + credential refactor, 100% backward-compatible)
**Component**: MCP transport, HTTP client, auth system
**Status**: Shipped (uncommitted; Phase 3 pending)
**Branch**: `feature/remote-multiuser-mcp`
**Plan**: `plans/260623-remote-mcp-multiuser-deploy/`

## What Happened

Multi-user HTTP deploy gated on two empirical unknowns: (1) can credentials propagate per-request to sync tools under `stateless_http=True` without threading `ctx` through all 44 tools? (2) will FastMCP / mcp SDK support the required transport + security plumbing? Phase 1 was a throwaway spike to answer both. **Verdict: both PASS.** Phase 2 shipped the per-request credential foundation on that verified approach. No plan reversals; "tools don't change" linchpin holds. 59 tests green (47 old + 12 new).

## Phase 1 Spike (Proof)

Built `spike/` (throwaway): empirically ran 20 interleaved concurrent identities over real HTTP, reading mcp's own `request_ctx` ContextVar inside `op_client` — zero identity leak. Verified mcp ≥1.8.0 has `streamable_http_app()`, `stateless_http` setting, and `TransportSecuritySettings`. Quantified sync-tool concurrency (H1): FastMCP runs sync tools directly on event loop (serialize 5×0.5s=2.59s), but `anyio.to_thread.run_sync` escape hatch proved cheap (0.58s overlapped). **Decision:** keep `op_client` sync (team <10, acceptable latency). Full analysis at `plans/260623-remote-mcp-multiuser-deploy/reports/spike-architecture-and-auth-decision-note.md`.

## Phase 2 Shipped (Code)

**Three modules refactored:**

1. **`server/config.py` (+49 LOC)**: `TransportConfig` dataclass; `resolve_transport(env)` parses `MCP_TRANSPORT` (default `stdio`, opt-in `http`), `MCP_HOST`, `MCP_PORT`, `MCP_STATELESS_HTTP`. Decouples transport config from env-reading — test-friendly, no mcp dependency.

2. **`server/op_client.py` (+120 LOC refactor)**: Rewrote auth. Old: single `httpx.Client` with baked `auth=("apikey", API_KEY)`, shared across all requests. **New:** `Creds` dataclass (base_url + auth tuple OR bearer string), `current_creds()` chain (override→Bearer-from-request→env→AuthError 401), one `httpx.Client(base_url)` per instance (M1: no auth baked — each `_req()` call passes auth via kwargs). SDK's `request_ctx` ContextVar read at `_current_request()`, Bearer header extracted at `_bearer_from_request()`. Stdio (no request) or missing Bearer → fallback `OPENPROJECT_API_KEY` (RÀNG BUỘC SỐ 1 preserved: single-user env flow untouched).

3. **`server/server.py` (+64 LOC)**: `main()` branches on `config.resolve_transport()`: stdio path (`mcp.run()`, unchanged) vs HTTP path (`_run_http()` sets `streamable_http_app(..., stateless_http=True, json_response=True)` and `TransportSecuritySettings(enable_dns_rebinding_protection=True)` — H3). All 44 tools & formatters untouched (H2: `BASE_URL` is global, no per-request override needed).

**Tests:** 12 new (test_op_client_creds.py: Creds chain, override seam; test_transport_select.py: resolve_transport parsing). Smoke: bad Host→421, bad Origin→403, valid Bearer→200, stdio baseline intact.

## Key Decisions

- **Per-request auth in `op_client`, not middleware:** red-team's original middleware+ContextVar didn't work; using mcp's own `request_ctx` (documented at `mcp/server/lowlevel/server.py:109`) bypasses that, zero tool changes required.
- **Sync `op_client` (no `anyio.to_thread.run_sync`):** Phase 1 proved acceptable latency for team size; escape hatch available if needed later.
- **HTTP 401 AuthError for undefined identity:** not "OPENPROJECT_API_KEY unconfigured" — multi-user mode distinguishes missing credentials (401) from misconfiguration (startup error).
- **env fallback (RÀNG BUỘC SỐ 1):** stdio flow and env-only http (smoke test) still work 100%.
- **Defer 401-vs-fallback decision:** Phase 3 gates on choice: always 401 when no Bearer (strict multi-user), or keep env fallback as single-user safeguard? Documented at 260623 decision-note.
- **Defer OAuth A/B:** Phase 3A (Bearer implementation) vs 3B (vault/injected header) still OPEN. Needs live Claude.ai↔OpenProject OAuth handshake test that requires user interaction (user must create OAuth app in OpenProject).

## Notable

- Code review APPROVED 5/5 (no blocking defects; applied two non-behavioral fixes: MCP_PORT int guard + loud warning when http+env-key=single-user fallback).
- All 44 tools remain untouched; backward compat confirmed (stdio smoke test passes).
- M1 decision (one client, auth per-request) lets us scale users without multiplying client instances — fits stateless HTTP design.
- H3 (DNS rebinding protection) applied; H1 quantified + decision documented; H2 (BASE_URL global) confirmed safe for team-scoped instance.

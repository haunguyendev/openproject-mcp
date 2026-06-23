# Remote MCP Phase 4 — transport-aware admin allowlist (v0.8.0-dev)

**Date**: 2026-06-23 22:50
**Severity**: Medium (tool visibility/dispatch filtering, zero API exposure change)
**Component**: MCP tool registry, request dispatch
**Status**: Shipped (committed as 92a9c36)
**Branch**: `feature/remote-multiuser-mcp`
**Plan**: `plans/260623-remote-mcp-multiuser-deploy/phase-04-admin-tool-allowlist-runtime-filter.md`

## What Happened

Non-tech colleagues on the remote HTTP surface need protection from firing destructive tools (delete, bulk-write, create project) — Phase 4 hides 7 high-impact tools on http (showing 37 of 44) while stdio keeps full 44 (RÀNG BUỘC SỐ 1). Runtime filter design (M5 fix from red-team: import-time gating is brittle) — filter runs at list-time and dispatch-time, env override both ways. Tests: 67 green; in-process stdio=44, http=37, http+override=44; over-wire dispatch block confirmed (`delete_work_package`→ValueError→isError=True).

## What Shipped

**Three modules:**

1. **`server/allowlist.py` (NEW, 44 LOC)**: `install(mcp)` wraps `list_tools()` and `call_tool()` on the FastMCP instance, then re-registers both to the lowlevel SDK handlers (`_mcp_server.list_tools()`/`call_tool()`) so in-process calls and over-the-wire requests stay consistent. `list_tools()` filters out destructive tools when `admin_destructive_enabled()`=False; `call_tool()` raises ValueError on disabled destructive dispatch (caught by SDK's exception handler → clean isError=True over-wire). Idempotent guard (`_allowlist_installed` flag).

2. **`server/config.py` (+48 LOC)**: Single-source `_DESTRUCTIVE_TOOLS` frozenset (7 tools: delete_work_package, delete_news, remove_member, create_project, update_project, bulk_create_work_packages, bulk_update_work_packages — re-grepped, not guessed). `is_destructive(tool_name)` predicate. `admin_destructive_enabled(env)` transport-aware: stdio→True, http→False, override via `OP_MCP_ENABLE_ADMIN_DESTRUCTIVE` (true/1/yes or false/0/no). Env read per-call (GIL-safe dict lookup; no concurrency risk).

3. **`server/app.py` (+3 LOC)**: Calls `allowlist.install(mcp)` once after FastMCP creation (module import cached → no re-wrapping).

**Tests:** 124 new lines in `tests/test_admin_allowlist.py` — mcp-free via FakeMcp mock. Predicates + install filter verified in-process; dispatch block over-wire behavior inferred via mock. Remains compatible with `pytest --with httpx`.

## Key Decisions

- **Runtime filter, not import-time gate:** M5 (red-team finding) — import-time visibility control doesn't reflect env changes (or commit the magic number of tools). Moving to runtime (`list_tools`/`call_tool` wrappers) makes tool count deterministic and env-driven.
- **Both list-hide AND dispatch-block:** hiding alone bypasses by guessing the name; dispatch block fires before `orig_call_tool` runs, so no path reaches the underlying tool while disabled.
- **Lowlevel handler re-registration:** mirrors SDK's own `_setup_handlers` pattern (verified in mcp 1.28) — same public API, private `_mcp_server` + `validate_input=False` kwarg. Risky if SDK refactors (breaks loudly at startup, not silently). Code review recommends `hasattr` assert for friendlier failure; applied as optional hardening.
- **`is_destructive` naming:** bundles true deletes (delete_work_package, delete_news, remove_member) + high-impact non-deletes (create/update project, bulk writes). Semantically broader than literal "destructive" but matches user-approved red-team H5 correction. Flagged for user decision (leave as-is vs rename to `is_restricted`); left unchanged.
- **Env override both ways:** `OP_MCP_ENABLE_ADMIN_DESTRUCTIVE=true` unlocks http, `false` locks stdio. Reads live os.environ per call (no caching). Used by Phase 5 deploy smoke-test (verify 44 available when needed).

## Notable

- Code review APPROVED 5/5; two cheap hardening notes applied (idempotent guard + hasattr assert for SDK version fragility).
- H5 (red-team destructive-set audit) resolved: grep-verified 7 tools, single-source frozenset eliminates list/dispatch drift. `delete_work_package` (the most dangerous, missed in original list) now caught.
- No new lint/format/py_compile errors; 67 tests total (47 old + 20 new for phases 2+4).
- Phases 2 and 4 shipped; Phase 3 (auth impl) and Phase 5 (deploy/docs) remain blocked pending user's OAuth A vs B decision from Phase 1 spike.

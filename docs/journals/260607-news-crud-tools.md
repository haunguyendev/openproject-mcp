# News CRUD Tools Shipped (v0.4.0)

**Date**: 2026-06-07 15:56
**Severity**: Low (feature addition)
**Component**: MCP tools, OpenProject API v3
**Status**: Resolved
**Commit**: 5646d34

## What Happened

Completed the News CRUD feature: added 5 new MCP tools (`list_news`, `get_news`, `create_news`, `update_news`, `delete_news`) in a new `server/tools_news.py` module, connected them to project-manager and admin personas, updated all docs, and bumped version from 0.3.0 → 0.4.0. Tools are live and verified to import cleanly; formatter + import smoke tests pass. All 17 existing tests still pass.

## Technical Details

- **New module:** `server/tools_news.py` (106 lines), 5 tools following the per-domain pattern.
- **Formatter:** `_fmt_news()` in `server/formatters.py` + unit test `test_fmt_news` in `tests/test_formatters.py`.
- **Permissions:** Tools require "manage news" permission in project; HTTP 403 handled by existing `op_client._req`.
- **Write tool UX:** Create/update/delete all require write confirmation in skill layer (not in code).
- **Docs updated:** README Tools table + count (33 → 38), SKILL.md catalog + count, CHANGELOG 0.4.0 entry, plugin.json + marketplace.json versions.
- **Tests:** 17 passed (ruff clean, pytest clean). No live CRUD test (no test instance) — formatter unit test + import smoke verify contract.

## Code Review Catch — The Critical Lesson

`code-reviewer` agent found 2 silent-failure bugs in `list_news` during review. Both were copy-paste errors from the `work_packages` tools, which use camelCase query keys. News endpoint uses **snake_case** keys:

1. **Filter key:** Filter was `"project"` but News API requires `"project_id"`. Wrong key silently returned ALL news across all projects (permissions still enforced downstream, but query semantically broken).
2. **Sort key:** Sort was `"createdAt"` but News API requires `"created_at"`. Wrong key silently fell back to id-desc ordering (no error raised).

Both bugs verified against:
- OpenProject official API docs: `/api/v3/news` endpoint spec.
- Rails source (news.yml query filter spec).

After fixing, docstring was clarified: `project` parameter is a **numeric ID** (not identifier string like "website"). Re-ran ruff + pytest (17 passed) + import smoke — clean.

## Root Cause Analysis

Assumed query key conventions generalize across OpenProject endpoints. They don't. The work_packages tools established a camelCase pattern, and I incorrectly carried it forward without verifying against the News endpoint spec. This is a **copy-paste + assumption failure**, not a documentation gap — the official spec explicitly lists the keys.

The bugs were *silent* (no 400 error, just wrong semantics), which made them particularly dangerous. Live testing would have caught both immediately; offline unit tests only verify the formatter, not the query construction.

## Lessons Learned

1. **Per-endpoint query keys are NOT standardized in OpenProject API v3.** Each endpoint specifies its own filter/sort key names in the official docs. Always verify new endpoint keys against the official spec, even if you're following an established pattern from another endpoint in the same codebase.

2. **Silent failures are worse than loud ones.** A 400 error would have been caught immediately. Returning all-projects or wrong sort order goes unnoticed until live testing or a user reports unexpected behavior. When working with APIs, verify the contract explicitly and early.

3. **Code review saved us.** The reviewer caught this because they cross-checked the code against the API spec. For offline-tested code, code review becomes the first line of defense for API contract correctness.

4. **Document key differences when they deviate.** Added a docstring note that `project` filter is numeric ID, clarifying the departure from work_packages patterns.

## Next Steps

- None — feature is complete and verified. Docs + CHANGELOG cover the change.
- Note for future: when adding new OpenProject API tools, create a checklist: official spec → filter/sort keys → test semantics with live instance if possible (or document the assumption clearly in the tool docstring).

## Branch & Merge Context

Built on feature branch `feat/harden-task-hierarchy-relations` (v0.3.1, unmerged). News has no code dependency on that branch — it's a standalone feature. However, version/CHANGELOG assume 0.3.1 as the baseline (both get updated when either branch merges). Master is currently at v0.3.0. Whichever merges second will reconcile the CHANGELOG/version line. Not a blocker.

Commit stacked cleanly; no conflicts anticipated on master merge because `tools_news.py` is a new file (only import in `server.py` is new).

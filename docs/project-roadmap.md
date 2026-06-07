# Project Roadmap — openproject-mcp

## Current Version: 0.4.0 (2026-06-07)

**Status:** Stable, production-ready  
**Shipped:** All core features; news tools recently added

## Completed Phases

### Phase 0 (v0.1.0 — 2026-06-07)
**Initial Release**

- ✅ Python MCP server on FastMCP with 16 tools
- ✅ Work package CRUD + comments
- ✅ Projects, members, metadata queries
- ✅ Basic time tracking
- ✅ Simple reports

### Phase 1 (v0.2.0 — 2026-06-07)
**Modularization & Resilience**

- ✅ Separated `server.py` into modular sub-files (<230 LOC each)
  - `app.py`, `config.py`, `op_client.py`, `formatters.py`
- ✅ Shared HTTP client with connection reuse
- ✅ Retry on 429/5xx with `Retry-After` honor
- ✅ Clear error messages (401, 403, 404, 422)
- ✅ Logging to stderr (stdout reserved for MCP)
- ✅ MIT license + CHANGELOG + README polish

### Phase 2 (v0.2.1 — 2026-06-07)
**Secrets Security & CI**

- ✅ Environment-only credentials (`.mcp.json` no longer contains secrets)
- ✅ Verified no keys in repo: `git grep -iE "api[_-]?key"`
- ✅ Added community health files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`
- ✅ Issue + PR templates
- ✅ CI workflow: ruff lint, format check, syntax, JSON validation
- ✅ `.claude-plugin/marketplace.json` for direct install

### Phase 3 (v0.3.0 — 2026-06-07)
**Personas & Admin Tooling**

- ✅ Persona-aware skill router (`SKILL.md` + role-specific guides)
- ✅ Role detection via intent + `whoami` API
- ✅ Coder persona tools: `list_children`, `get_relations`, `create_relation`
- ✅ Manager persona tools: versions, workload, status board, portfolio reports
- ✅ Reporting persona: my_time_summary, 7 report tools
- ✅ Admin persona: user/role management, create/update/archive projects, member admin
- ✅ Confirm-first pattern for write tools
- ✅ Double-confirm for destructive actions
- ✅ Unit tests for formatters + validators
- ✅ CI test job

### Phase 4 (v0.3.1 — 2026-06-07)
**Relation & Hierarchy Hardening**

- ✅ Idempotent POST: never retry create ops (prevent duplicates)
- ✅ Relation validators: reject self, duplicate (either direction), direct 2-node cycles
- ✅ Re-parenting: `update_work_package(parent_id=...)` moves subtask
- ✅ Clearer 404 errors with request path
- ✅ Coder skill guidance: relation direction, single-direction rule, scheduling, deduplication
- ✅ Unit tests for `validate_relation`

### Phase 5 (v0.4.0 — 2026-06-07)
**News CRUD Tools**

- ✅ 5 news tools: `list_news`, `get_news`, `create_news`, `update_news`, `delete_news`
- ✅ News formatter: `_fmt_news` (id, title, summary, created_on, url)
- ✅ Routed under project-manager and admin personas
- ✅ Write confirmation + double-confirm for delete
- ✅ Permission check: 403 if "manage news" role missing
- ✅ Unit test for `_fmt_news`

## Planned Work (Future Releases)

### Near-term (v0.5.0 — Ideas)

#### News Workflow Polish
- [ ] Bulk news operations (create multiple in batch)
- [ ] News filters: `list_news(project_id, created_after, ...)`
- [ ] News update permission: allow partial updates without full redraft
- [ ] Skill guidance: news templates, common workflows

#### Broader Cycle Detection
- [ ] Current: rejects A → B → A (2-node)
- [ ] New: detect longer cycles (A → B → C → A)
- [ ] Graph traversal in `validators.py` (DFS or BFS)
- [ ] Skill guidance: "cycle detected; break with 'relates' instead"

#### Cross-Project Relations
- [ ] Current: tools assume same-project (subtasks, some relations)
- [ ] New: allow relations between projects
- [ ] Re-parent across projects (requires API support verification)
- [ ] Skill guidance: "cross-project hierarchy implications"

#### Performance Optimizations
- [ ] Prefetch relations when listing work packages (reduce round-trips)
- [ ] Cache OpenProject metadata (types, statuses, priorities)
- [ ] Batch API calls (if OpenProject v3 supports bulk ops)
- [ ] Profile response times; optimize slow queries

### Medium-term (v0.6.0+ — Exploration)

#### Extended Reporting
- [ ] Custom reports: user-defined filters, aggregations
- [ ] Time allocation trends (hours per month, per team)
- [ ] Budget tracking (if OpenProject has cost fields)
- [ ] Capacity planning (team workload forecast)
- [ ] Risk summary (overdue, blocked, at-risk tasks)

#### Advanced Hierarchy
- [ ] Multi-level project templates
- [ ] Smart re-parenting (detect conflicts, suggest solutions)
- [ ] Epic tracking (large features spanning multiple tasks)
- [ ] Dependency chains: critical path analysis

#### Integration Bridges
- [ ] Sync with external tools (Slack updates, GitHub actions, etc.)
- [ ] Webhook support for real-time event streaming
- [ ] Export to Excel, PDF reports
- [ ] Import bulk tasks from CSV

#### AI Agent Enhancements
- [ ] Proactive suggestions ("Task overdue; reassign?")
- [ ] Smart task routing (assign based on skills + workload)
- [ ] Natural language release notes (summarize changes by version)
- [ ] Anomaly detection (unusual patterns in time logs)

## Version History Summary

| Version | Release | Focus | Tools |
|---------|---------|-------|-------|
| 0.1.0 | 2026-06-07 | MVP | 16 |
| 0.2.0 | 2026-06-07 | Modularized, resilient | 16 |
| 0.2.1 | 2026-06-07 | Secrets-out, CI | 16 |
| 0.3.0 | 2026-06-07 | Personas, admin | 33 |
| 0.3.1 | 2026-06-07 | Hierarchy hardening | 33 |
| **0.4.0** | **2026-06-07** | **News CRUD** | **38** |
| 0.5.0 | Planned | News polish, cycle detection, cross-project | TBD |
| 0.6.0+ | Exploration | Extended reporting, integrations, AI enhancements | TBD |

## Success Metrics

### Shipped Features
- [x] 38 tools across 4 personas
- [x] Works with any self-hosted OpenProject instance (API v3)
- [x] Safe writes (confirm-first, double-confirm destructive)
- [x] Resilient (retry, clear errors)
- [x] No secrets in repo
- [x] CI passing (lint, format, syntax, tests)
- [x] Documented (README, CONTRIBUTING, SECURITY, SKILL guides)

### User Satisfaction
- 🟡 Real-world usage feedback (not yet collected; need pilot users)
- 🟡 Response time <3s (measured in development; needs prod data)
- 🟡 No duplicate-create incidents (not yet observed; needs time)

### Code Quality
- [x] All modules <230 LOC
- [x] Test coverage for helpers ≥80%
- [x] Vietnamese docstrings (convention) read by Claude
- [x] Clear error messages
- [x] No hardcoded secrets

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|----------|--------|-----------|
| OpenProject API breaking change | Low | High | Track API docs, add version matrix to README |
| Duplicate creates on network failure | Low | High | Never retry POST (implemented v0.3.1) |
| Token leak in logs | Low | Critical | Log only `api_key_set=bool`, audit all print statements |
| Concurrent edit conflicts | Medium | Medium | Optimistic locking via `lockVersion` (implemented) |
| Slow queries (large projects) | Medium | Medium | Pagination + filtering; cache metadata |
| User loses unsaved data | Low | High | Confirm-first pattern for writes (implemented) |
| Cross-project relations break | Low | Medium | Document limitation; plan for v0.5.0 |

## Dependencies & External Factors

| Dependency | Version | Status | Notes |
|-----------|---------|--------|-------|
| Python | 3.10+ | ✅ Stable | PEP 723 inline metadata |
| mcp | ≥1.2.0 | ✅ Stable | MCP v1.0+ protocol |
| httpx | ≥0.27 | ✅ Stable | Async-capable; we use sync |
| OpenProject | API v3 | ✅ Stable | Community + Cloud supported |
| uv | Latest | ✅ Stable | Script runner, no virtualenv |
| ruff | Latest | ✅ Stable | Lint + format |

## Maintenance Schedule

### Regular Tasks
- **Weekly:** Monitor issues, respond to PRs
- **Monthly:** Review & merge contributions; test against new OpenProject releases
- **Quarterly:** Plan next phase; assess real-world feedback
- **On release:** Version bump (4 places), CHANGELOG, tag, CI validation

### Deprecation Policy
- **Breaking changes:** Announce in README + CHANGELOG; give 2 releases notice
- **Deprecated features:** Mark with `# TODO: deprecated in vX.Y.Z`; remove in vX+1.0.0

## Communication & Support

- **GitHub issues:** Bug reports, feature requests
- **Discussions:** Q&A, feedback, ideas
- **CONTRIBUTING.md:** Development setup, PR guidelines
- **SECURITY.md:** Security issues (non-public; email maintainer)

## Open Questions

1. **Real-world usage:** Who are the first paying users? What workflows matter most?
2. **Cross-project strategy:** Should we support relations/re-parenting across projects? OpenProject API support TBD.
3. **Performance baselines:** What's acceptable latency for large projects (1000+ tasks)? Needs benchmarking.
4. **Integration priorities:** Which integrations (Slack, GitHub, etc.) would unlock most value?
5. **Skill evolution:** Should the skill adapt based on user role or project context? Expand guidance?

## Next Immediate Action

1. Release v0.4.0 to marketplace + tag
2. Gather user feedback on news tools (usage, UX)
3. Plan v0.5.0 scope (news polish vs. cycle detection vs. performance)
4. Identify pilot users for real-world validation

# openproject-mcp Documentation

Complete project documentation for the OpenProject MCP server and Claude plugin.

## Quick Navigation

### For Project Managers & Product Teams
**Start here:** [`project-overview-pdr.md`](./project-overview-pdr.md)
- Project vision, problem statement, target users
- Functional and non-functional requirements
- Success criteria and acceptance checklist
- Technical constraints overview

### For Developers Joining the Project
**Read in order:**
1. [`project-overview-pdr.md`](./project-overview-pdr.md) — understand the "why"
2. [`codebase-summary.md`](./codebase-summary.md) — understand the structure
3. [`code-standards.md`](./code-standards.md) — follow conventions when coding
4. [`system-architecture.md`](./system-architecture.md) — understand how it works

### For DevOps / Infrastructure Teams
**Start here:** [`deployment-guide.md`](./deployment-guide.md)
- 4 installation paths (Claude Code, Desktop, Cowork)
- Configuration (environment variables)
- Troubleshooting table
- Security checklist
- Monitoring & logging

### For Understanding the System
**Read in order:**
1. [`codebase-summary.md`](./codebase-summary.md) — module overview + 38 tools inventory
2. [`system-architecture.md`](./system-architecture.md) — request flow, auth, idempotency, locking
3. [`code-standards.md`](./code-standards.md) — naming conventions, tool design patterns

### For Planning Next Phases
**Start here:** [`project-roadmap.md`](./project-roadmap.md)
- Completed phases (v0.1.0 → v0.4.0)
- Planned work (v0.5.0+, ideas for v0.6.0+)
- Success metrics and open questions
- Risk assessment

---

## Document Overview

| Document | LOC | Purpose | Audience |
|----------|-----|---------|----------|
| **project-overview-pdr.md** | 128 | Vision, requirements, constraints, acceptance criteria | PM, leads, stakeholders |
| **codebase-summary.md** | 225 | Module breakdown, tool inventory, request flow | Developers, code reviewers |
| **code-standards.md** | 448 | Naming, docstrings, error handling, tool design, testing, versioning | Developers, code reviewers |
| **system-architecture.md** | 444 | Architecture diagram, auth, idempotency, locking, error handling, security | Developers, architects |
| **project-roadmap.md** | 220 | Completed phases, planned work, risks, metrics, maintenance | PM, leads |
| **deployment-guide.md** | 459 | Installation (4 paths), configuration, troubleshooting, upgrades | DevOps, users |

**Total:** 1,924 LOC (well-organized, no file exceeds 800 LOC limit)

---

## Key Facts

- **Current version:** 0.4.0 (shipped 2026-06-07)
- **Tools:** 38 across 4 personas (member, project-manager, coder, admin)
- **Server:** Single Python MCP server; modularized (13 files <230 LOC each)
- **Stack:** FastMCP + httpx; dependencies via PEP 723; run via `uv run --script`
- **API:** OpenProject REST API v3 (any self-hosted instance)
- **Auth:** HTTP Basic Auth (username "apikey", token from environment)
- **Philosophy:** Dependency-light, resilient, secrets-out, confirm-before-write

---

## Getting Started

### 1. First Time Here?
Read [`project-overview-pdr.md`](./project-overview-pdr.md) (5 min) for the big picture.

### 2. Want to Install?
Follow [`deployment-guide.md`](./deployment-guide.md) — 4 installation paths (Claude Code, Desktop, Cowork, dev mode).

### 3. Want to Contribute Code?
1. Read [`code-standards.md`](./code-standards.md) for naming + docstring conventions
2. Read [`codebase-summary.md`](./codebase-summary.md) for module overview
3. Read [`system-architecture.md`](./system-architecture.md) for request flow
4. See `../CONTRIBUTING.md` for PR guidelines

### 4. Want to Understand the Request Flow?
See [`system-architecture.md`](./system-architecture.md) — includes Mermaid diagram + step-by-step example.

### 5. Debugging an Issue?
See [`deployment-guide.md`](./deployment-guide.md) → Troubleshooting section.

---

## Documentation Standards

All docs follow these conventions:
- **Accuracy:** Every code reference verified against actual codebase
- **Examples:** Real code from the project (not invented)
- **Tables:** Used for reference data (tools, modules, troubleshooting)
- **Links:** Internal cross-references help navigation
- **Clarity:** No jargon without explanation; layered for different audiences
- **Completeness:** No "TODO: update" sections; remove stale content instead

---

## Version History

Documentation is versioned alongside the codebase:
- **v0.4.0** — Added news tools; documented all 38 tools + 4 personas
- **v0.3.1** — Documented relation hardening, idempotent retry, optimistic locking
- **v0.3.0** — Documented persona routing, admin tools, reporting
- **v0.2.1** — Documented secrets-out, CI setup
- **v0.2.0** — Initial modularization docs

---

## Feedback & Maintenance

### Reporting Issues with Docs
- Found outdated info? Create GitHub issue with `[DOCS]` tag
- Code behavior changed? Update relevant doc and create PR
- Docs unclear? Suggest rewording in issue or PR

### Updating Docs After Code Changes
When implementing a new feature:
1. Update relevant doc (codebase-summary, code-standards, system-architecture, roadmap)
2. If new module added: add to codebase-summary table
3. If new tool added: add to tool inventory + roadmap
4. If tool parameter changed: update code-standards examples
5. If architecture changed: update system-architecture diagram

---

## Quick Reference

### All 38 Tools (by area)
- **Work packages:** list_work_packages, get_work_package, create_work_package, update_work_package, add_comment
- **Projects & metadata:** list_projects, list_project_members, list_versions, list_types, list_statuses, list_priorities, whoami
- **Coder:** list_children, get_relations, create_relation
- **Time tracking:** log_time, list_time_entries, my_time_summary
- **Reports:** report_overdue, report_my_tasks, report_project_progress, report_workload, report_status_board, report_time, report_portfolio
- **News:** list_news, get_news, create_news, update_news, delete_news
- **Admin:** list_users, get_user, list_roles, create_project, update_project, add_member, update_member, remove_member

### Key Concepts
- **MCP:** Model Context Protocol; Claude's standard for tool access
- **Persona:** Role-based router; guides tool selection (member, project-manager, coder, admin)
- **Skill:** Bundled persona guide + role detection logic
- **Trimmed JSON:** Tool output contains only essential fields + `url` for direct access
- **Optimistic locking:** `lockVersion` field prevents concurrent-edit conflicts
- **Idempotent retry:** GET/PATCH/DELETE retry on transient failure; POST never retries (write-once)

---

## Related Files

- **Code:** `/server/` — 13 Python files (1,361 LOC)
- **Tests:** `/tests/` — unit tests for pure helpers
- **Skills:** `/skills/openproject-manager/` — persona router + role-specific guides
- **README:** `../README.md` — user-facing setup guide
- **CHANGELOG:** `../CHANGELOG.md` — version history + release notes
- **Contributing:** `../CONTRIBUTING.md` — development setup
- **Security:** `../SECURITY.md` — security policy + vulnerability reporting

---

## Questions?

- **Setup issues?** See [`deployment-guide.md`](./deployment-guide.md#troubleshooting)
- **Code conventions?** See [`code-standards.md`](./code-standards.md)
- **How does it work?** See [`system-architecture.md`](./system-architecture.md)
- **What's next?** See [`project-roadmap.md`](./project-roadmap.md)

For issues or suggestions, open a GitHub issue or discussion.

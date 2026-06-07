# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.1] - 2026-06-07

### Changed
- Read `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` from the environment; `.mcp.json` no longer contains secrets and is committed to the repo (removed `.mcp.json.example`).
- Added `.claude-plugin/marketplace.json` for direct install via `/plugin marketplace add`.
- Rewrote the README in English and generalized the plugin for any OpenProject instance (removed the hardcoded URL).
- Added an "AI agent quick setup" flow — paste a link and the agent self-installs.

### Added
- Project health files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue/PR templates, and `.editorconfig`.
- CI workflow: ruff lint, ruff format check, Python syntax check, and JSON config validation.

## [0.2.0] - 2026-06-07

### Changed
- Separated secrets from git; shared HTTP client (connection reuse); one retry on `429`/`5xx` honoring `Retry-After`; clearer `401` errors; logging to stderr.
- Added the MIT license, this changelog, and ruff configuration.

## [0.1.0] - 2026-06-07

### Added
- Python MCP server (FastMCP) for OpenProject API v3 with 16 tools — work packages, projects/members, metadata, time tracking, and reports.
- `openproject-manager` skill with workflow guidance.

# Changelog

## [0.2.1] - 2026-06-07

### Thay đổi
- Chuyển sang đọc `OPENPROJECT_API_KEY` từ biến môi trường shell — `.mcp.json` không còn chứa secret và được commit vào repo (bỏ `.mcp.json.example`).
- Thêm `.claude-plugin/marketplace.json` — cài trực tiếp qua `/plugin marketplace add`.
- README: hướng dẫn cài qua marketplace cho Claude Code, cấu hình key qua `~/.zshrc`.

## [0.2.0] - 2026-06-07

### Thay đổi
- Tách secret khỏi git: `.mcp.json` vào `.gitignore`, thêm `.mcp.json.example`.
- Server: client HTTP dùng chung (connection reuse), retry 1 lần cho 429/5xx (tôn trọng `Retry-After`), thông báo lỗi 401 rõ ràng, logging ra stderr.
- Thêm LICENSE (MIT), CHANGELOG, cấu hình ruff.

## [0.1.0] - 2026-06-07

### Thêm mới
- MCP server Python (FastMCP) cho OpenProject API v3: 16 tool — work packages, dự án/thành viên, metadata, time tracking, báo cáo.
- Skill `openproject-manager` hướng dẫn workflow.

# Changelog

## [0.2.0] - 2026-06-07

### Thay đổi
- Tách secret khỏi git: `.mcp.json` vào `.gitignore`, thêm `.mcp.json.example`.
- Server: client HTTP dùng chung (connection reuse), retry 1 lần cho 429/5xx (tôn trọng `Retry-After`), thông báo lỗi 401 rõ ràng, logging ra stderr.
- Thêm LICENSE (MIT), CHANGELOG, cấu hình ruff.

## [0.1.0] - 2026-06-07

### Thêm mới
- MCP server Python (FastMCP) cho OpenProject API v3: 16 tool — work packages, dự án/thành viên, metadata, time tracking, báo cáo.
- Skill `openproject-manager` hướng dẫn workflow.

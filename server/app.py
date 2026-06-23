"""FastMCP app instance dùng chung. Các module tools đăng ký lên đây qua @mcp.tool()."""

import allowlist
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("openproject")

# Lọc nhóm tool destructive theo transport (Phase 4) — runtime, không gate lúc import.
allowlist.install(mcp)

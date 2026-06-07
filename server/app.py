"""FastMCP app instance dùng chung. Các module tools đăng ký lên đây qua @mcp.tool()."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("openproject")

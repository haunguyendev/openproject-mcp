"""Runtime allowlist (Phase 4): ẩn + chặn nhóm tool destructive theo transport.

Lọc ở **runtime** (không gate lúc import — M5) nên đếm tool xác định và đọc env hiện tại:
- `list_tools`: bỏ tool destructive khi `admin_destructive_enabled()` False.
- `call_tool` (dispatch): chặn cả khi bị gọi trực tiếp → không bypass bằng cách đoán tên.

Bọc cả method trên instance FastMCP (caller trực tiếp như lệnh verify) lẫn handler lowlevel
đã đăng ký (đường over-the-wire) để hai nơi luôn nhất quán.
"""

import config


def install(mcp) -> None:
    """Gắn bộ lọc destructive vào FastMCP instance. Gọi một lần sau khi tạo `mcp`."""
    if getattr(mcp, "_allowlist_installed", False):
        return  # idempotent: tránh bọc chồng nếu lỡ gọi 2 lần
    if not hasattr(mcp, "_mcp_server"):  # fail rõ ràng nếu SDK đổi vị trí server lowlevel
        raise AttributeError("FastMCP instance thiếu `_mcp_server` — phiên bản mcp không hợp.")

    orig_list_tools = mcp.list_tools
    orig_call_tool = mcp.call_tool

    async def list_tools():
        tools = await orig_list_tools()
        if config.admin_destructive_enabled():
            return tools
        return [t for t in tools if not config.is_destructive(t.name)]

    async def call_tool(name, arguments):
        if config.is_destructive(name) and not config.admin_destructive_enabled():
            raise ValueError(
                f"Tool '{name}' bị tắt trên deployment này (nhóm destructive). "
                "Bật bằng OP_MCP_ENABLE_ADMIN_DESTRUCTIVE=true nếu hiểu rủi ro."
            )
        return await orig_call_tool(name, arguments)

    # Caller trực tiếp (in-process, vd lệnh verify đếm tool).
    mcp.list_tools = list_tools
    mcp.call_tool = call_tool
    # Đường over-the-wire: ghi đè handler đã đăng ký trong _setup_handlers().
    mcp._mcp_server.list_tools()(list_tools)
    mcp._mcp_server.call_tool(validate_input=False)(call_tool)
    mcp._allowlist_installed = True

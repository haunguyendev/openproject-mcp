# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp>=1.2.0",
#     "httpx>=0.27",
# ]
# ///
"""OpenProject MCP server — entry point.

Cấu hình qua biến môi trường (xem README):

  OPENPROJECT_URL              URL của OpenProject (vd: https://your-openproject.example.com)
  OPENPROJECT_API_KEY          API key cá nhân (My account → Access tokens → API)
  OPENPROJECT_TIMEOUT_SECONDS  Timeout request (mặc định 30)

OpenProject API v3 xác thực bằng Basic Auth: username "apikey", password = API key.

Code được tách module: config (env), op_client (HTTP), formatters (rút gọn JSON),
app (FastMCP instance), và các tools_*.py đăng ký tool lên app.mcp.
"""

# Import các module tools để side-effect đăng ký @mcp.tool() lên app.mcp.
import tools_admin  # noqa: F401
import tools_coder  # noqa: F401
import tools_news  # noqa: F401
import tools_projects  # noqa: F401
import tools_reports  # noqa: F401
import tools_time  # noqa: F401
import tools_work_packages  # noqa: F401
from app import mcp
from config import API_KEY, BASE_URL, log

__version__ = "0.4.0"


def main() -> None:
    log.info(
        "openproject-mcp v%s — base_url=%s, api_key_set=%s",
        __version__,
        BASE_URL or "(chưa cấu hình)",
        bool(API_KEY),
    )
    mcp.run()


if __name__ == "__main__":
    main()

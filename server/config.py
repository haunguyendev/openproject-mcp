"""Cấu hình & logging dùng chung cho OpenProject MCP server.

Đọc từ biến môi trường (xem README). stdout dành cho giao thức MCP nên log ra stderr.
"""

import logging
import os
import sys

BASE_URL = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
API_KEY = os.environ.get("OPENPROJECT_API_KEY", "")
TIMEOUT = float(os.environ.get("OPENPROJECT_TIMEOUT_SECONDS", "30"))

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s openproject-mcp: %(message)s",
)
log = logging.getLogger("openproject-mcp")

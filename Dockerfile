# OpenProject MCP — remote multi-user (Streamable HTTP) image.
# stdio vẫn chạy như cũ qua `uv run --script`; image này dành cho deploy HTTP sau reverse proxy.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_CACHE_DIR=/opt/uv-cache \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY server/ ./server/

# Pre-warm PEP723 deps vào layer image để cold start không phải tải lại.
RUN uv run --with "mcp>=1.8.0" --with "httpx>=0.27" --with "starlette>=0.37" \
        --with "uvicorn>=0.30" python3 -c "import mcp, httpx, starlette, uvicorn"

# Chạy non-root. uv CẦN ghi vào cache mỗi lần `uv run` → mcp phải SỞ HỮU cache (không chỉ đọc).
RUN useradd -m -u 1000 mcp && chown -R mcp /app /opt/uv-cache
USER mcp

# Mặc định http multi-user, bind mọi interface trong container; destructive tools tắt.
# OPENPROJECT_URL / MCP_PUBLIC_URL / ALLOWED_HOSTS đặt qua env/compose lúc deploy.
ENV MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    OP_MCP_ENABLE_ADMIN_DESTRUCTIVE=false \
    OPENPROJECT_TIMEOUT_SECONDS=15
EXPOSE 8000

# Healthcheck dùng endpoint metadata công khai (không cần auth).
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python3 -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/.well-known/oauth-protected-resource',timeout=4).status==200 else 1)"

CMD ["uv", "run", "--script", "server/server.py"]

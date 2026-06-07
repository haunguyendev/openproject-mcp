#!/usr/bin/env bash
# OpenProject MCP installer — detect Claude Code / Claude Desktop and configure the server.
# macOS & Linux. Run after cloning the repo:  ./scripts/install.sh
set -euo pipefail

# Locate repo root + server entry point (this script lives in scripts/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER="$REPO_ROOT/server/server.py"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
info() { printf '  %s\n' "$1"; }
err()  { printf '\033[31mError:\033[0m %s\n' "$1" >&2; }

[ -f "$SERVER" ] || { err "Không thấy server.py tại $SERVER — hãy chạy script từ trong repo đã clone."; exit 1; }

# Desktop config path differs per OS; Windows is not covered by this bash installer.
OS="$(uname -s)"
case "$OS" in
  Darwin) DESKTOP_CFG="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
  Linux)  DESKTOP_CFG="$HOME/.config/Claude/claude_desktop_config.json" ;;
  *) err "OS không hỗ trợ: $OS (chỉ macOS/Linux). Windows: theo hướng dẫn thủ công trong README."; exit 1 ;;
esac

HAS_CODE=0;    if command -v claude >/dev/null 2>&1; then HAS_CODE=1; fi
HAS_DESKTOP=0; if [ -d "$(dirname "$DESKTOP_CFG")" ]; then HAS_DESKTOP=1; fi

bold "OpenProject MCP — Installer"
info "Repo:           $REPO_ROOT"
info "Claude Code:    $( [ $HAS_CODE = 1 ]    && echo 'phát hiện ✓' || echo 'không thấy' )"
info "Claude Desktop: $( [ $HAS_DESKTOP = 1 ] && echo 'phát hiện ✓' || echo 'không thấy' )"

if [ $HAS_CODE = 0 ] && [ $HAS_DESKTOP = 0 ]; then
  err "Không phát hiện Claude Code hay Claude Desktop trên máy."; exit 1
fi

# Choose target(s) among what was detected.
echo
if [ $HAS_CODE = 1 ] && [ $HAS_DESKTOP = 1 ]; then
  bold "Cài cho đâu?"
  info "1) Claude Code"
  info "2) Claude Desktop"
  info "3) Cả hai"
  read -r -p "Chọn [1/2/3]: " choice
  case "$choice" in
    1) TARGETS="code" ;;
    2) TARGETS="desktop" ;;
    3) TARGETS="code desktop" ;;
    *) err "Lựa chọn không hợp lệ."; exit 1 ;;
  esac
elif [ $HAS_CODE = 1 ]; then
  TARGETS="code"; info "Chỉ có Claude Code — cài cho mục này."
else
  TARGETS="desktop"; info "Chỉ có Claude Desktop — cài cho mục này."
fi

# Gather credentials (token input hidden); reuse current env as defaults if set.
echo
read -r -p "OPENPROJECT_URL [${OPENPROJECT_URL:-https://your-openproject.example.com}]: " IN_URL
URL="${IN_URL:-${OPENPROJECT_URL:-}}"
[ -n "$URL" ] || { err "URL không được rỗng."; exit 1; }
read -r -s -p "OPENPROJECT_API_KEY: " IN_KEY; echo
KEY="${IN_KEY:-${OPENPROJECT_API_KEY:-}}"
[ -n "$KEY" ] || { err "API key không được rỗng."; exit 1; }

# Ensure uv and resolve its absolute path (Desktop does not inherit shell PATH).
if ! command -v uv >/dev/null 2>&1; then
  bold "uv chưa có — cài qua astral installer…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
UV="$(command -v uv || true)"
[ -n "$UV" ] || { err "uv vẫn không tìm thấy sau khi cài."; exit 1; }

# Claude Code: native CLI writes the config (user scope = available in every project).
install_code() {
  bold "→ Claude Code"
  claude mcp remove -s user openproject >/dev/null 2>&1 || claude mcp remove openproject >/dev/null 2>&1 || true
  claude mcp add -s user \
    -e OPENPROJECT_URL="$URL" \
    -e OPENPROJECT_API_KEY="$KEY" \
    -e OPENPROJECT_TIMEOUT_SECONDS=30 \
    openproject \
    -- "$UV" run --script "$SERVER"
  info "Đã thêm. Kiểm tra: claude mcp get openproject  (hoặc /mcp trong Claude Code)."
}

# Claude Desktop: merge into claude_desktop_config.json via python (back up, never overwrite).
install_desktop() {
  bold "→ Claude Desktop"
  mkdir -p "$(dirname "$DESKTOP_CFG")"
  [ -f "$DESKTOP_CFG" ] || echo '{}' > "$DESKTOP_CFG"
  CONFIG="$DESKTOP_CFG" UV="$UV" SERVER="$SERVER" URL="$URL" KEY="$KEY" python3 - <<'PY'
import json, os, shutil, time, sys
cfg = os.environ["CONFIG"]
try:
    with open(cfg) as f:
        data = json.load(f) if os.path.getsize(cfg) else {}
except json.JSONDecodeError:
    sys.exit("claude_desktop_config.json không phải JSON hợp lệ — sửa tay hoặc xoá rồi chạy lại.")
if not isinstance(data, dict):
    sys.exit("Cấu trúc config không như mong đợi (root không phải object).")
shutil.copy2(cfg, cfg + ".bak." + time.strftime("%Y%m%d-%H%M%S"))
data.setdefault("mcpServers", {})
data["mcpServers"]["openproject"] = {
    "command": os.environ["UV"],
    "args": ["run", "--script", os.environ["SERVER"]],
    "env": {
        "OPENPROJECT_URL": os.environ["URL"],
        "OPENPROJECT_API_KEY": os.environ["KEY"],
        "OPENPROJECT_TIMEOUT_SECONDS": "30",
    },
}
with open(cfg, "w") as f:
    json.dump(data, f, indent=2)
print("  Đã merge vào " + cfg + " (đã tạo backup .bak.*).")
PY
  info "Thoát hẳn Claude Desktop (Cmd+Q) rồi mở lại để áp dụng."
}

for t in $TARGETS; do
  echo
  case "$t" in
    code)    install_code ;;
    desktop) install_desktop ;;
  esac
done

echo
bold "Xong."
info "Thử hỏi Claude: \"Tôi là ai trên OpenProject?\" (gọi tool whoami)."
info "Bảo mật: token lưu plaintext trong config — nếu lộ, thu hồi tại My account → Access tokens."

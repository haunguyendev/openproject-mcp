# openproject-mcp

MCP server + plugin Claude (Cowork / Claude Code / Claude Desktop) cho **OpenProject tự host** — quản lý công việc bằng AI: xem/tạo/cập nhật task, gán người, log giờ, báo cáo tiến độ.

> 🔑 **Bảo mật:** repo này **không chứa API key**. File `.mcp.json` chỉ khai báo cách chạy server; key được đọc từ **biến môi trường shell** (`OPENPROJECT_API_KEY`) — mỗi người dùng key riêng, không secret nào lên git.

## Cấu trúc

```
openproject-mcp/
├── .claude-plugin/
│   ├── plugin.json                  # Manifest plugin
│   └── marketplace.json             # Cho phép cài qua /plugin marketplace
├── .mcp.json                        # Khai báo MCP server (không chứa secret)
├── server/server.py                 # MCP server Python (FastMCP, PEP 723)
├── skills/openproject-manager/      # Skill hướng dẫn workflow cho Claude
├── pyproject.toml                   # Cấu hình ruff (dev)
├── CHANGELOG.md
└── LICENSE                          # MIT
```

## Các tool (16)

| Nhóm | Tool |
|---|---|
| Work packages | `list_work_packages`, `get_work_package`, `create_work_package`, `update_work_package`, `add_comment` |
| Dự án & thành viên | `list_projects`, `list_project_members`, `whoami` |
| Metadata | `list_types`, `list_statuses`, `list_priorities` |
| Time tracking | `log_time`, `list_time_entries` |
| Báo cáo | `report_overdue`, `report_my_tasks`, `report_project_progress` |

## Cài đặt

### 1. Yêu cầu

- [`uv`](https://docs.astral.sh/uv/) — tự cài dependency (`mcp`, `httpx`) từ metadata PEP 723:

  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- API key OpenProject: đăng nhập → avatar → **My account → Access tokens → API**.

### 2. Cấu hình API key

Thêm vào `~/.zshrc` (hoặc `~/.bashrc`):

```sh
export OPENPROJECT_API_KEY="<api-key-của-bạn>"
```

Mở Terminal mới (hoặc `source ~/.zshrc`) để biến có hiệu lực. Server đọc key từ môi trường — không cần sửa file nào trong repo.

| Biến | Ý nghĩa | Nguồn | Mặc định |
|---|---|---|---|
| `OPENPROJECT_API_KEY` | API key cá nhân (**bắt buộc**) | Shell env (`~/.zshrc`) | — |
| `OPENPROJECT_URL` | URL OpenProject | `.mcp.json` | `https://manage.promete.ai` |
| `OPENPROJECT_TIMEOUT_SECONDS` | Timeout request | `.mcp.json` | `30` |

> Muốn trỏ sang OpenProject khác? Sửa `OPENPROJECT_URL` trong `.mcp.json` hoặc export biến cùng tên trong shell.

> API v3 của OpenProject dùng Basic Auth với username `apikey`, password = API key — server xử lý sẵn.

### 3a. Dùng với Claude Code

**Thử nhanh (không cài):**

```sh
cd /thư/mục/chứa/plugin
claude --plugin-dir ./openproject-mcp
```

**Cài cố định từ repo (khuyến nghị cho team):** repo này đồng thời là marketplace (có sẵn `.claude-plugin/marketplace.json`). Trong Claude Code:

```
/plugin marketplace add haunguyendev/openproject-mcp
/plugin install openproject-mcp@promete-plugins
```

Plugin lấy API key từ biến môi trường (xem mục **2. Cấu hình API key**) — chỉ cần đã `export OPENPROJECT_API_KEY` trong shell là chạy được ngay, không phải sửa file nào sau khi cài.

Kiểm tra: gõ `/mcp` → server `openproject` hiện **connected** → hỏi "Tôi là ai trên OpenProject?". Lần khởi động đầu hơi chậm do `uv` tải thư viện.

### 3b. Dùng với Claude Desktop

Settings → Developer → Edit Config, thêm vào `claude_desktop_config.json` (thay đường dẫn tuyệt đối và key của bạn):

```json
{
  "mcpServers": {
    "openproject": {
      "command": "/đường/dẫn/tới/uv",
      "args": ["run", "--script", "/đường/dẫn/tới/openproject-mcp/server/server.py"],
      "env": {
        "OPENPROJECT_URL": "https://your-openproject.example.com",
        "OPENPROJECT_API_KEY": "<api-key>",
        "OPENPROJECT_TIMEOUT_SECONDS": "30"
      }
    }
  }
}
```

Khởi động lại app, hỏi thử: **"Tôi là ai trên OpenProject?"** → Claude gọi `whoami`.

## Ví dụ câu lệnh

- "Hôm nay tôi cần làm gì?" / "Việc nào của tôi sắp đến hạn?"
- "Có task nào quá hạn trong dự án Website không?"
- "Tạo task 'Fix lỗi login' trong dự án ABC, gán cho Nam, hạn thứ Sáu"
- "Chuyển task #123 sang In progress và log 2 tiếng"
- "Báo cáo tiến độ dự án XYZ" / "Tuần này tôi đã log bao nhiêu giờ?"

## Phát triển

```sh
uvx ruff check server/   # lint
uvx ruff format server/  # format
```

Quy tắc thiết kế tool: tên động từ rõ ràng, docstring tiếng Việt mô tả từng tham số (Claude đọc docstring để biết cách gọi), kết quả JSON rút gọn các trường hữu ích kèm `url` để mở trực tiếp.

## Bảo mật

- `.mcp.json` **không chứa key** — chỉ khai báo cách chạy server; API key đọc từ biến môi trường shell. Kiểm tra không lọt secret: `git grep -iE "api[_-]?key.*[a-f0-9]{40}" $(git rev-list --all)` phải rỗng.
- Key không bao giờ được in ra log hay kết quả tool.
- Nếu key từng bị lộ (dán vào chat, commit nhầm...), thu hồi ngay tại **My account → Access tokens** và tạo key mới.

## Giấy phép

MIT — xem [LICENSE](LICENSE).

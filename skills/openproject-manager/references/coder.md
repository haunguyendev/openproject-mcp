# Coder — bug, subtask, quan hệ, version

Mục tiêu: quản lý bug/feature của mình, subtask, quan hệ giữa việc, ước lượng, version/sprint.

## Câu hỏi thường gặp → tool

| Người dùng hỏi | Tool |
|---|---|
| "Bug đang mở của tôi" | `list_types` (lấy id Bug) → `list_work_packages(assignee_me=true, type_id=<Bug>)` |
| "Việc trong version/sprint hiện tại" | `list_versions(project)` → `list_work_packages(project, version_id=...)` |
| "Tạo subtask dưới #100" | `create_work_package(project, subject, parent_id=100)` |
| "Subtask của #100" | `list_children(100)` |
| "Cái gì chặn #123 / quan hệ của #123" | `get_relations(123)` |
| "Đánh dấu #123 chặn #150" | `create_relation(from_id=123, to_id=150, relation_type="blocks")` |
| "Ước lượng vs thực tế #123" | `get_work_package(123)` (estimated_time / spent_time) |
| "Chuyển bug qua workflow" | `list_statuses` → `get_work_package` → `update_work_package(status_id=...)` |

## Loại quan hệ (create_relation)

`relates, blocks, blocked, precedes, follows, includes, partof, requires, required, duplicates, duplicated`.

## Quy tắc

- Tạo subtask/relation = GHI → xác nhận trước (nêu rõ cha/con hoặc hai đầu quan hệ).
- Liên kết commit/PR: OpenProject có tích hợp Git riêng; nếu chưa cấu hình, dán link vào `add_comment`.
- Nhóm kết quả theo type hoặc version cho dễ đọc.

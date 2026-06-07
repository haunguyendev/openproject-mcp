# Coder — bug, subtask, quan hệ, version

Mục tiêu: quản lý bug/feature của mình, subtask, quan hệ giữa việc, ước lượng, version/sprint.

## Câu hỏi thường gặp → tool

| Người dùng hỏi | Tool |
|---|---|
| "Bug đang mở của tôi" | `list_types` (lấy id Bug) → `list_work_packages(assignee_me=true, type_id=<Bug>)` |
| "Việc trong version/sprint hiện tại" | `list_versions(project)` → `list_work_packages(project, version_id=...)` |
| "Tạo subtask dưới #100" | `create_work_package(project, subject, type="Task", parent_id=100)` |
| "Chuyển #50 thành con của #100" | `update_work_package(50, parent_id=100)` (không cần get/lock_version) |
| "Subtask của #100" | `list_children(100)` |
| "Cái gì chặn #123 / quan hệ của #123" | `get_relations(123)` |
| "Xem đầy đủ #123 (con + quan hệ + cha) trong một lần" | `get_work_package(123, include=["children","relations"])` |
| "Đánh dấu #123 chặn #150" | `create_relation(from_id=123, to_id=150, relation_type="blocks")` |
| "Tạo loạt subtask dưới #100" | `bulk_create_work_packages(project, items=[{subject, type, parent_id:100}, ...])` (đọc `failed` sau) |
| "Ước lượng vs thực tế #123" | `get_work_package(123)` (estimated_time / spent_time) |
| "Chuyển bug qua workflow" | `update_work_package(123, status="In progress")` (nhận tên, tự lấy lock_version) |
| "Lịch sử/bình luận của #123" | `list_activities(123)` |
| "Sửa custom field của #123" | `get_work_package(123)` (xem `custom_fields`) → `update_work_package(123, custom_fields={...})` |

## Loại quan hệ (create_relation)

`relates, blocks, blocked, precedes, follows, includes, partof, requires, required, duplicates, duplicated`.

## Relations — quy tắc

- **Hướng:** `create_relation(from_id, to_id, "blocks")` nghĩa là `from` **CHẶN** `to`. Tương tự `precedes` = `from` đi **trước** `to`. Nói rõ hướng cho người dùng trước khi tạo (ai chặn ai / cái nào trước).
- **Một chiều:** OpenProject **tự tạo nghịch đảo** (tạo `blocks` thì đầu kia tự thấy `blocked`). Chỉ tạo **một** chiều — đừng tạo cả `blocks` lẫn `blocked` cho cùng cặp.
- **Lịch trình:** `precedes`/`follows` có thể **dời start/due date** của các việc liên quan (scheduling). Cảnh báo người dùng khả năng đổi ngày **trước** khi tạo.
- **Kiểm tra trùng trước:** gọi `get_relations(from_id)` trước khi tạo để tránh trùng và giải thích cho người dùng. (Tool cũng tự chặn self-relation, trùng cặp, ngược chiều và vòng lặp trực tiếp — nếu bị từ chối, đọc thông báo và báo lại.)
- **Vòng lặp nhiều nút** (A→B→C→A) không được kiểm phía client — nếu API từ chối, báo lại nguyên văn lỗi.

## Lấy gộp ngữ cảnh (include)

- `get_work_package(wp_id)` mặc định luôn trả `parent_id` + `parent_subject` (None nếu là WP gốc) — không cần đọc mô tả để biết cha.
- Cần hiểu đầy đủ một việc → `get_work_package(wp_id, include=["children","relations"])` gộp con (đầy đủ trường) + quan hệ vào **một** response, thay vì gọi riêng `list_children` và `get_relations`. Truyền chỉ phần cần (`["children"]` hoặc `["relations"]`) để khỏi tốn call thừa; giá trị lạ sẽ báo lỗi.

## Subtask / parent

- Tạo subtask: `create_work_package(project, subject, parent_id=...)`. Di chuyển task có sẵn thành con của task khác: `update_work_package(wp_id, parent_id=...)` (không cần lấy `lock_version` thủ công — tool tự lấy + tự retry 409 một lần).
- Khuyến nghị cha **cùng project** với con. Cấu hình OpenProject có thể từ chối cha khác project — nếu bị từ chối, báo lại rõ và gợi ý cùng project.
- **Phân tầng theo chuẩn Scrum** (Epic→Story→Task, auto-map type, validate cha-con): xem `references/work-package-hierarchy.md`.

## Custom fields

- Xem giá trị: `get_work_package` trả về `custom_fields` (nếu có), key dạng `customFieldN`.
- Ghi theo ID: `custom_fields={"1": "Foo", "2": 42}`. Trường **liên kết** (user/version/list) truyền **href**, vd `{"3": "/api/v3/users/14"}`.
- Không chắc N là gì → xem trước bằng `get_work_package`; tên người-đọc của field phải tra schema (chưa expose), nên dựa vào ID quan sát được.

## Quy tắc chung

- Tạo subtask/relation = GHI → xác nhận trước (nêu rõ cha/con hoặc hai đầu quan hệ).
- **Hàng loạt:** khi tạo nhiều subtask, dùng `bulk_create_work_packages` (một call, `parent_id` trỏ việc đã có) thay vì gọi lẻ; khi đóng/đổi nhiều việc, dùng `bulk_update_work_packages`. **Tóm tắt cây** (cha → các con; các cặp quan hệ + hướng) và xác nhận **một lần** trước khi chạy loạt; đọc `failed` trong kết quả để xử lý phần lỗi.
- **Cắt bớt (truncation):** `list_children` tối đa 100 con; `get_relations` không phân trang — nếu chạm mốc, nói rõ "có thể còn nữa".
- Liên kết commit/PR: OpenProject có tích hợp Git riêng; nếu chưa cấu hình, dán link vào `add_comment`.
- Nhóm kết quả theo type hoặc version cho dễ đọc.

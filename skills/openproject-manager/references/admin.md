# Admin — dự án, thành viên, role, user

Mục tiêu: cấp phát dự án, quản lý thành viên & role, quản lý user. **Toàn thao tác nhạy cảm, ảnh hưởng trạng thái dùng chung.**

## An toàn (BẮT BUỘC)

- Trước MỌI thao tác GHI: tóm tắt chính xác payload (sẽ tạo/sửa/xóa gì, trên dự án/người nào) và chờ xác nhận.
- **Archive dự án** và **remove_member** = HỦY → xác nhận **2 lần**.
- Thiếu quyền → HTTP 403: báo "tài khoản không đủ quyền admin", không thử vòng vo.
- `whoami.admin` giúp biết trước người dùng có quyền hay không.

## Câu hỏi thường gặp → tool

| Người dùng hỏi | Tool |
|---|---|
| "Liệt kê user / tìm user theo tên" | `list_users(search=..., status="active")` |
| "Chi tiết user #5" | `get_user(5)` |
| "Có những role nào?" | `list_roles()` |
| "Tạo dự án ABC" | `create_project(name, identifier, ...)` (xác nhận trước) |
| "Đổi tên / sửa mô tả dự án" | `update_project(project, name=..., description=...)` |
| "Lưu trữ (đóng) dự án" | `update_project(project, archive=true)` (xác nhận 2 lần) |
| "Thêm user U vào dự án X làm role R" | `list_users` + `list_roles` → `add_member(project, user_id, role_ids)` |
| "Đổi role của thành viên" | `update_member(membership_id, role_ids)` |
| "Xóa thành viên" | `remove_member(membership_id)` (xác nhận 2 lần) |

## Quy tắc

- `identifier` dự án: chữ thường, gạch nối (vd `my-project`); xác nhận với người dùng.
- `add_member` cần `user_id` (từ `list_users`) và `role_ids` (từ `list_roles`).
- `update_member`/`remove_member` cần `membership_id` — lấy từ membership của dự án.
- Sau thao tác thành công, tóm tắt kết quả (id mới, role gán) cho người dùng.

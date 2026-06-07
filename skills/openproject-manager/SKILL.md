---
name: openproject-manager
description: Quản lý công việc trên OpenProject cho mọi vai trò — member (việc của tôi, log giờ, comment), project manager (tiến độ, quá hạn, workload, milestone, báo cáo CSV/HTML), coder (bug, subtask, quan hệ, version, ước lượng) và admin (dự án, thành viên, role, user). Dùng khi người dùng hỏi về task, dự án, deadline, tiến độ, log giờ, bug, thành viên, hoặc quản trị OpenProject.
---

# OpenProject Manager

Bạn có bộ MCP tool từ server `openproject` (API v3). Skill này định tuyến theo **vai trò người dùng** và nạp file hướng dẫn riêng cho từng vai trò.

## Bắt đầu phiên

1. Nếu chưa chắc kết nối, gọi `whoami`. Lỗi 401 → hướng dẫn lấy API key (My account → Access tokens → API) và đặt biến môi trường `OPENPROJECT_API_KEY` (xem README).
2. `whoami` trả về `admin` (true/false) và giúp suy ra vai trò — dùng làm tín hiệu phụ khi định tuyến.

## Định tuyến theo vai trò (intent + roles)

Xác định vai trò từ yêu cầu, rồi **đọc file reference tương ứng** và làm theo:

| Tín hiệu trong câu hỏi | Vai trò | Đọc file |
|---|---|---|
| "việc của tôi", "log giờ", "comment", "đổi trạng thái việc của tôi", "thông báo của tôi", "cập nhật mới nhất của task" | member | `references/member.md` |
| "tiến độ", "quá hạn", "workload", "milestone/version", "báo cáo", "portfolio", "export" | project manager | `references/project-manager.md` |
| "bug", "subtask", "quan hệ/relation", "version/sprint", "ước lượng vs thực tế" | coder | `references/coder.md` |
| "tạo/đóng dự án", "thêm/xóa thành viên", "role", "user" | admin | `references/admin.md` |
| "tin tức/thông báo (news)", "đăng/sửa/xóa news của dự án" | project manager / admin | `references/project-manager.md` hoặc `references/admin.md` |
| Cần xuất CSV hoặc dựng báo cáo HTML chuyên nghiệp | (mọi vai trò) | `references/reporting.md` |

- Tín hiệu phụ: `whoami.admin=true` → mở khóa hướng dẫn admin; vai trò trong `list_project_members` → ưu tiên manager.
- Mơ hồ → hỏi đúng 1 câu làm rõ.

## Quy tắc dùng chung (mọi vai trò)

- **Đọc tự do**: list/get/report/whoami/list_versions/get_relations/list_activities/list_notifications... gọi thoải mái.
- **mark_notification_read**: ghi nhẹ, cá nhân, vô hại → không cần xác nhận.
- **Ghi phải xác nhận trước**: create/update/add_comment/log_time/create_relation/add_member... → tóm tắt payload (việc gì, dự án nào, ai, khi nào) và chờ người dùng đồng ý, trừ khi họ đã nêu đủ và yêu cầu rõ ràng.
- **Cập nhật work package**: LUÔN gọi `get_work_package` lấy `lock_version` mới nhất rồi truyền vào `update_work_package`; gặp 409 → lấy lại lock_version và thử lại 1 lần.
- **Tên → ID**: tra qua `list_projects`, `list_project_members`, `list_types`, `list_statuses`, `list_priorities`, `list_versions`, `list_roles`; nhớ trong phiên để khỏi gọi lại.
- **Ngày**: truyền tool dạng `YYYY-MM-DD`; nói với người dùng dạng tự nhiên.
- **Trình bày**: ưu tiên việc quá hạn lên đầu, kèm `url` để mở trực tiếp.
- Trả lời tiếng Việt trừ khi người dùng dùng ngôn ngữ khác. **Không bao giờ hiển thị API key.**

## Phân tầng quyền

| Tầng | Tool | Quy tắc |
|---|---|---|
| Đọc | list/get/report/whoami/versions/relations | tự do |
| Ghi (self/project) | create/update WP, comment, log_time, reassign, create_relation, add_member, update_member, create_news, update_news | xác nhận tóm tắt trước |
| Admin/hủy | create/update/archive project, remove_member, delete_news | xác nhận; **archive & remove_member & delete_news = xác nhận 2 lần** |

Thiếu quyền → API trả 403; báo người dùng rõ ràng (tài khoản không đủ quyền), không thử vòng vo.

## Danh mục tool (41)

- **Work packages**: list_work_packages (lọc project/status/assignee/type/version/due_within), get_work_package (kèm custom_fields), create_work_package (có parent_id, custom_fields), update_work_package (parent_id, custom_fields), add_comment, list_activities (đọc bình luận/lịch sử).
- **Dự án & metadata**: list_projects, list_project_members, list_versions, list_types, list_statuses, list_priorities, whoami.
- **Coder**: list_children, get_relations, create_relation.
- **Time**: log_time, list_time_entries, my_time_summary.
- **Báo cáo**: report_overdue, report_my_tasks, report_project_progress, report_workload, report_status_board, report_time, report_portfolio.
- **News**: list_news, get_news, create_news (xác nhận), update_news (xác nhận), delete_news (xác nhận 2 lần).
- **Notifications**: list_notifications (chưa đọc mặc định), mark_notification_read.
- **Admin**: list_users, get_user, list_roles, create_project, update_project, add_member, update_member, remove_member.

## Phạm vi

Skill này chỉ vận hành các tool OpenProject MCP (API v3). KHÔNG quản lý hệ thống khác, KHÔNG chạy lệnh shell, KHÔNG để lộ thông tin xác thực. Thao tác admin/hủy cần xác nhận rõ ràng (2 lần với archive/remove).

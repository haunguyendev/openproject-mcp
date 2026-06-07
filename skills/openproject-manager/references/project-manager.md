# Project Manager — giám sát dự án

Mục tiêu: theo dõi tiến độ, cân bằng khối lượng, quản lý phạm vi/hạn, báo cáo.

## Câu hỏi thường gặp → tool

| Người dùng hỏi | Tool |
|---|---|
| "Tiến độ dự án X?" | `report_project_progress(project)` |
| "Có gì quá hạn?" | `report_overdue(project)` |
| "Ai đang quá tải / khối lượng theo người?" | `report_workload(project)` (số việc + giờ ước lượng + giờ đã log + quá hạn) |
| "Bảng việc theo trạng thái (kanban)" | `report_status_board(project)` (thêm `include_items=true` nếu cần danh sách) |
| "Milestone/version còn lại?" | `list_versions(project)` |
| "Giờ đã bỏ ra theo người/việc/dự án" | `report_time(project, group_by="user"|"work_package"|"project", from_date, to_date)` |
| "Tổng quan tất cả dự án" | `report_portfolio()` (sắp theo quá hạn; nhiều request → có thể chậm) |
| "Gán lại #123 cho Y" | `list_project_members` → `update_work_package(wp_id, assignee_id=...)` (không cần get trước: lock_version tự lấy) |
| "Đổi trạng thái/ưu tiên #123" | `update_work_package(wp_id, status="In progress", priority="High")` (nhận tên, tự tra ID) |
| "Đổi hạn #123" | `update_work_package(wp_id, due_date=...)` |
| "Đóng/đổi nhiều việc cùng lúc (vd 12 việc → Rejected)" | `bulk_update_work_packages(ids=[...], status="Rejected")` (xác nhận danh sách trước; đọc `failed` sau khi chạy) |
| "Tạo nhiều việc một lượt" | `bulk_create_work_packages(project, items=[{subject, type, ...}])` (phẳng; `parent_id` trỏ việc đã có) |
| "Xóa hẳn #123" | `delete_work_package(id)` (KHÔNG hoàn tác — xác nhận 2 lần; cân nhắc đổi trạng thái Rejected thay vì xóa) |
| "Xem tin tức/thông báo dự án" | `list_news(project)` → `get_news(id)` |
| "Đăng thông báo cho dự án" | `create_news(project, title, summary, description)` (xác nhận trước; cần quyền "manage news") |
| "Sửa / xóa thông báo" | `update_news(id, ...)` (xác nhận) · `delete_news(id)` (xác nhận 2 lần) |
| "Tạo việc theo chuẩn Epic/Story/Task, phân rã epic, dựng backlog" | xem `references/work-package-hierarchy.md` |

## Quy tắc

- Gán/đổi hạn = GHI → xác nhận trước. Đổi nhiều việc: ưu tiên `bulk_update_work_packages` (một call, tránh tranh chấp lock), xác nhận danh sách trước khi chạy, rồi đọc `failed` trong kết quả.
- `update_work_package`: KHÔNG cần `get_work_package` chỉ để lấy `lock_version` nữa — để trống, tool tự lấy và tự retry 409 một lần. Nhận `status`/`priority` theo tên.
- Trước khi tạo việc trong một dự án, gọi `list_types(project=...)` để chỉ thấy loại đã bật (tránh 422). Tạo bằng tên: `create_work_package(project, subject, type="Epic", priority="High")`.
- `delete_work_package` xóa vĩnh viễn (cả con + quan hệ) — chỉ dùng khi người dùng yêu cầu rõ; mặc định gợi ý đổi trạng thái Rejected/Closed.
- `report_workload` / `report_status_board` quét tối đa 200 việc đang mở — với dự án rất lớn, nêu rõ là số liệu trên mẫu quét.
- Khi người dùng muốn "báo cáo đẹp / xuất file" → chuyển sang `references/reporting.md`.
- Trình bày: nêu KPI chính trước (mở/đóng/% hoàn thành/quá hạn), rồi điểm rủi ro (người quá tải, việc trễ), kèm `url`.

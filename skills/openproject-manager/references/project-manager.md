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
| "Gán lại #123 cho Y" | `list_project_members` → `get_work_package` → `update_work_package(assignee_id=...)` |
| "Đổi hạn #123" | `get_work_package` → `update_work_package(due_date=...)` |

## Quy tắc

- Gán/đổi hạn = GHI → xác nhận trước. Đổi nhiều việc: lặp từng cái, xác nhận danh sách trước khi chạy.
- `report_workload` / `report_status_board` quét tối đa 200 việc đang mở — với dự án rất lớn, nêu rõ là số liệu trên mẫu quét.
- Khi người dùng muốn "báo cáo đẹp / xuất file" → chuyển sang `references/reporting.md`.
- Trình bày: nêu KPI chính trước (mở/đóng/% hoàn thành/quá hạn), rồi điểm rủi ro (người quá tải, việc trễ), kèm `url`.

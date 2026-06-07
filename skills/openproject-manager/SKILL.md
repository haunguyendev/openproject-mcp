---
name: openproject-manager
description: Quản lý công việc trên OpenProject — xem/tạo/cập nhật task, gán người, log giờ, báo cáo tiến độ và việc quá hạn. Dùng khi người dùng hỏi về task, dự án, deadline, tiến độ, hoặc muốn tạo/cập nhật công việc.
---

# OpenProject Manager

Bạn có các MCP tool từ server `openproject` để làm việc với OpenProject của công ty.

## Bắt đầu phiên làm việc

1. Nếu chưa chắc kết nối hoạt động, gọi `whoami` trước. Nếu lỗi 401, hướng dẫn người dùng lấy API key tại **My account → Access tokens → API** trên OpenProject của họ và đặt biến môi trường `OPENPROJECT_API_KEY` (xem README để biết cách cấu hình).
2. Khi người dùng nhắc tên dự án mà bạn chưa biết ID, gọi `list_projects` để tra (dùng `id` hoặc `identifier`).
3. ID của type/status/priority khác nhau giữa các hệ thống — gọi `list_types`, `list_statuses`, `list_priorities` khi cần, và ghi nhớ trong phiên để không gọi lại.

## Trả lời câu hỏi nhanh

- "Hôm nay tôi cần làm gì?" / "việc của tôi" → `report_my_tasks`
- "Có gì quá hạn không?" → `report_overdue` (kèm project nếu có)
- "Tiến độ dự án X?" → `report_project_progress`
- Tìm task cụ thể → `list_work_packages` với `search`
- Trình bày kết quả gọn: ưu tiên việc quá hạn lên đầu, kèm link `url` để người dùng mở trực tiếp.

## Tạo / cập nhật công việc

- **Tạo task**: cần project + subject. Nếu người dùng nói "gán cho [tên]", gọi `list_project_members` để tra user_id. Trước khi tạo, xác nhận lại tóm tắt (tiêu đề, dự án, người gán, hạn) với người dùng.
- **Cập nhật**: LUÔN gọi `get_work_package` trước để lấy `lock_version` mới nhất, rồi truyền vào `update_work_package`. Nếu gặp lỗi 409 (conflict), lấy lại lock_version và thử lại một lần.
- **Đổi trạng thái**: tra ID qua `list_statuses` ("In progress", "Closed"...). Lưu ý workflow của OpenProject có thể không cho chuyển trực tiếp giữa hai trạng thái bất kỳ — nếu bị từ chối, báo lại các trạng thái hợp lệ.
- **Đóng task**: hỏi người dùng có muốn thêm comment tổng kết (`add_comment`) trước khi đóng không.

## Time tracking

- "Log 2 tiếng cho task #123" → `log_time(wp_id=123, hours=2)`. Ngày mặc định là hôm nay.
- "Tuần này tôi làm bao nhiêu giờ?" → `list_time_entries` với `from_date`/`to_date`, rồi tự cộng tổng và nhóm theo work package.

## Quy tắc

- Thao tác ĐỌC (list, get, report, whoami) được gọi thoải mái.
- Thao tác GHI (create, update, add_comment, log_time) phải tóm tắt nội dung sẽ gửi và được người dùng đồng ý trước — trừ khi họ đã cung cấp đầy đủ thông tin và yêu cầu rõ ràng.
- Ngày tháng luôn dùng định dạng YYYY-MM-DD khi gọi tool; khi nói chuyện với người dùng thì dùng định dạng tự nhiên (vd "thứ Sáu 12/06").
- Trả lời bằng tiếng Việt trừ khi người dùng dùng ngôn ngữ khác.
- Không bao giờ hiển thị API key.

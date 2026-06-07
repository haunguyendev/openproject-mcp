# Member — làm việc của tôi

Mục tiêu: xem việc được giao, cập nhật tiến độ, log giờ, trao đổi. Hầu hết thao tác là của chính mình.

## Câu hỏi thường gặp → tool

| Người dùng hỏi | Tool |
|---|---|
| "Hôm nay tôi làm gì?" / "việc của tôi" | `report_my_tasks` |
| "Việc của tôi sắp đến hạn (tuần này)?" | `list_work_packages(assignee_me=true, due_within_days=7)` |
| "Tìm task X của tôi" | `list_work_packages(assignee_me=true, search="X")` |
| "Chuyển #123 sang In progress" | `list_statuses` → `get_work_package(123)` (lấy lock_version) → `update_work_package(123, lock_version, status_id=...)` |
| "Đánh dấu #123 xong" | `update_work_package(..., status_id=<Closed>)` hoặc `done_ratio=100` |
| "Log 2 tiếng cho #123" | `log_time(wp_id=123, hours=2)` (ngày mặc định hôm nay) |
| "Tuần này tôi log bao nhiêu giờ?" | `my_time_summary(from_date, to_date)` |
| "Bình luận vào #123" | `add_comment(123, "...")` |
| "Cập nhật/thảo luận mới nhất của #123?" | `list_activities(123)` (đọc bình luận + thay đổi) |
| "Thông báo của tôi" / "có gì mới chưa đọc?" | `list_notifications()` (chưa đọc mặc định) |
| "Đánh dấu thông báo #5 đã đọc" | `mark_notification_read(5)` |

## Quy tắc

- Cập nhật trạng thái: tra ID qua `list_statuses`. Workflow OpenProject có thể chặn vài chuyển tiếp — nếu bị từ chối, báo lại các trạng thái hợp lệ.
- Mọi thao tác GHI (update/log_time/comment) → tóm tắt ngắn rồi xác nhận, trừ khi người dùng đã yêu cầu rõ.
- Trình bày việc quá hạn lên đầu, kèm `url`.

# Reporting — CSV + báo cáo HTML chuyên nghiệp

Khi người dùng muốn "báo cáo đẹp", "xuất file", hoặc trình bày số liệu kiểu data analyst. Dữ liệu lấy từ các report tool (JSON); skill này biến nó thành CSV và/hoặc HTML.

## Quy trình

1. **Thu thập số liệu** bằng đúng report tool:
   - Tiến độ: `report_project_progress`, `report_overdue`.
   - Khối lượng: `report_workload`.
   - Trạng thái: `report_status_board`.
   - Thời gian: `report_time`, `my_time_summary`.
   - Đa dự án: `report_portfolio`.
2. **Nêu rõ phạm vi**: dự án nào, khoảng thời gian nào, ngày chạy. Chỉ dùng số tool trả về — KHÔNG bịa số.
3. **Chọn định dạng đầu ra** theo yêu cầu: CSV, HTML, hoặc cả hai.

## CSV

- Ghi file `.csv` (vd `report-<project>-<YYYYMMDD>.csv`), 1 dòng / work package (hoặc / người / time entry tùy báo cáo).
- Header rõ ràng; số dạng thuần để mở bằng Excel/Sheets.

## HTML (kiểu data analyst)

Trang HTML tự chứa (self-contained), không gọi mạng ngoài:

- **Header + KPI cards**: tổng việc, đang mở, % hoàn thành, quá hạn, tổng giờ.
- **Bảng**: workload theo người, việc quá hạn (sắp theo hạn), phân bố theo trạng thái.
- **Biểu đồ đơn giản**: status mix (bar/donut), workload theo người (bar), xu hướng nếu có — dùng inline SVG hoặc thư viện chart nhẹ qua CDN nếu được phép.
- Typography sạch, in được, màu nhấn cho rủi ro (đỏ = quá hạn).
- Footer: nguồn dữ liệu + thời điểm tạo.

## Tận dụng công cụ sẵn có

Nếu môi trường có sẵn, ưu tiên `/ck:preview --html` hoặc skill `show-off` để dựng HTML chất lượng cao thay vì viết tay từ đầu. Nếu không, tự sinh một file HTML tĩnh gọn gàng.

## Nguyên tắc

- Trung thực số liệu: không nội suy/đoán; nếu báo cáo quét giới hạn (vd tối đa 200 việc / 25 dự án), ghi chú rõ.
- Luôn cho người dùng biết file được lưu ở đâu.

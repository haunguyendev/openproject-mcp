# Phân tầng công việc chuẩn Scrum (Epic / Story / Task)

Mục tiêu: giúp PM và coder tạo work package **đúng loại (type)** và **đúng phân tầng cha-con** theo chuẩn Agile/Scrum, thay vì tạo task "lơ lửng" không có type hoặc đặt sai cấp.

Dùng khi người dùng nói: "tạo epic/story/task", "phân rã/breakdown epic", "dựng backlog/sprint", "tạo việc theo chuẩn".

> Đây là **lớp quy ước (advisory)**. OpenProject **không** tự ép luật này — Claude tuân theo để gợi ý đúng, nhưng nếu người dùng cố ý làm khác thì vẫn cho phép (cảnh báo trước).

## Cây phân tầng chuẩn

```
Epic                      (cấp cao nhất, không có parent)
 └─ User Story | Feature  (parent = Epic)
     └─ Task | Bug        (parent = Story/Feature)
         └─ Sub-task      (parent = Task, tùy chọn)
```

- **Epic**: mục tiêu/khối lớn, kéo dài nhiều sprint.
- **User Story / Feature**: một mẩu giá trị cho người dùng, vừa một sprint.
- **Task / Bug**: việc kỹ thuật cụ thể để hoàn thành Story.
- **Sub-task**: chia nhỏ Task khi cần.

## Auto-map type (loại của instance → vai trò Scrum)

Tên type do admin cấu hình từng instance, có thể không trùng tên chuẩn. Trước khi tạo, **discover** rồi map theo tên (không phân biệt hoa/thường):

1. Gọi `list_types(project=<id>)` khi đã biết dự án (chỉ trả type **đã bật** trong dự án → tránh lỗi 422). Chưa biết dự án thì `list_types()` toàn hệ thống.
2. Map tên chứa từ khóa sang vai trò:

| Vai trò Scrum | Tên type chứa | Fallback nếu thiếu |
|---|---|---|
| Epic | `epic` | `phase`; vẫn không có → báo người dùng tạo type "Epic" trong admin |
| Story | `user story`, `story` | `feature` |
| Task | `task`, `công việc` | type mặc định của dự án |
| Bug | `bug`, `defect`, `lỗi` | (bỏ qua nếu instance không có) |

3. **Mơ hồ** (không khớp / tên lạ / nhiều type khớp): hỏi người dùng xác nhận mapping **đúng 1 lần**, rồi **nhớ trong phiên**.
4. **Nhớ trong phiên**: lưu kết quả `list_types` + mapping đã chốt để khỏi gọi lại.

## Recipe tạo

Tất cả thao tác tạo = GHI → tóm tắt và xác nhận trước (theo quy tắc chung ở `SKILL.md`).

`create_work_package` nhận **type theo tên** (`type="Epic"`) và tự khớp theo loại đã bật trong dự án — khỏi phải tra `type_id` thủ công. Vẫn dùng quy trình auto-map ở trên khi tên type của instance lạ/mơ hồ (hỏi xác nhận 1 lần).

| Việc | Các bước |
|---|---|
| Tạo Epic | `create_work_package(project, subject, type="Epic")` (không `parent_id`). |
| Tạo Story dưới Epic #X | `get_work_package(X)` xác minh #X là Epic → `create_work_package(project, subject, type="User story", parent_id=X)`. |
| Tạo Task dưới Story #Y | `get_work_package(Y)` xác minh #Y là Story/Feature → `create_work_package(project, subject, type="Task", parent_id=Y)`. |
| Breakdown Epic #X | tạo nhiều Story dưới #X bằng `bulk_create_work_packages(project, items=[{subject, type:"User story", parent_id:X}, ...])`: **tóm tắt cây và xác nhận MỘT lần** trước khi chạy. |

Cơ chế subtask/parent, re-parent (`update_work_package(parent_id=...)`), và quy tắc xác nhận hàng loạt: xem `references/coder.md` (mục "Subtask / parent" và "Quy tắc chung") — **không lặp lại ở đây**.

## Dựng cả cây trong vài call (bulk theo tầng)

Không có một tool "tạo cả cây" — dựng **theo tầng**, dùng id trả về của tầng trên làm `parent_id` cho tầng dưới (vì `bulk_create_work_packages` là **phẳng**: `parent_id` chỉ trỏ việc đã tồn tại, không tham chiếu việc tạo cùng lần gọi):

1. Tạo Epic: `create_work_package(project, subject, type="Epic")` → lấy `id` (vd #500).
2. Tạo loạt Story dưới Epic: `bulk_create_work_packages(project, items=[{subject, type:"User story", parent_id:500}, ...])` → lấy các id Story từ `created[]`.
3. Tạo loạt Task dưới mỗi Story: lặp `bulk_create_work_packages` với `parent_id` là id Story tương ứng.
4. Quan hệ chéo (blocks/precedes giữa các việc): thêm bằng `create_relation` sau khi đã có id (xem `references/coder.md`).

Tóm tắt toàn cây + xác nhận **một lần** trước khi chạy; sau mỗi loạt đọc `failed` để vá phần lỗi (tạo lại riêng các item thất bại).

## Validate cha-con (advisory)

Trước khi tạo việc con (có `parent_id`):

1. `get_work_package(parent_id)` → lấy type của cha.
2. Map type cha sang vai trò Scrum, đối chiếu cây:
   - Story/Feature → parent nên là **Epic**.
   - Task/Bug → parent nên là **Story/Feature**.
   - Sub-task → parent nên là **Task**.
3. **Lệch cây** (vd định đặt Story dưới Task, hay Task thẳng dưới Epic): **cảnh báo + gợi ý vị trí đúng**. Nếu người dùng vẫn muốn → cho phép (mềm), không chặn.

## Lưu ý

- OpenProject core không lưu luật hierarchy này; mỗi phiên Claude tự áp theo file này.
- Map theo tên có thể sai với instance đặt tên lạ → đã giảm thiểu bằng "hỏi xác nhận 1 lần".
- Nếu tạo việc bị **422** vì type chưa bật trong dự án → dùng `list_types(project=...)` để lấy đúng type đã bật, hoặc nhờ admin bật type trong project settings.

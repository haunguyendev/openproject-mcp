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

| Việc | Các bước |
|---|---|
| Tạo Epic | map type Epic → `create_work_package(project, subject, type_id=<epic>)` (không `parent_id`). |
| Tạo Story dưới Epic #X | `get_work_package(X)` xác minh #X là Epic → `create_work_package(project, subject, type_id=<story>, parent_id=X)`. |
| Tạo Task dưới Story #Y | `get_work_package(Y)` xác minh #Y là Story/Feature → `create_work_package(project, subject, type_id=<task>, parent_id=Y)`. |
| Breakdown Epic #X | tạo nhiều Story dưới #X: **tóm tắt cây (Epic → các Story dự kiến) và xác nhận MỘT lần** trước khi chạy loạt. |

Cơ chế subtask/parent, re-parent (`update_work_package(parent_id=...)`), và quy tắc xác nhận hàng loạt: xem `references/coder.md` (mục "Subtask / parent" và "Quy tắc chung") — **không lặp lại ở đây**.

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

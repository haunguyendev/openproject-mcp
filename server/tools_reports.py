"""Tools: báo cáo — quá hạn, việc của tôi, tiến độ dự án."""

from datetime import date

from app import mcp
from formatters import _fmt_wp, _link_title, _out, iso8601_to_hours
from op_client import _collection


@mcp.tool()
def report_overdue(project: str | None = None) -> str:
    """Báo cáo việc QUÁ HẠN: các work package đang mở có due date đã qua.

    Args:
        project: ID dự án (để trống = mọi dự án).
    """
    filters = [
        {"status": {"operator": "o", "values": []}},
        {"dueDate": {"operator": "<t-", "values": ["1"]}},
    ]
    path = f"/projects/{project}/work_packages" if project else "/work_packages"
    data = _collection(path, filters, page_size=100, sort=[["dueDate", "asc"]])
    items = [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
    return _out({"overdue_total": data.get("total"), "items": items})


@mcp.tool()
def report_my_tasks() -> str:
    """Báo cáo việc CỦA TÔI đang mở, sắp xếp theo hạn chót gần nhất."""
    filters = [
        {"status": {"operator": "o", "values": []}},
        {"assignee": {"operator": "=", "values": ["me"]}},
    ]
    data = _collection("/work_packages", filters, page_size=100, sort=[["dueDate", "asc"]])
    items = [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
    today = date.today().isoformat()
    overdue = [i for i in items if i["due_date"] and i["due_date"] < today]
    return _out({"total_open": data.get("total"), "overdue_count": len(overdue), "items": items})


@mcp.tool()
def report_project_progress(project: str) -> str:
    """Báo cáo tiến độ một dự án: tổng việc, mở/đóng, quá hạn, phân bố theo người.

    Args:
        project: ID hoặc identifier của dự án.
    """
    path = f"/projects/{project}/work_packages"
    all_data = _collection(path, page_size=1)
    open_data = _collection(path, [{"status": {"operator": "o", "values": []}}], page_size=200)
    open_items = [_fmt_wp(w) for w in open_data.get("_embedded", {}).get("elements", [])]

    today = date.today().isoformat()
    by_assignee: dict[str, int] = {}
    overdue = 0
    for i in open_items:
        name = i["assignee"] or "(chưa gán)"
        by_assignee[name] = by_assignee.get(name, 0) + 1
        if i["due_date"] and i["due_date"] < today:
            overdue += 1

    total = all_data.get("total", 0)
    open_total = open_data.get("total", 0)
    return _out(
        {
            "project": project,
            "total": total,
            "open": open_total,
            "closed": total - open_total,
            "overdue": overdue,
            "open_by_assignee": dict(sorted(by_assignee.items(), key=lambda x: -x[1])),
            "percent_closed": round((total - open_total) / total * 100, 1) if total else None,
        }
    )


@mcp.tool()
def report_workload(project: str) -> str:
    """Khối lượng việc ĐANG MỞ theo từng người: số việc, giờ ước lượng, giờ đã log, quá hạn.

    Args:
        project: ID hoặc identifier của dự án.
    """
    path = f"/projects/{project}/work_packages"
    data = _collection(
        path,
        [{"status": {"operator": "o", "values": []}}],
        page_size=200,
        sort=[["dueDate", "asc"]],
    )
    today = date.today().isoformat()
    by: dict[str, dict] = {}
    for w in data.get("_embedded", {}).get("elements", []):
        name = _link_title(w, "assignee") or "(chưa gán)"
        b = by.setdefault(
            name, {"open": 0, "estimated_hours": 0.0, "spent_hours": 0.0, "overdue": 0}
        )
        b["open"] += 1
        b["estimated_hours"] = round(
            b["estimated_hours"] + iso8601_to_hours(w.get("estimatedTime")), 2
        )
        b["spent_hours"] = round(b["spent_hours"] + iso8601_to_hours(w.get("spentTime")), 2)
        due = w.get("dueDate")
        if due and due < today:
            b["overdue"] += 1
    return _out(
        {
            "project": project,
            "open_total": data.get("total"),
            "by_assignee": dict(sorted(by.items(), key=lambda x: -x[1]["open"])),
        }
    )


@mcp.tool()
def report_status_board(project: str, include_items: bool = False) -> str:
    """Bảng kanban: đếm work package theo từng trạng thái (tùy chọn kèm danh sách việc).

    Args:
        project: ID hoặc identifier của dự án.
        include_items: True = kèm danh sách work package trong mỗi cột (tối đa 200 việc).
    """
    path = f"/projects/{project}/work_packages"
    data = _collection(path, page_size=200, sort=[["status", "asc"]])
    board: dict[str, dict] = {}
    for w in data.get("_embedded", {}).get("elements", []):
        st = _link_title(w, "status") or "(không rõ)"
        col = board.setdefault(st, {"count": 0, "items": []})
        col["count"] += 1
        if include_items:
            col["items"].append(_fmt_wp(w))
    if not include_items:
        for col in board.values():
            del col["items"]
    return _out({"project": project, "scanned": data.get("total"), "by_status": board})


@mcp.tool()
def report_time(
    project: str | None = None,
    group_by: str = "user",
    from_date: str | None = None,
    to_date: str | None = None,
) -> str:
    """Tổng giờ đã log, nhóm theo user / work_package / project.

    Args:
        project: ID dự án (để trống = mọi dự án).
        group_by: "user", "work_package", hoặc "project".
        from_date: Từ ngày YYYY-MM-DD.
        to_date: Đến ngày YYYY-MM-DD.
    """
    link = {"user": "user", "work_package": "workPackage", "project": "project"}.get(
        group_by, "user"
    )
    filters = []
    if project:
        filters.append({"project": {"operator": "=", "values": [str(project)]}})
    if from_date and to_date:
        filters.append({"spentOn": {"operator": "<>d", "values": [from_date, to_date]}})

    data = _collection("/time_entries", filters, page_size=500)
    entries = data.get("_embedded", {}).get("elements", [])
    totals: dict[str, float] = {}
    grand = 0.0
    for t in entries:
        hrs = iso8601_to_hours(t.get("hours"))
        grand += hrs
        key = _link_title(t, link) or "(không rõ)"
        totals[key] = round(totals.get(key, 0.0) + hrs, 2)
    return _out(
        {
            "group_by": group_by,
            "from": from_date,
            "to": to_date,
            "entry_count": len(entries),
            "total_hours": round(grand, 2),
            "totals": dict(sorted(totals.items(), key=lambda x: -x[1])),
        }
    )


@mcp.tool()
def report_portfolio(active_only: bool = True, max_projects: int = 25) -> str:
    """Tổng quan NHIỀU dự án: mỗi dự án có tổng việc, đang mở, quá hạn, % hoàn thành.

    Lưu ý: quét nhiều dự án = nhiều request, có thể chậm.

    Args:
        active_only: True = chỉ dự án đang hoạt động.
        max_projects: Giới hạn số dự án quét (mặc định 25).
    """
    pf = [{"active": {"operator": "=", "values": ["t"]}}] if active_only else None
    projects = (
        _collection("/projects", pf, page_size=max_projects)
        .get("_embedded", {})
        .get("elements", [])
    )
    rows = []
    for p in projects:
        pid = p.get("id")
        path = f"/projects/{pid}/work_packages"
        total = _collection(path, page_size=1).get("total", 0)
        open_total = _collection(
            path, [{"status": {"operator": "o", "values": []}}], page_size=1
        ).get("total", 0)
        overdue = _collection(
            path,
            [
                {"status": {"operator": "o", "values": []}},
                {"dueDate": {"operator": "<t-", "values": ["1"]}},
            ],
            page_size=1,
        ).get("total", 0)
        rows.append(
            {
                "id": pid,
                "name": p.get("name"),
                "total": total,
                "open": open_total,
                "overdue": overdue,
                "percent_closed": round((total - open_total) / total * 100, 1) if total else None,
            }
        )
    rows.sort(key=lambda r: -(r["overdue"] or 0))
    return _out({"project_count": len(rows), "projects": rows})

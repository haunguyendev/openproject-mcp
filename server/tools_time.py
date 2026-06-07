"""Tools: time tracking — ghi nhận và liệt kê giờ làm việc."""

from datetime import date
from typing import Any

from app import mcp
from formatters import _link_title, _out, iso8601_to_hours
from op_client import _collection, _req


@mcp.tool()
def log_time(
    wp_id: int,
    hours: float,
    spent_on: str | None = None,
    comment: str = "",
    activity_id: int | None = None,
) -> str:
    """Ghi nhận giờ làm việc (time entry) cho một work package.

    Args:
        wp_id: ID work package.
        hours: Số giờ (vd 1.5).
        spent_on: Ngày làm, YYYY-MM-DD (mặc định hôm nay).
        comment: Ghi chú.
        activity_id: ID loại hoạt động (để trống dùng mặc định).
    """
    body: dict[str, Any] = {
        "hours": f"PT{hours}H",
        "spentOn": spent_on or date.today().isoformat(),
        "comment": {"format": "markdown", "raw": comment},
        "_links": {"workPackage": {"href": f"/api/v3/work_packages/{wp_id}"}},
    }
    if activity_id:
        body["_links"]["activity"] = {"href": f"/api/v3/time_entries/activities/{activity_id}"}
    te = _req("POST", "/time_entries", body=body)
    return _out(
        {"created": {"id": te.get("id"), "hours": te.get("hours"), "spent_on": te.get("spentOn")}}
    )


@mcp.tool()
def list_time_entries(
    project: str | None = None,
    user_me: bool = True,
    from_date: str | None = None,
    to_date: str | None = None,
    page_size: int = 50,
) -> str:
    """Xem các time entries đã ghi nhận.

    Args:
        project: ID dự án (để trống = mọi dự án).
        user_me: True = chỉ giờ của tôi.
        from_date: Từ ngày, YYYY-MM-DD.
        to_date: Đến ngày, YYYY-MM-DD.
        page_size: Số kết quả tối đa.
    """
    filters = []
    if user_me:
        filters.append({"user": {"operator": "=", "values": ["me"]}})
    if project:
        filters.append({"project": {"operator": "=", "values": [str(project)]}})
    if from_date and to_date:
        filters.append({"spentOn": {"operator": "<>d", "values": [from_date, to_date]}})

    data = _collection("/time_entries", filters, page_size)
    items = [
        {
            "id": t.get("id"),
            "hours": t.get("hours"),
            "spent_on": t.get("spentOn"),
            "work_package": _link_title(t, "workPackage"),
            "user": _link_title(t, "user"),
            "comment": (t.get("comment") or {}).get("raw"),
        }
        for t in data.get("_embedded", {}).get("elements", [])
    ]
    return _out({"total": data.get("total"), "items": items})


@mcp.tool()
def my_time_summary(
    from_date: str | None = None,
    to_date: str | None = None,
    project: str | None = None,
) -> str:
    """Tổng hợp giờ làm CỦA TÔI, nhóm theo dự án và work package.

    Args:
        from_date: Từ ngày YYYY-MM-DD (đi cặp với to_date để lọc khoảng).
        to_date: Đến ngày YYYY-MM-DD.
        project: ID dự án (để trống = mọi dự án).
    """
    filters = [{"user": {"operator": "=", "values": ["me"]}}]
    if project:
        filters.append({"project": {"operator": "=", "values": [str(project)]}})
    if from_date and to_date:
        filters.append({"spentOn": {"operator": "<>d", "values": [from_date, to_date]}})

    data = _collection("/time_entries", filters, page_size=200)
    entries = data.get("_embedded", {}).get("elements", [])
    total = 0.0
    by_project: dict[str, float] = {}
    by_wp: dict[str, float] = {}
    for t in entries:
        hrs = iso8601_to_hours(t.get("hours"))
        total += hrs
        proj = _link_title(t, "project") or "(không rõ)"
        wp = _link_title(t, "workPackage") or "(không rõ)"
        by_project[proj] = round(by_project.get(proj, 0.0) + hrs, 2)
        by_wp[wp] = round(by_wp.get(wp, 0.0) + hrs, 2)

    return _out(
        {
            "from": from_date,
            "to": to_date,
            "entry_count": len(entries),
            "total_hours": round(total, 2),
            "by_project": dict(sorted(by_project.items(), key=lambda x: -x[1])),
            "by_work_package": dict(sorted(by_wp.items(), key=lambda x: -x[1])),
        }
    )

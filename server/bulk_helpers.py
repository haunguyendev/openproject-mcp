"""Hàm thuần cho thao tác hàng loạt — chỉ stdlib (test được không cần mạng/mcp)."""


def summarize_bulk(result_key: str, succeeded: list, failed: list) -> dict:
    """Gói kết quả bulk thành envelope thống nhất kèm số đếm.

    Args:
        result_key: Tên khóa cho danh sách thành công ("updated" hoặc "created").
        succeeded: Danh sách item xử lý thành công.
        failed: Danh sách lỗi, mỗi mục có id/index + error.
    """
    return {
        result_key: succeeded,
        "failed": failed,
        "ok_count": len(succeeded),
        "fail_count": len(failed),
        "total": len(succeeded) + len(failed),
    }

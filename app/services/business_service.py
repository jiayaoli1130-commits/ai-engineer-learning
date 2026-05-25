from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.db.sqlite_client import get_connection, init_db


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def query_employee_record(uid: str) -> dict[str, Any]:
    init_db()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT uid, name, department, role, status FROM employees WHERE uid = ?",
            (uid,),
        ).fetchone()

    employee = _row_to_dict(row)
    if employee is None:
        return {"found": False, "error": "未找到该员工", "uid": uid}

    return {"found": True, "employee": employee}


def query_reimbursement_record(reimbursement_id: str) -> dict[str, Any]:
    init_db()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, uid, item_name, amount, platform, status, has_approval, created_at
            FROM reimbursements
            WHERE id = ?
            """,
            (reimbursement_id,),
        ).fetchone()

    reimbursement = _row_to_dict(row)
    if reimbursement is None:
        return {
            "found": False,
            "error": "未找到该报销单",
            "reimbursement_id": reimbursement_id,
        }

    reimbursement["has_approval"] = bool(reimbursement["has_approval"])
    return {"found": True, "reimbursement": reimbursement}


def create_review_ticket_record(reimbursement_id: str, reason: str) -> dict[str, Any]:
    init_db()
    reimbursement_result = query_reimbursement_record(reimbursement_id)
    if not reimbursement_result.get("found"):
        return {
            "success": False,
            "error": "无法创建复核工单：报销单不存在",
            "reimbursement_id": reimbursement_id,
        }

    ticket_id = f"T{uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    ticket = {
        "id": ticket_id,
        "reimbursement_id": reimbursement_id,
        "reason": reason,
        "status": "open",
        "created_at": created_at,
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO tickets (id, reimbursement_id, reason, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticket["id"],
                ticket["reimbursement_id"],
                ticket["reason"],
                ticket["status"],
                ticket["created_at"],
            ),
        )

    return {"success": True, "ticket": ticket}


def calculate_reimbursement_policy(amount: float, limit: float) -> dict[str, Any]:
    reimbursable_amount = min(amount, limit)
    over_limit_amount = max(amount - limit, 0)
    return {
        "amount": amount,
        "limit": limit,
        "is_over_limit": amount > limit,
        "reimbursable_amount": reimbursable_amount,
        "over_limit_amount": over_limit_amount,
    }

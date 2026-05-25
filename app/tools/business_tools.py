import json

from app.services.business_service import (
    calculate_reimbursement_policy as calculate_reimbursement_policy_record,
    create_review_ticket_record,
    query_employee_record,
    query_reimbursement_record,
)


def query_employee(uid: str) -> str:
    return json.dumps(query_employee_record(uid), ensure_ascii=False)


def query_reimbursement(reimbursement_id: str) -> str:
    return json.dumps(
        query_reimbursement_record(reimbursement_id),
        ensure_ascii=False,
    )


def create_review_ticket(reimbursement_id: str, reason: str) -> str:
    return json.dumps(
        create_review_ticket_record(reimbursement_id, reason),
        ensure_ascii=False,
    )


def calculate_reimbursement_policy(amount: float, limit: float) -> str:
    return json.dumps(
        calculate_reimbursement_policy_record(amount, limit),
        ensure_ascii=False,
    )

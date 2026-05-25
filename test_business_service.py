from app.db import sqlite_client
from app.services import business_service


def test_business_service_queries_seeded_reimbursement_and_employee(monkeypatch, tmp_path):
    db_path = tmp_path / "business.db"
    monkeypatch.setattr(sqlite_client, "DB_PATH", db_path)

    employee = business_service.query_employee_record("1001")
    reimbursement = business_service.query_reimbursement_record("R1001")

    assert employee["found"] is True
    assert employee["employee"]["name"] == "张三"
    assert reimbursement["found"] is True
    assert reimbursement["reimbursement"]["item_name"] == "人体工学椅"
    assert reimbursement["reimbursement"]["platform"] == "淘宝"
    assert reimbursement["reimbursement"]["has_approval"] is False


def test_business_service_creates_review_ticket(monkeypatch, tmp_path):
    db_path = tmp_path / "business.db"
    monkeypatch.setattr(sqlite_client, "DB_PATH", db_path)

    result = business_service.create_review_ticket_record(
        "R1001",
        "淘宝购买人体工学椅缺少提前审批，需要人工复核。",
    )

    assert result["success"] is True
    assert result["ticket"]["id"].startswith("T")
    assert result["ticket"]["reimbursement_id"] == "R1001"
    assert result["ticket"]["status"] == "open"


def test_calculate_reimbursement_policy_returns_over_limit_amount():
    result = business_service.calculate_reimbursement_policy(amount=700, limit=600)

    assert result == {
        "amount": 700,
        "limit": 600,
        "is_over_limit": True,
        "reimbursable_amount": 600,
        "over_limit_amount": 100,
    }

import json

from app.agent.agent_tools import TOOL_DISPATCH, tools_list
from app.db import sqlite_client


def test_business_tools_are_registered():
    tool_names = {tool["function"]["name"] for tool in tools_list}

    assert "query_reimbursement" in tool_names
    assert "query_employee" in tool_names
    assert "create_review_ticket" in tool_names
    assert "calculate_reimbursement_policy" in tool_names
    assert "query_reimbursement" in TOOL_DISPATCH
    assert "create_review_ticket" in TOOL_DISPATCH


def test_query_reimbursement_tool_returns_json(monkeypatch, tmp_path):
    db_path = tmp_path / "business.db"
    monkeypatch.setattr(sqlite_client, "DB_PATH", db_path)

    payload = json.loads(TOOL_DISPATCH["query_reimbursement"]("R1001"))

    assert payload["found"] is True
    assert payload["reimbursement"]["id"] == "R1001"
    assert payload["reimbursement"]["item_name"] == "人体工学椅"

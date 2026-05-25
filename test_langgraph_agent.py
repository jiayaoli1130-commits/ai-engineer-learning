from app.agent import langgraph_agent


def test_route_intent_detects_reimbursement_review():
    route = langgraph_agent.route_intent("帮我判断报销单 R1001 是否合规")

    assert route == {
        "intent": "business_reimbursement_review",
        "reimbursement_id": "R1001",
    }


def test_graph_agent_runs_business_review_nodes(monkeypatch):
    monkeypatch.setattr(
        langgraph_agent,
        "query_reimbursement_record",
        lambda reimbursement_id: {
            "found": True,
            "reimbursement": {
                "id": reimbursement_id,
                "uid": "1001",
                "item_name": "人体工学椅",
                "amount": 300,
                "platform": "淘宝",
                "status": "submitted",
                "has_approval": False,
                "created_at": "2026-05-20",
            },
        },
    )
    monkeypatch.setattr(
        langgraph_agent,
        "query_employee_record",
        lambda uid: {
            "found": True,
            "employee": {
                "uid": uid,
                "name": "张三",
                "department": "研发部",
                "role": "算法工程师",
                "status": "active",
            },
        },
    )
    monkeypatch.setattr(
        langgraph_agent,
        "search_knowledge",
        lambda query, n_results=3: {
            "query": query,
            "results": [
                {
                    "content": "淘宝购买办公用品未经审批原则上不予报销。",
                    "metadata": {
                        "filename": "company_rules.md",
                        "section_title": "办公用品采购规定",
                        "chunk_index": 0,
                    },
                    "distance": 0.2,
                    "score": 10.0,
                }
            ],
        },
    )
    monkeypatch.setattr(
        langgraph_agent,
        "create_review_ticket_record",
        lambda reimbursement_id, reason: {
            "success": True,
            "ticket": {
                "id": "TTEST001",
                "reimbursement_id": reimbursement_id,
                "reason": reason,
                "status": "open",
                "created_at": "2026-05-25T00:00:00+00:00",
            },
        },
    )

    result = langgraph_agent.run_graph_agent(
        "帮我判断报销单 R1001 是否合规，如果不合规就创建复核工单。",
        session_id="s1",
        include_trace=True,
    )

    assert "不合规" in result["answer"]
    assert "TTEST001" in result["answer"]
    assert result["sources"][0]["section_title"] == "办公用品采购规定"
    assert [step["node"] for step in result["graph_trace"]] == [
        "intent_router",
        "business_tool_node",
        "rag_node",
        "human_review_node",
        "final_answer_node",
    ]
    assert [item["tool_name"] for item in result["trace"]] == [
        "query_reimbursement",
        "query_employee",
        "retrieve_knowledge",
        "create_review_ticket",
    ]


def test_graph_agent_falls_back_to_react_for_general_chat(monkeypatch):
    monkeypatch.setattr(
        langgraph_agent,
        "run_react_agent",
        lambda user_message, session_id="default", include_trace=False: {
            "answer": "hello",
            "trace": [],
            "sources": [],
            "session_id": session_id,
        },
    )

    result = langgraph_agent.run_graph_agent("你好", session_id="s2", include_trace=True)

    assert result["answer"] == "hello"
    assert result["graph_trace"] == [
        {
            "node": "intent_router",
            "status": "completed",
            "summary": "识别为 general_chat",
        },
        {
            "node": "react_agent_node",
            "status": "completed",
            "summary": "交给现有 ReAct Agent 执行工具调用",
        },
    ]

import re
from typing import Any

from app.agent.agent_core import run_agent as run_react_agent
from app.rag.rag_store import search_knowledge
from app.services.business_service import (
    create_review_ticket_record,
    query_employee_record,
    query_reimbursement_record,
)


BUSINESS_REIMBURSEMENT_PATTERN = re.compile(r"\bR\d+\b", re.IGNORECASE)


def _graph_step(node: str, summary: str, status: str = "completed") -> dict[str, str]:
    return {
        "node": node,
        "status": status,
        "summary": summary,
    }


def route_intent(user_message: str) -> dict[str, Any]:
    reimbursement_match = BUSINESS_REIMBURSEMENT_PATTERN.search(user_message)
    if reimbursement_match:
        return {
            "intent": "business_reimbursement_review",
            "reimbursement_id": reimbursement_match.group(0).upper(),
        }

    policy_keywords = ["制度", "报销", "采购", "流程", "知识库", "规定", "审批"]
    if any(keyword in user_message for keyword in policy_keywords):
        return {"intent": "knowledge_policy_qa", "reimbursement_id": None}

    return {"intent": "general_chat", "reimbursement_id": None}


def _build_policy_query(reimbursement: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for value in [
            reimbursement.get("platform"),
            reimbursement.get("item_name"),
            "报销",
            "审批",
            "制度",
        ]
        if value
    )


def _source_from_search_result(result: dict[str, Any]) -> dict[str, Any]:
    metadata = result.get("metadata") or {}
    return {
        "filename": metadata.get("filename"),
        "document_id": metadata.get("document_id"),
        "section_title": metadata.get("section_title"),
        "chunk_index": metadata.get("chunk_index"),
        "distance": result.get("distance"),
        "score": result.get("score"),
    }


def _needs_review(reimbursement: dict[str, Any], knowledge_text: str) -> tuple[bool, list[str]]:
    reasons = []
    platform = str(reimbursement.get("platform") or "")
    has_approval = bool(reimbursement.get("has_approval"))

    if platform in {"淘宝", "京东", "拼多多", "闲鱼"} and not has_approval:
        reasons.append(f"{platform} 第三方平台购买且缺少提前审批")

    if "不予报销" in knowledge_text and not has_approval:
        reasons.append("制度依据包含不予报销风险且业务记录无审批")

    return bool(reasons), reasons


def _should_create_ticket(user_message: str) -> bool:
    return "创建" in user_message and ("工单" in user_message or "复核" in user_message)


def _business_reimbursement_graph(
    user_message: str,
    session_id: str | None,
    reimbursement_id: str,
) -> dict[str, Any]:
    graph_trace = [
        _graph_step("intent_router", f"识别为报销单合规判断: {reimbursement_id}"),
    ]
    trace = []

    reimbursement_result = query_reimbursement_record(reimbursement_id)
    trace.append(
        {
            "tool_name": "query_reimbursement",
            "arguments": {"reimbursement_id": reimbursement_id},
            "result_summary": (
                f"命中报销单 {reimbursement_id}"
                if reimbursement_result.get("found")
                else reimbursement_result.get("error", "未找到报销单")
            ),
            "result": reimbursement_result,
        }
    )
    graph_trace.append(_graph_step("business_tool_node", "查询报销单业务记录"))

    if not reimbursement_result.get("found"):
        return {
            "answer": f"未找到报销单 {reimbursement_id}，无法判断合规性。",
            "trace": trace,
            "sources": [],
            "graph_trace": graph_trace,
            "session_id": session_id,
        }

    reimbursement = reimbursement_result["reimbursement"]
    employee_result = query_employee_record(str(reimbursement.get("uid")))
    trace.append(
        {
            "tool_name": "query_employee",
            "arguments": {"uid": reimbursement.get("uid")},
            "result_summary": (
                f"命中员工 {reimbursement.get('uid')}"
                if employee_result.get("found")
                else employee_result.get("error", "未找到员工")
            ),
            "result": employee_result,
        }
    )

    policy_query = _build_policy_query(reimbursement)
    knowledge_result = search_knowledge(policy_query, n_results=3)
    knowledge_results = knowledge_result.get("results", [])
    knowledge_text = "\n".join(result.get("content", "") for result in knowledge_results)
    trace.append(
        {
            "tool_name": "retrieve_knowledge",
            "arguments": {"query": policy_query, "n_results": 3},
            "result_summary": (
                "知识库中未找到明确依据"
                if not knowledge_results
                else f"命中 {knowledge_results[0].get('metadata', {}).get('section_title') or '知识库片段'}"
            ),
            "result": knowledge_result,
        }
    )
    graph_trace.append(_graph_step("rag_node", f"检索制度依据: {policy_query}"))

    needs_review, review_reasons = _needs_review(reimbursement, knowledge_text)
    ticket_result = None
    if needs_review and _should_create_ticket(user_message):
        reason = "；".join(review_reasons)
        ticket_result = create_review_ticket_record(reimbursement_id, reason)
        trace.append(
            {
                "tool_name": "create_review_ticket",
                "arguments": {
                    "reimbursement_id": reimbursement_id,
                    "reason": reason,
                },
                "result_summary": (
                    f"已创建复核工单 {ticket_result.get('ticket', {}).get('id')}"
                    if ticket_result.get("success")
                    else ticket_result.get("error", "复核工单创建失败")
                ),
                "result": ticket_result,
            }
        )

    graph_trace.append(
        _graph_step(
            "human_review_node",
            "需要人工复核" if needs_review else "未发现必须人工复核的风险",
        )
    )

    employee = employee_result.get("employee") or {}
    sources = [_source_from_search_result(result) for result in knowledge_results]
    conclusion = "不合规，建议退回复核" if needs_review else "暂未发现明确不合规风险"
    ticket_line = ""
    if ticket_result and ticket_result.get("success"):
        ticket_line = f"\n- 复核工单: {ticket_result['ticket']['id']}"

    source_lines = "\n".join(
        f"- {source.get('filename')}（{source.get('section_title') or '未命名章节'}）"
        for source in sources
    )
    if not source_lines:
        source_lines = "- 知识库中未找到明确依据"

    answer = (
        f"**结论**\n"
        f"- 报销单 {reimbursement_id}: {conclusion}。\n"
        f"{ticket_line}\n\n"
        f"**业务记录**\n"
        f"- 员工: {employee.get('name', '未知')}（{employee.get('department', '未知部门')}）\n"
        f"- 事项: {reimbursement.get('platform')} 购买 {reimbursement.get('item_name')}，金额 {reimbursement.get('amount')} 元\n"
        f"- 审批记录: {'有' if reimbursement.get('has_approval') else '无'}\n\n"
        f"**依据**\n"
        f"- {'；'.join(review_reasons) if review_reasons else '未发现第三方平台未审批或超额等确定性风险'}\n\n"
        f"**建议**\n"
        f"- {'等待人工复核后再处理报销。' if needs_review else '按正常报销流程继续审核。'}\n\n"
        f"**引用来源**\n"
        f"{source_lines}"
    )
    graph_trace.append(_graph_step("final_answer_node", "生成最终业务回答"))

    return {
        "answer": answer,
        "trace": trace,
        "sources": sources,
        "graph_trace": graph_trace,
        "session_id": session_id,
    }


def run_graph_agent(
    user_message: str,
    session_id: str | None = "default",
    include_trace: bool = False,
) -> Any:
    route = route_intent(user_message)

    if route["intent"] == "business_reimbursement_review":
        result = _business_reimbursement_graph(
            user_message=user_message,
            session_id=session_id,
            reimbursement_id=route["reimbursement_id"],
        )
        return result if include_trace else result["answer"]

    graph_trace = [
        _graph_step("intent_router", f"识别为 {route['intent']}"),
        _graph_step("react_agent_node", "交给现有 ReAct Agent 执行工具调用"),
    ]
    result = run_react_agent(
        user_message=user_message,
        session_id=session_id,
        include_trace=True,
    )
    result["graph_trace"] = graph_trace

    return result if include_trace else result["answer"]

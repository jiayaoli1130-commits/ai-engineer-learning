import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from app.agent.agent_tools import TOOL_DISPATCH, tools_list


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"),
)

MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")


SYSTEM_PROMPT = """
你是企业内部 AI Agent，负责基于企业知识库和业务工具回答问题。

规则：
1. 涉及公司制度、报销、采购、流程或内部知识库时，必须调用 retrieve_knowledge。
2. 调用 retrieve_knowledge 时，query 必须保留用户问题和业务记录中的关键实体，包括物品、平台、金额、城市、人员和业务场景。
3. 用户要求判断某个报销单是否合规时，必须先调用 query_reimbursement；拿到 uid 后再调用 query_employee。
4. 报销单合规判断必须同时使用业务记录和制度依据，不要只看知识库或只看业务库。
5. 发现缺少审批、平台不符合制度、超额或其他需人工确认的风险时，可以调用 create_review_ticket 创建复核工单。
6. 金额比较、上限计算等确定性判断优先调用 calculate_reimbursement_policy 或在工具结果基础上明确计算。
7. 工具返回 results 为空时，必须说“知识库中未找到明确依据”。
8. 回答必须基于工具结果，不允许编造制度名、金额、审批人、条款编号或日期。
9. 最终回答需要包含：结论、依据、建议、引用来源；如创建了工单，也要给出工单号。
10. 引用来源只列出真正用于回答的 chunk，不要列出所有检索结果。
"""


def _format_reference(result: Dict[str, Any]) -> str:
    metadata = result.get("metadata") or {}
    filename = metadata.get("filename") or metadata.get("source") or "知识库检索结果"
    section_title = metadata.get("section_title")
    chunk_index = metadata.get("chunk_index")
    distance = result.get("distance")
    details = []

    if section_title:
        details.append(str(section_title))

    if chunk_index is not None:
        details.append(f"chunk {int(chunk_index) + 1}")

    if distance is not None:
        details.append(f"distance {float(distance):.4f}")

    if details:
        return f"{filename}（{'，'.join(details)}）"

    return str(filename)


def _source_from_result(result: Dict[str, Any]) -> Dict[str, Any]:
    metadata = result.get("metadata") or {}
    return {
        "filename": metadata.get("filename"),
        "document_id": metadata.get("document_id"),
        "section_title": metadata.get("section_title"),
        "chunk_index": metadata.get("chunk_index"),
        "distance": result.get("distance"),
        "score": result.get("score"),
    }


def _extract_sources(tool_results: List[str]) -> List[Dict[str, Any]]:
    sources = []
    seen = set()

    for raw_result in tool_results:
        try:
            payload = json.loads(raw_result)
        except json.JSONDecodeError:
            continue

        for result in payload.get("results", []):
            source = _source_from_result(result)
            key = (
                source.get("document_id"),
                source.get("filename"),
                source.get("chunk_index"),
                source.get("section_title"),
            )
            if key in seen:
                continue

            seen.add(key)
            sources.append(source)

    return sources


def _extract_references(tool_results: List[str]) -> List[str]:
    references = []
    seen = set()

    for raw_result in tool_results:
        try:
            payload = json.loads(raw_result)
        except json.JSONDecodeError:
            continue

        for result in payload.get("results", []):
            reference = _format_reference(result)
            if reference in seen:
                continue

            seen.add(reference)
            references.append(reference)

    return references


def _append_references(answer: str, tool_results: List[str]) -> str:
    references = _extract_references(tool_results)

    if not references or "引用来源" in answer:
        return answer

    reference_lines = "\n".join(f"- {reference}" for reference in references)
    return f"{answer.rstrip()}\n\n**引用来源**\n{reference_lines}"


def _parse_trace_value(raw_value: str) -> Any:
    if not isinstance(raw_value, str):
        return raw_value

    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def _summarize_tool_result(tool_name: str, parsed_result: Any) -> str:
    if tool_name == "retrieve_knowledge" and isinstance(parsed_result, dict):
        results = parsed_result.get("results") or []
        if not results:
            return "知识库中未找到明确依据"

        first = results[0]
        metadata = first.get("metadata") or {}
        section = metadata.get("section_title") or metadata.get("filename") or "unknown"
        chunk_index = metadata.get("chunk_index")
        chunk_label = f" chunk {int(chunk_index) + 1}" if chunk_index is not None else ""
        return f"命中 {section}{chunk_label}"

    if tool_name == "query_reimbursement" and isinstance(parsed_result, dict):
        if not parsed_result.get("found"):
            return parsed_result.get("error", "未找到报销单")
        reimbursement = parsed_result.get("reimbursement") or {}
        return f"报销单 {reimbursement.get('id')}：{reimbursement.get('item_name')} {reimbursement.get('amount')}"

    if tool_name == "query_employee" and isinstance(parsed_result, dict):
        if not parsed_result.get("found"):
            return parsed_result.get("error", "未找到员工")
        employee = parsed_result.get("employee") or {}
        return f"员工 {employee.get('uid')}：{employee.get('name')} {employee.get('department')}"

    if tool_name == "create_review_ticket" and isinstance(parsed_result, dict):
        if not parsed_result.get("success"):
            return parsed_result.get("error", "复核工单创建失败")
        ticket = parsed_result.get("ticket") or {}
        return f"已创建复核工单 {ticket.get('id')}"

    if isinstance(parsed_result, dict):
        if parsed_result.get("error"):
            return str(parsed_result["error"])
        keys = ", ".join(list(parsed_result.keys())[:3])
        return f"返回字段: {keys}" if keys else "返回空对象"

    return str(parsed_result)[:120]


def run_agent(
    user_message: str,
    session_id: str | None = "default",
    include_trace: bool = False,
) -> Any:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    knowledge_tool_results = []
    trace = []

    while True:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools_list,
            tool_choice="auto",
        )

        ai_message = response.choices[0].message
        messages.append(ai_message.model_dump(exclude_none=True))

        if not ai_message.tool_calls:
            answer = _append_references(ai_message.content or "", knowledge_tool_results)
            sources = _extract_sources(knowledge_tool_results)

            if include_trace:
                return {
                    "answer": answer,
                    "trace": trace,
                    "sources": sources,
                    "session_id": session_id,
                }

            return answer

        for tool_call in ai_message.tool_calls:
            tool_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments or "{}"
            trace_arguments = raw_arguments

            try:
                arguments = json.loads(raw_arguments)
                trace_arguments = arguments
            except json.JSONDecodeError:
                tool_result = json.dumps(
                    {
                        "error": "工具参数不是合法 JSON",
                        "raw_arguments": raw_arguments,
                    },
                    ensure_ascii=False,
                )
            else:
                func = TOOL_DISPATCH.get(tool_name)

                if func is None:
                    tool_result = json.dumps(
                        {
                            "error": f"未知工具: {tool_name}",
                        },
                        ensure_ascii=False,
                    )
                else:
                    try:
                        tool_result = func(**arguments)
                    except Exception as exc:
                        tool_result = json.dumps(
                            {
                                "error": f"工具执行失败: {str(exc)}",
                                "tool_name": tool_name,
                                "arguments": arguments,
                            },
                            ensure_ascii=False,
                        )

            parsed_result = _parse_trace_value(tool_result)
            trace.append(
                {
                    "tool_name": tool_name,
                    "arguments": trace_arguments,
                    "result_summary": _summarize_tool_result(tool_name, parsed_result),
                    "result": parsed_result,
                }
            )

            if tool_name == "retrieve_knowledge":
                knowledge_tool_results.append(tool_result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": tool_result,
                }
            )

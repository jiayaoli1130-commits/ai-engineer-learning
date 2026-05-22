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
你是一个企业内部 AI Agent。

规则：
1. 如果用户问题涉及公司制度、报销、采购、流程、内部知识库，必须先调用 retrieve_knowledge。
2. 回答必须严格基于工具返回的内容。
3. 不允许编造文档标题、制度名称、条款编号、审批人、金额、日期。
4. 如果工具返回内容里没有明确来源名称，就只说“根据知识库检索结果”。
5. 如果知识库没有检索到明确依据，要说“知识库中未找到明确依据”，不要猜测。
6. 可以做常识归类，例如人体工学椅可以归为办公用品，但必须说明这是基于知识库内容的合理归类。
7. 最终回答要简洁、明确、可执行，并在回答中使用 Markdown 格式。
"""


def _format_reference(result: Dict[str, Any]) -> str:
    metadata = result.get("metadata") or {}
    filename = metadata.get("filename") or metadata.get("source") or "知识库检索结果"
    chunk_index = metadata.get("chunk_index")
    distance = result.get("distance")
    details = []

    if chunk_index is not None:
        details.append(f"chunk {int(chunk_index) + 1}")

    if distance is not None:
        details.append(f"distance {float(distance):.4f}")

    if details:
        return f"{filename}（{'，'.join(details)}）"

    return str(filename)


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


def run_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    knowledge_tool_results = []

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
            return _append_references(ai_message.content or "", knowledge_tool_results)

        for tool_call in ai_message.tool_calls:
            tool_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments or "{}"

            try:
                arguments = json.loads(raw_arguments)
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

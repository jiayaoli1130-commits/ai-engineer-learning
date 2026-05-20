import json

from dotenv import load_dotenv
from openai import OpenAI

from agent_tools import TOOL_DISPATCH, tools_list


load_dotenv()

client = OpenAI(base_url="https://api.deepseek.com")

MODEL_NAME = "deepseek-chat"


SYSTEM_PROMPT = """
你是一个企业内部 AI Agent。

规则：
1. 如果用户问题涉及公司制度、报销、采购、流程、内部知识库，必须先调用 retrieve_knowledge。
2. 回答必须严格基于工具返回的内容。
3. 不允许编造文档标题、制度名称、条款编号、审批人、金额、日期。
4. 如果工具返回内容里没有明确来源名称，就只说“根据知识库检索结果”。
5. 如果知识库没有检索到明确依据，要说“知识库中未找到明确依据”，不要猜测。
6. 可以做常识归类，例如人体工学椅可以归为办公用品，但必须说明这是基于知识库内容的合理归类。
7. 最终回答要简洁、明确、可执行。
"""


def run_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

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
            return ai_message.content or ""

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

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": tool_result,
                }
            )

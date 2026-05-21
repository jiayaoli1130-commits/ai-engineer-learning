import os
import json
from dotenv import load_dotenv
from openai import OpenAI
# 【关键第一步】导入你刚刚在另一个文件里写的本地函数和说明书
from app.agent.agent_tools import get_weather, query_user, update_user_status, tools_list

load_dotenv()
client = OpenAI(base_url="https://api.deepseek.com")

# 我们故意问一个需要用到工具的问题
messages_history = [
    {"role": "system", "content": "你是数据库管理员助手。"},
    {"role": "user", "content": "帮我查一下工号 1002 的用户。如果他的状态是 locked，请帮我把他修改为 active。"}
]

print("1️⃣ 正在把问题和【工具箱】一起发给大模型...\n")

# 注意这里的重大变化：多了一个 tools 参数！
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages_history,
    tools=tools_list  # 把工具说明书告诉它
)

# 获取 AI 返回的完整消息对象
ai_message = response.choices[0].message

# ---------------------------------------------------------
# 🔄 多轮循环：AI 可能连续调用多个工具！
#   比如：先 query_user -> 看到 locked -> 再 update_user_status
# ---------------------------------------------------------

# 工具名 -> 实际 Python 函数的映射表（优雅分发）
TOOL_DISPATCH = {
    "get_weather": get_weather,
    "query_user": query_user,
    "update_user_status": update_user_status,
}

turn_count = 0

while ai_message.tool_calls:
    turn_count += 1
    print(f"\n{'='*50}")
    print(f"🔁 第 {turn_count} 轮工具调用")
    print(f"{'='*50}")

    # 遍历 AI 这次请求调用的所有工具（某些场景可能一次要调多个）
    for tool_call in ai_message.tool_calls:
        func_name = tool_call.function.name

        # 【重点回忆】AI 返回的参数是 JSON 格式的字符串，必须用 json.loads 转成 Python 字典！
        arguments = json.loads(tool_call.function.arguments)
        print(f"\n   => AI 请求执行的函数名：{func_name}")
        print(f"   => AI 提取出的参数为：{arguments}")

        # 从映射表中找到对应的真实 Python 函数并执行
        func = TOOL_DISPATCH.get(func_name)
        if func:
            print(f"\n⚡ 正在本地执行 Python 函数：{func_name}()...")
            local_result = func(**arguments)
            print(f"   => 本地函数执行完毕，拿到的数据是：{local_result}")
        else:
            local_result = json.dumps({"error": f"未知工具: {func_name}"})
            print(f"   ⚠️ 警告：找不到名为 {func_name} 的工具")

        # --- 结果回传阶段 ---
        # (1) 必须先把 AI 的"调用动作"存入历史记录
        messages_history.append(ai_message)
        # (2) 再把"本地执行的结果"存入历史记录（注意 role 是 "tool"）
        messages_history.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": local_result
        })

        print(f"\n📤 已将 {func_name} 的执行结果回传给 AI...")

    # 拿着包含了【本地数据】的完整历史记录，再次请求 AI
    # AI 此时可能会：
    #   - 继续调用下一个工具（比如先查用户，再修改状态）
    #   - 或者拿到所有结果后，直接回复最终答案
    print(f"\n🔄 将历史记录再次发给 AI，等待它的下一步决定...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages_history,
        tools=tools_list  # 每次都带着工具箱，让 AI 可以继续调用
    )

    ai_message = response.choices[0].message

# ---------------------------------------------------------
# 🎯 当 AI 不再请求工具调用，说明它已经准备好回答用户
# ---------------------------------------------------------
print(f"\n{'='*50}")
print(f"🎉 AI 已完成所有工具调用，以下是最终回答：")
print(f"{'='*50}")
print(f"\nAI: {ai_message.content}")

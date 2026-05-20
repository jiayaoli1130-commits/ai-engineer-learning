import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 【关键配置拓展】：如果你使用的是国内的代理 API 服务，或者兼容 OpenAI 格式的国产大模型（如 DeepSeek），
# 你只需要在初始化时传入 base_url。如果用的是原生 OpenAI，括号里留空即可。
client = OpenAI(
    base_url="https://api.deepseek.com", 
)

print("正在向 AI 发送电报...")

messages_history = [
    {"role": "system", "content": "你是一个说话极其简短、像黑客一样的AI助手。"}
]
while True:
    input_maessage=input("你：")
    if input_maessage in ["quit", "退出"]:
        break
    else:
        messages_history.append({"role": "user", "content": input_maessage})
        try:
            response = client.chat.completions.create(
                model="deepseek-v4-flash", 
                messages=messages_history,
            )
            # 2. 剥洋葱式的解析
            # 大模型返回的 response 是一个极其复杂的巨大嵌套数据结构，包含了使用消耗的 token 数、停止原因等。
            # 我们只需要它回复的那句纯文本，必须这样“剥洋葱”：
            ai_reply = response.choices[0].message.content
            print(f"AI 回复: {ai_reply}")
            messages_history.append({"role": "assistant", "content": ai_reply})
            
        except Exception as e:
            print(f"发生错误: {e}")
            continue
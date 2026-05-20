import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url="https://api.deepseek.com")

# 1. 模拟我们刚刚从"向量数据库"里检索出来的私有切片
knowledge_base = """
员工报销管理规定：
1. 员工每月交通补助上限为 800 元，超出部分需由部门总监审批。
2. 购买办公用品必须在指定的"星辰采购网"进行，否则不予报销。
3. 报销单提交截止时间为每月 25 号下午 5 点，逾期顺延至次月。
"""

# ========================================================
# 2. RAG 核心魔法：系统提示词工程 (Prompt Engineering)
# ========================================================
system_prompt = f"""
你是一个严谨的公司行政财务助手。
请你**严格**根据下面提供的【参考资料】来回答用户的问题。
如果用户的提问在【参考资料】中找不到答案，请直接回答"抱歉，公司规定中未提及此事，请咨询人工 HR"，绝不能利用你自己的知识编造！

【参考资料】：
{knowledge_base}
"""

def ask_rag(question):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )
    return response.choices[0].message.content

# ========================================================
# 3. 三次测试
# ========================================================

# 测试1：基础功能 - 交通补贴
q1 = "我这个月打车花了 950 块钱，可以直接找财务报销吗？"
print(f"[测试1] 员工提问: {q1}")
print(f"[财务 AI]: {ask_rag(q1)}\n")

# 测试2：防幻觉机制 - 未提及的问题
q2 = "咱们公司的年假有几天？"
print(f"[测试2] 员工提问: {q2}")
print(f"[财务 AI]: {ask_rag(q2)}\n")

# 测试3：细节检索 - 办公用品采购
q3 = "我在京东上买了一把 200 块钱的办公椅，明天去报销行吗？"
print(f"[测试3] 员工提问: {q3}")
print(f"[财务 AI]: {ask_rag(q3)}\n")

import json

from app.rag.rag_store import retrieve_knowledge


mock_db = {
    "1001": {"name": "张三", "role": "user", "status": "active"},
    "1002": {"name": "李四", "role": "admin", "status": "locked"},
}


def query_user(uid):
    """查询模拟用户信息。"""
    user_data = mock_db.get(uid, {"error": "未找到该用户"})
    return json.dumps(user_data, ensure_ascii=False)


def update_user_status(uid, new_status):
    """更新模拟用户状态。"""
    if uid in mock_db:
        mock_db[uid]["status"] = new_status
        return json.dumps({"success": True, "message": "状态更新成功"}, ensure_ascii=False)
    return json.dumps({"success": False, "message": "用户不存在"}, ensure_ascii=False)


def get_weather(location):
    """返回模拟天气数据，用于保留早期 tool calling 示例。"""
    weather_data = {
        "location": location,
        "temperature": "25°C",
        "condition": "晴朗",
        "tips": "适合穿短袖",
    }
    return json.dumps(weather_data, ensure_ascii=False)


tools_list = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_knowledge",
            "description": (
                "从本地公司知识库、规章制度、报销规定、采购制度、流程文档中检索相关内容。"
                "当用户询问公司制度、报销、采购、流程、内部规定时，必须优先调用此工具。"
                "query 必须保留用户原问题中的具体实体，包括物品、平台、金额、城市、人员和业务场景。"
                "例如用户问“淘宝买人体工学椅可以报销吗”，query 应为“淘宝 人体工学椅 办公用品 报销 星辰采购网”，"
                "不要只写“淘宝购买报销规定”。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "保留关键实体后的知识库检索 query。",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "返回的相关片段数量，默认 3。",
                    },
                    "max_distance": {
                        "type": "number",
                        "description": "可选的向量距离上限；距离越小表示越相似，超过该值的结果会被过滤。",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的模拟天气情况。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、广州。",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_user",
            "description": "通过工号 uid 查询模拟用户信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string", "description": "用户的唯一工号，如 1001。"}
                },
                "required": ["uid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_status",
            "description": "修改指定模拟用户的状态 status。",
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string", "description": "用户的唯一工号。"},
                    "new_status": {"type": "string", "description": "新的状态，如 active 或 locked。"},
                },
                "required": ["uid", "new_status"],
            },
        },
    },
]

TOOL_DISPATCH = {
    "get_weather": get_weather,
    "query_user": query_user,
    "update_user_status": update_user_status,
    "retrieve_knowledge": retrieve_knowledge,
}

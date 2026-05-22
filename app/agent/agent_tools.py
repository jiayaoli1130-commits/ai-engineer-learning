import json
from app.rag.rag_store import retrieve_knowledge

# 模拟系统底层数据库
mock_db = {
    "1001": {"name": "张三", "role": "user", "status": "active"},
    "1002": {"name": "李四", "role": "admin", "status": "locked"}
}



def query_user(uid):
    """查询数据库中的用户信息"""
    print(f"🗄️ [DB执行]: SELECT * FROM users WHERE uid = '{uid}'")
    # 模拟数据库查询
    user_data = mock_db.get(uid, {"error": "未找到该用户"})
    return json.dumps(user_data, ensure_ascii=False)

def update_user_status(uid, new_status):
    """更新数据库中的用户状态"""
    print(f"🗄️ [DB执行]: UPDATE users SET status = '{new_status}' WHERE uid = '{uid}'")
    if uid in mock_db:
        mock_db[uid]["status"] = new_status
        return json.dumps({"success": True, "message": "状态更新成功"}, ensure_ascii=False)
    return json.dumps({"success": False, "message": "用户不存在"}, ensure_ascii=False)

def get_weather(location):
    """一个模拟查询天气的本地函数"""
    print(f"🔧 [本地执行]: 正在查询 {location} 的天气...")
    # 在真实项目中，这里会去调用真实的天气 API，现在我们写死假数据
    weather_data = {
        "location": location,
        "temperature": "25℃",
        "condition": "晴朗",
        "tips": "适合穿短袖"
    }
    # 必须把字典转成 JSON 字符串返回，因为大模型只认识文本
    return json.dumps(weather_data, ensure_ascii=False)

# 这是 OpenAI 和 DeepSeek 标准的工具描述格式 (严格的 JSON 结构化字典)
tools_list = [
    {
        "type": "function",
        "function": {
            "name": "get_weather", # 必须和你的 Python 函数名一模一样
            "description": "获取指定城市的当前天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、广州"
                    }
                },
                "required": ["location"] # 告诉 AI 这个参数是必填的
            }
        }
    },

    
    {
        "type": "function",
        "function": {
            "name": "query_user",
            "description": "通过工号(uid)查询数据库中的用户信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string", "description": "用户的唯一工号，如 1001"}
                },
                "required": ["uid"]
            }
        }
    },

    {
    "type": "function",
    "function": {
        "name": "retrieve_knowledge",
        "description": (
            "从本地公司知识库、规章制度、报销规定、采购制度、流程文档中检索相关内容。"
            "当用户询问公司制度、报销、采购、流程、内部规定时，必须优先调用此工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用户问题或需要检索的语义查询",
                },
                "n_results": {
                    "type": "integer",
                    "description": "返回的相关片段数量，默认 3",
                },
                "max_distance": {
                    "type": "number",
                    "description": "可选的向量距离上限；距离越小表示越相似，超过该值的结果会被过滤",
                },
            },
            "required": ["query"],
        },
    },
},
    {
        "type": "function",
        "function": {
            "name": "update_user_status",
            "description": "修改指定用户的状态(status)",
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string", "description": "用户的唯一工号"},
                    "new_status": {"type": "string", "description": "新的状态，如 active 或 locked"}
                },
                "required": ["uid", "new_status"]
            }
        }
    }
]
TOOL_DISPATCH = {
    "get_weather": get_weather,
    "query_user": query_user,
    "update_user_status": update_user_status,
    "retrieve_knowledge": retrieve_knowledge,
}

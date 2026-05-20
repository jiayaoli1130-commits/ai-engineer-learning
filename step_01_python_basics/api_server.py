import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from openai import OpenAI
from dotenv import load_dotenv # 👈 新增
from fastapi.middleware.cors import CORSMiddleware
# 导入你之前写好的工具库
from agent_tools import get_weather, query_user, update_user_status, tools_list

load_dotenv()  # 加载环境变量，确保 API Key 可用

app = FastAPI(title="AI Agent Core Service", description="企业级智能体微服务")
client = OpenAI(base_url="https://api.deepseek.com")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有前端域名访问（测试时写 "*" 最方便，上线时改成前端的具体域名）
    allow_credentials=True,
    allow_methods=["*"], # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE)
    allow_headers=["*"], # 允许所有请求头
)

# ==========================================
# 1. 定义数据传输对象 (对标 Java 的 DTO)
# ==========================================
class ChatRequest(BaseModel):
    message: str
    # 未来这里可以加上 user_id, session_id 等参数用于历史记录管理

class ResultWrapper(BaseModel):
    code: int
    msg: str
    data: str

# 工具路由表
TOOL_DISPATCH = {
    "get_weather": get_weather,
    "query_user": query_user,
    "update_user_status": update_user_status,
}

# ==========================================
# 2. 核心接口定义 (对标 Java 的 @RestController 和 @PostMapping)
# ==========================================
@app.post("/api/chat", response_model=ResultWrapper)
def agent_chat_endpoint(req: ChatRequest):
    """
    接收用户自然语言指令，调度 Agent 完成任务并返回结果。
    """
    try:
        # 初始化当前会话的上下文
        messages_history = [
            {"role": "system", "content": "你是数据库管理员助手。"},
            {"role": "user", "content": req.message} # 使用接收到的 JSON 里的 message
        ]
        
        # 第一次向 AI 发起请求
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_history,
            tools=tools_list
        )
        ai_message = response.choices[0].message

        # 核心的 ReAct 循环 (直接复用你刚才写好的逻辑)
        while ai_message.tool_calls:
            for tool_call in ai_message.tool_calls:
                func_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # 执行本地函数
                func = TOOL_DISPATCH.get(func_name)
                local_result = func(**arguments) if func else json.dumps({"error": "未知工具"})
                
                # 回传结果
                messages_history.append(ai_message)
                messages_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": local_result
                })
            
            # 携带执行结果，再次请求大模型
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages_history,
                tools=tools_list
            )
            ai_message = response.choices[0].message

        # 循环结束，拿到最终纯文本结果，封装成统一格式返回
        return ResultWrapper(
            code=200, 
            msg="success", 
            data=ai_message.content
        )

    except Exception as e:
        # 全局异常捕获，返回标准错误格式
        print(f"服务器内部错误: {str(e)}")
        # 对标 Java 的 throw new CustomException(...)
        raise HTTPException(status_code=500, detail=f"Agent 处理异常: {str(e)}")

# ==========================================
# 3. 启动服务器 (对标 public static void main)
# ==========================================
if __name__ == "__main__":
    # 启动命令：运行在本机的 8080 端口
    print("🚀 AI Agent 微服务正在启动...")
    uvicorn.run(app, host="127.0.0.1", port=8080)
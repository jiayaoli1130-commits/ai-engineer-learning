# Enterprise Agentic RAG Platform

企业知识库智能体平台：用 ChromaDB 检索制度依据，用 Agent 调用工具并整合结果，用 trace 解释每一步，用 eval 防止系统退化。

## What It Solves

企业内部有大量制度文档、审批规则、业务记录和操作流程。用户不想手动翻文档，也不想自己判断政策是否适用。

本项目通过 RAG 检索制度依据，通过 Agent 调用业务工具，最终给出可追溯、可评测、可扩展的业务回答。

## Current Scope

- FastAPI API layer
- OpenAI-compatible tool calling agent
- ChromaDB 本地向量知识库
- `.txt`、`.md`、`.pdf` 文档入库
- Markdown 章节切块与 `section_title` metadata
- 检索结果关键词重排和 `distance` 过滤
- `/chat` 返回固定结构：`answer + trace + sources`
- `run_eval.py` 检查答案关键词、禁止词、trace 和 sources
- 简单 HTML 前端

## Architecture Direction

```text
frontend/
  -> FastAPI API Layer
  -> Application Service Layer
  -> Agent Core
  -> Tool Layer
       - RAG Tool
       - Business DB Tool
       - Ticket Tool
       - Calculator Tool
       - Future MCP Tool Adapter
  -> Data Layer
       - ChromaDB / Qdrant
       - SQLite / PostgreSQL
       - uploads/
       - eval_results/
```

当前代码仍保持小步演进，没有一次性重构到完整目录。后续优先顺序：

1. v2：可观测 + 可评测 Agent
2. v3：SQLite 业务数据库和企业工具
3. v4：LangGraph Agent
4. v5：MCP Demo

## Quick Start

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

在 `.env` 中填写 API key：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

启动后端：

```bash
uvicorn app.main:app --reload --port 8000
```

接口文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

前端：直接打开 `frontend/index.html`。

## API

### `POST /chat`

```json
{
  "message": "我在淘宝买了一把人体工学椅，300块，可以报销吗？",
  "session_id": "default"
}
```

响应固定为：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "answer": "...",
    "trace": [],
    "sources": [],
    "session_id": "default"
  }
}
```

### Knowledge

- `POST /knowledge/ingest`
- `POST /knowledge/upload`
- `POST /knowledge/search`
- `GET /knowledge/documents`
- `POST /knowledge/delete`
- `POST /knowledge/reset`

## Eval

先启动后端并入库测试文档：

```bash
python -m app.rag.rag_store
python run_eval.py
```

`eval_cases.json` 会检查：

- `must_include`
- `must_not_include`
- `trace_must_include`
- `sources_must_include`

失败时脚本会 `exit(1)`，适合放进后续 CI。

## Tests

```bash
pytest test_agent_core.py test_api_server.py test_rag_store_management.py test_rag.py
```

全量 `pytest` 目前还会收集 `step_01_python_basics/` 里的早期练习文件；那些文件不是当前平台测试套件的一部分。

## Deployment Notes

Render backend:

```bash
pip install -r requirements.txt
uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

Set `OPENAI_API_KEY` in Render Environment Variables. Do not upload `.env`.

Vercel frontend:

- Root Directory: `frontend`
- Framework Preset: `Other`
- Build Command: leave empty
- Output Directory: leave empty or `.`

当前演示版使用本地 ChromaDB persistence at `./my_vector_db`。在 Render 等云环境中，本地文件长期可靠性有限，重启或重新部署后可能需要重新上传文档。正式版本建议升级到 Qdrant Cloud、Pinecone、Supabase pgvector 或托管 Chroma。

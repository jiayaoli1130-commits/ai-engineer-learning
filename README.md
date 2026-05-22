# AI Agent RAG Demo

一个基于 FastAPI、OpenAI SDK 和 ChromaDB 的本地 RAG Agent 示例项目。它支持文档入库、知识库检索、文件上传、Agent 工具调用，以及带引用来源的 Markdown 回答。

## 功能

- FastAPI 提供 HTTP 接口
- OpenAI-compatible API 负责 Agent 推理
- ChromaDB 负责本地向量知识库
- 支持 `.txt`、`.md`、`.pdf` 文档入库
- 支持 `distance` 阈值过滤检索结果
- Agent 回答会追加知识库引用来源
- 纯 HTML 前端，支持 Markdown 渲染

## 快速开始

1. 创建虚拟环境并安装依赖：

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. 创建环境变量文件：

```bash
copy .env.example .env
```

然后在 `.env` 中填写自己的 API Key。

3. 启动后端：

```bash
uvicorn app.main:app --reload --port 8000
```

接口文档地址：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

4. 打开前端：

直接用浏览器打开 `frontend/index.html`。

## 环境变量

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
```

`OPENAI_BASE_URL` 和 `MODEL_NAME` 都有默认值；只要 `.env` 中有可用的 `OPENAI_API_KEY` 就能运行当前配置。

## 常用接口

### `POST /chat`

```json
{
  "message": "我在淘宝买了人体工学椅，可以报销吗？"
}
```

### `POST /knowledge/ingest`

```json
{
  "file_path": "./docs/company_rules.md"
}
```

### `POST /knowledge/search`

```json
{
  "query": "人体工学椅报销",
  "n_results": 3,
  "max_distance": 1.2
}
```

`max_distance` 是可选字段。距离越小表示越相似；传入后，超过该阈值的向量检索结果会被过滤。

### `POST /knowledge/upload`

使用 `multipart/form-data` 上传文件，字段名为 `file`。

### `GET /knowledge/documents`

返回已入库文档列表。

### `POST /knowledge/delete`

```json
{
  "document_id": "document_id_here"
}
```

### `POST /knowledge/reset`

清空并重建当前 ChromaDB collection。

## 测试

```bash
pytest
```

## 目录说明

- `app/main.py`：FastAPI 入口
- `app/rag/rag_store.py`：文档读取、切块、入库、检索
- `app/agent/agent_core.py`：Agent 循环与引用来源拼接
- `app/agent/agent_tools.py`：工具定义与分发
- `frontend/index.html`：本地前端页面
- `docs/`：示例知识库文档

# AI Agent RAG Demo

一个基于 FastAPI、OpenAI SDK 和 ChromaDB 的本地 RAG Agent 示例项目。它既能通过知识库做制度问答，也保留了 Agent 的 Tool Calling / ReAct 循环能力，适合作为第一个完整 AI 工程项目放到 GitHub 展示。

## 项目功能

- FastAPI 提供 HTTP 接口
- OpenAI 模型负责 Agent 推理
- ChromaDB 负责本地向量知识库
- 支持公司制度文档检索问答
- 支持 Tool Calling / ReAct 循环

## 启动方式

```bash
uvicorn app.main:app --reload --port 8000
```

启动后默认地址为 [http://127.0.0.1:8000](http://127.0.0.1:8000)，接口文档可在 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看。

## 接口

### `POST /chat`

请求：

```json
{
  "message": "我在淘宝买了人体工学椅，可以报销吗？"
}
```

### `POST /knowledge/ingest`

请求：

```json
{
  "file_path": "./docs/company_rules.md"
}
```

说明：将本地文档切块后写入 ChromaDB，适合导入公司制度、知识库、FAQ 等内容。

### `POST /knowledge/search`

请求：

```json
{
  "query": "人体工学椅报销",
  "n_results": 3
}
```

说明：直接调试 RAG 召回结果，便于观察知识库是否命中正确片段。

### `POST /knowledge/reset`

请求：无请求体

说明：清空并重建当前知识库集合，方便反复实验和重新导入文档。

## 技术栈

- Python
- FastAPI
- OpenAI SDK
- ChromaDB
- Pydantic

## 项目价值

这个项目已经不只是“能跑的 RAG Demo”，而是一个具备知识库入库、检索、重置能力的 RAG 微服务雏形，适合作为 AI Engineer 学习阶段的作品集项目。

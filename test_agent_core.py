import json
from types import SimpleNamespace

from app.agent import agent_core
from app.agent.agent_core import _append_references, run_agent


def test_append_references_adds_sources_from_knowledge_results():
    tool_result = json.dumps(
        {
            "results": [
                {
                    "metadata": {
                        "filename": "company_rules.md",
                        "chunk_index": 1,
                    },
                    "distance": 0.42,
                }
            ]
        },
        ensure_ascii=False,
    )

    answer = _append_references("可以报销，但需要按制度提交。", [tool_result])

    assert "**引用来源**" in answer
    assert "company_rules.md（chunk 2，distance 0.4200）" in answer


def test_append_references_does_not_duplicate_existing_source_section():
    answer = "已有回答\n\n**引用来源**\n- company_rules.md"

    assert _append_references(answer, []) == answer


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        payload = {"role": "assistant"}

        if self.content is not None:
            payload["content"] = self.content

        if self.tool_calls is not None:
            payload["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in self.tool_calls
            ]

        return payload


def _fake_response(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_run_agent_returns_tool_trace_when_requested(monkeypatch):
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="get_weather", arguments='{"location": "北京"}'),
    )
    responses = [
        _fake_response(FakeMessage(tool_calls=[tool_call])),
        _fake_response(FakeMessage(content="北京今天晴朗。")),
    ]

    fake_completions = SimpleNamespace(create=lambda **kwargs: responses.pop(0))
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=fake_completions))
    monkeypatch.setattr(agent_core, "client", fake_client)
    monkeypatch.setitem(
        agent_core.TOOL_DISPATCH,
        "get_weather",
        lambda location: json.dumps(
            {"location": location, "condition": "晴朗"},
            ensure_ascii=False,
        ),
    )

    result = run_agent("北京天气怎么样？", include_trace=True)

    assert result == {
        "answer": "北京今天晴朗。",
        "trace": [
            {
                "tool_name": "get_weather",
                "arguments": {"location": "北京"},
                "result": {"location": "北京", "condition": "晴朗"},
            }
        ],
    }

import json

from app.agent.agent_core import _append_references


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

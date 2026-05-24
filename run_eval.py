import json
from pathlib import Path
from typing import Any

import requests


API_BASE = "http://127.0.0.1:8000"
EVAL_FILE = Path("eval_cases.json")
RESULT_FILE = Path("eval_results.json")


def call_chat_api(question: str) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE}/chat",
        json={"message": question, "session_id": "eval"},
        timeout=60,
    )
    response.raise_for_status()

    result = response.json()
    if result.get("code") != 200:
        raise RuntimeError(f"接口返回异常: {result}")

    data = result.get("data")
    if isinstance(data, str):
        return {"answer": data, "trace": [], "sources": []}

    if isinstance(data, dict):
        return {
            "answer": data.get("answer", ""),
            "trace": data.get("trace", []),
            "sources": data.get("sources", []),
        }

    return {"answer": str(data), "trace": [], "sources": []}


def contains_keyword(value: Any, keyword: str) -> bool:
    return keyword in json.dumps(value, ensure_ascii=False)


def check_case(case: dict, payload: dict[str, Any]) -> dict[str, Any]:
    answer = payload.get("answer", "")
    trace = payload.get("trace", [])
    sources = payload.get("sources", [])

    missing = [keyword for keyword in case.get("must_include", []) if keyword not in answer]
    forbidden_hit = [
        keyword for keyword in case.get("must_not_include", []) if keyword in answer
    ]
    trace_missing = [
        keyword
        for keyword in case.get("trace_must_include", [])
        if not contains_keyword(trace, keyword)
    ]
    sources_missing = [
        keyword
        for keyword in case.get("sources_must_include", [])
        if not contains_keyword(sources, keyword)
    ]

    passed = not missing and not forbidden_hit and not trace_missing and not sources_missing

    return {
        "id": case.get("id"),
        "question": case.get("question"),
        "passed": passed,
        "missing": missing,
        "forbidden_hit": forbidden_hit,
        "trace_missing": trace_missing,
        "sources_missing": sources_missing,
        "answer": answer,
        "trace": trace,
        "sources": sources,
    }


def main():
    if not EVAL_FILE.exists():
        raise FileNotFoundError(f"找不到评测文件: {EVAL_FILE}")

    cases = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
    results = []

    print("=" * 80)
    print("开始 Agent Eval")
    print("=" * 80)

    for case in cases:
        case_id = case.get("id")
        question = case.get("question")

        print(f"\n正在测试: {case_id}")
        print(f"问题: {question}")

        try:
            payload = call_chat_api(question)
            result = check_case(case, payload)
        except Exception as exc:
            result = {
                "id": case_id,
                "question": question,
                "passed": False,
                "missing": [],
                "forbidden_hit": [],
                "trace_missing": [],
                "sources_missing": [],
                "answer": "",
                "trace": [],
                "sources": [],
                "error": str(exc),
            }

        results.append(result)

        if result["passed"]:
            print("结果: PASS")
        else:
            print("结果: FAIL")
            if result.get("error"):
                print("错误:", result["error"])
            if result.get("missing"):
                print("缺少答案关键词:", result["missing"])
            if result.get("forbidden_hit"):
                print("命中禁止词:", result["forbidden_hit"])
            if result.get("trace_missing"):
                print("缺少 trace 关键词:", result["trace_missing"])
            if result.get("sources_missing"):
                print("缺少 sources 关键词:", result["sources_missing"])

        print("-" * 80)

    total = len(results)
    passed_count = sum(1 for result in results if result["passed"])
    failed_count = total - passed_count

    print("\n" + "=" * 80)
    print("Eval 汇总")
    print("=" * 80)
    print(f"总数: {total}")
    print(f"通过: {passed_count}")
    print(f"失败: {failed_count}")
    print(f"通过率: {passed_count / total * 100:.2f}%")

    RESULT_FILE.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n详细结果已写入 {RESULT_FILE}")

    if failed_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

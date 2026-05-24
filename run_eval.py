import json
import requests
from pathlib import Path


API_BASE = "http://127.0.0.1:8000"
EVAL_FILE = Path("eval_cases.json")


def call_chat_api(question: str) -> str:
    response = requests.post(
        f"{API_BASE}/chat",
        json={"message": question},
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    if result.get("code") != 200:
        raise RuntimeError(f"接口返回异常: {result}")

    data = result.get("data")

    # 兼容两种结构：
    # 1. data 是字符串
    # 2. data 是 {"answer": "...", "trace": [...]}
    if isinstance(data, str):
        return data

    if isinstance(data, dict):
        return data.get("answer", "")

    return str(data)


def check_case(case: dict, answer: str) -> dict:
    must_include = case.get("must_include", [])
    must_not_include = case.get("must_not_include", [])

    missing = []
    forbidden_hit = []

    for keyword in must_include:
        if keyword not in answer:
            missing.append(keyword)

    for keyword in must_not_include:
        if keyword in answer:
            forbidden_hit.append(keyword)

    passed = not missing and not forbidden_hit

    return {
        "id": case.get("id"),
        "question": case.get("question"),
        "passed": passed,
        "missing": missing,
        "forbidden_hit": forbidden_hit,
        "answer": answer,
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
            answer = call_chat_api(question)
            result = check_case(case, answer)
        except Exception as e:
            result = {
                "id": case_id,
                "question": question,
                "passed": False,
                "missing": [],
                "forbidden_hit": [],
                "answer": "",
                "error": str(e),
            }

        results.append(result)

        if result["passed"]:
            print("结果: PASS")
        else:
            print("结果: FAIL")

            if result.get("error"):
                print("错误:", result["error"])

            if result.get("missing"):
                print("缺少关键词:", result["missing"])

            if result.get("forbidden_hit"):
                print("命中禁止词:", result["forbidden_hit"])

        print("-" * 80)

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count

    print("\n" + "=" * 80)
    print("Eval 汇总")
    print("=" * 80)
    print(f"总数: {total}")
    print(f"通过: {passed_count}")
    print(f"失败: {failed_count}")
    print(f"通过率: {passed_count / total * 100:.2f}%")

    Path("eval_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n详细结果已写入: eval_results.json")

    if failed_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

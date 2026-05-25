import json
import sys

from app.tools.mcp_tools import handle_mcp_request


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(exc),
                },
            }

        print(json.dumps(response, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

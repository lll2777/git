from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the AI Data Analysis API.")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL.")
    parser.add_argument("--timeout", default=10, type=int)
    parser.add_argument(
        "--local-testclient",
        action="store_true",
        help="Use FastAPI TestClient instead of a running server.",
    )
    args = parser.parse_args()

    if args.local_testclient:
        smoke_local()
    else:
        smoke_http(base_url=args.url.rstrip("/"), timeout=args.timeout)


def smoke_local() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    api_root = repo_root / "apps" / "api"
    sys.path.insert(0, str(api_root))

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "ok", payload
    protected = client.get("/api/v1/datasets/demo/jobs")
    assert protected.status_code == 401, protected.text
    print(json.dumps({"health": payload, "protected_status": protected.status_code}, indent=2))


def smoke_http(*, base_url: str, timeout: int) -> None:
    payload = fetch_json(f"{base_url}/api/v1/health", timeout=timeout)
    if payload.get("status") != "ok":
        raise SystemExit(f"Unexpected health payload: {payload}")
    print(json.dumps({"health": payload}, indent=2))


def fetch_json(url: str, timeout: int) -> dict[str, object]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"Unable to reach {url}: {exc}") from exc


if __name__ == "__main__":
    main()

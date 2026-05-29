from __future__ import annotations

import asyncio
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPOSITORY_ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.ai.providers.mimo import MimoProvider  # noqa: E402


async def main() -> None:
    settings = get_settings()
    if not settings.mimo_api_key:
        raise SystemExit(
            "MIMO_API_KEY is not configured. Add it to .env, restart the API, "
            "then run this script again."
        )

    provider = MimoProvider(
        api_key=settings.mimo_api_key,
        base_url=settings.mimo_base_url,
        model=settings.mimo_model,
    )
    result = await provider.chat(
        messages=[
            {
                "role": "system",
                "content": "你是 AI 数据分析 SaaS 的连通性测试助手。请用中文简短回答。",
            },
            {
                "role": "user",
                "content": "请回复：MiMo Provider 连通性正常。",
            },
        ],
        metadata={"script": "test_mimo_provider"},
    )

    content = str(result.get("content") or "").strip()
    if not content:
        raise SystemExit("Mimo provider returned an empty response.")

    print("mimo provider ok")
    print(f"base_url: {settings.mimo_base_url}")
    print(f"model: {settings.mimo_model}")
    print(f"response: {content[:300]}")
    usage = result.get("usage")
    if usage:
        print(f"usage: {usage}")


if __name__ == "__main__":
    asyncio.run(main())

import json
from typing import Any

import httpx

from app.services.ai.providers.base import AIProvider


class MimoProvider(AIProvider):
    def __init__(self, api_key: str | None, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            return {
                "provider": "mimo",
                "model": self.model,
                "content": "MIMO_API_KEY is not configured. Configure it to enable live AI answers.",
                "tool_calls": [],
                "metadata": metadata or {},
            }

        request_payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            request_payload["tools"] = tools
            request_payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
            )
            response.raise_for_status()
            payload = response.json()

        message = payload.get("choices", [{}])[0].get("message", {})
        return {
            "provider": "mimo",
            "model": self.model,
            "content": message.get("content") or "",
            "tool_calls": message.get("tool_calls") or [],
            "usage": payload.get("usage") or {},
            "metadata": metadata or {},
        }

    async def analyze_data(
        self,
        dataset_profile: dict[str, Any],
        question: str | None = None,
    ) -> dict[str, Any]:
        return await self.chat(
            messages=[
                {"role": "system", "content": "Analyze the provided dataset profile."},
                {"role": "user", "content": str({"profile": dataset_profile, "question": question})},
            ],
            metadata={"capability": "analyze_data"},
        )

    async def generate_insight(
        self,
        dataset_profile: dict[str, Any],
        chart_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate business insights from data evidence. "
                        "Return JSON only with this shape: "
                        "{\"insights\":[{\"title\":\"...\",\"summary\":\"...\","
                        "\"insight_type\":\"summary|trend|anomaly|correlation|business|warning\","
                        "\"severity\":\"info|low|medium|high\","
                        "\"evidence\":{}}]}"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "profile": dataset_profile,
                            "chart_context": chart_context,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            metadata={"capability": "generate_insight"},
        )

    async def generate_chart_config(
        self,
        dataset_profile: dict[str, Any],
        intent: str | None = None,
    ) -> dict[str, Any]:
        return await self.chat(
            messages=[
                {"role": "system", "content": "Generate a safe chart configuration."},
                {"role": "user", "content": str({"profile": dataset_profile, "intent": intent})},
            ],
            metadata={"capability": "generate_chart_config"},
        )

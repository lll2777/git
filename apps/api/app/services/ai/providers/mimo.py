from typing import Any

import httpx

from app.services.ai.providers.base import AIProvider


class MimoProvider(AIProvider):
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
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
                "content": "MIMO_API_KEY is not configured.",
                "tool_calls": [],
                "metadata": metadata or {},
            }

        # The concrete Mimo API contract will be wired in STEP 7 after official
        # documentation is verified. The provider boundary is already enforced.
        async with httpx.AsyncClient(timeout=30) as client:
            _ = client
            raise NotImplementedError("Mimo API transport will be implemented in STEP 7.")

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
                {"role": "system", "content": "Generate business insights from data evidence."},
                {
                    "role": "user",
                    "content": str({"profile": dataset_profile, "chart_context": chart_context}),
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


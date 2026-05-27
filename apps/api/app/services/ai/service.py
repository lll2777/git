from app.services.ai.providers.base import AIProvider
from app.services.ai.providers.factory import create_ai_provider


class AIService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or create_ai_provider()

    async def chat(self, messages, tools=None, metadata=None):
        return await self._provider.chat(messages=messages, tools=tools, metadata=metadata)

    async def analyze_data(self, dataset_profile, question=None):
        return await self._provider.analyze_data(dataset_profile=dataset_profile, question=question)

    async def generate_insight(self, dataset_profile, chart_context=None):
        return await self._provider.generate_insight(
            dataset_profile=dataset_profile,
            chart_context=chart_context,
        )

    async def generate_chart_config(self, dataset_profile, intent=None):
        return await self._provider.generate_chart_config(
            dataset_profile=dataset_profile,
            intent=intent,
        )


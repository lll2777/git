from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def analyze_data(
        self,
        dataset_profile: dict[str, Any],
        question: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_insight(
        self,
        dataset_profile: dict[str, Any],
        chart_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_chart_config(
        self,
        dataset_profile: dict[str, Any],
        intent: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


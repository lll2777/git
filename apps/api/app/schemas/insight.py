from typing import Any

from pydantic import BaseModel


class InsightResponse(BaseModel):
    id: str
    dataset_id: str
    title: str
    summary: str
    insight_type: str
    severity: str
    evidence: dict[str, Any]
    provider: str | None = None
    model: str | None = None
    source: str
    created_at: str | None = None


class InsightListResponse(BaseModel):
    insights: list[InsightResponse]


class InsightGenerationResponse(BaseModel):
    insights: list[InsightResponse]

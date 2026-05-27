from typing import Any

from pydantic import BaseModel, Field

from app.schemas.chart import ChartResponse
from app.schemas.insight import InsightResponse


class DashboardCreateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)


class DashboardSummaryResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: str
    title: str
    description: str | None = None
    layout: dict[str, Any]
    status: str
    chart_count: int
    insight_count: int
    created_at: str | None = None
    updated_at: str | None = None


class DashboardResponse(DashboardSummaryResponse):
    charts: list[ChartResponse]
    insights: list[InsightResponse]


class DashboardListResponse(BaseModel):
    dashboards: list[DashboardSummaryResponse]

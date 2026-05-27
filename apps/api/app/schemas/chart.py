from typing import Any

from pydantic import BaseModel


class ChartResponse(BaseModel):
    id: str
    dataset_id: str
    title: str
    chart_type: str
    config: dict[str, Any]
    query_spec: dict[str, Any]
    created_by: str


class ChartRecommendationResponse(BaseModel):
    charts: list[ChartResponse]


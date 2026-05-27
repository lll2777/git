from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.charts import ChartRepository
from app.repositories.dashboards import DashboardRepository
from app.repositories.datasets import DatasetRepository
from app.repositories.insights import InsightRepository
from app.schemas.auth import AuthUser
from app.schemas.dashboard import (
    DashboardCreateRequest,
    DashboardListResponse,
    DashboardResponse,
)


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.dataset_repository = DatasetRepository(session)
        self.chart_repository = ChartRepository(session)
        self.insight_repository = InsightRepository(session)
        self.dashboard_repository = DashboardRepository(session)

    def save_from_dataset(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
        payload: DashboardCreateRequest,
    ) -> DashboardResponse:
        dataset = self.dataset_repository.get_dataset_for_user(
            dataset_id=dataset_id,
            user_id=user.id,
        )
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found for this workspace.",
            )

        charts = self.chart_repository.list_for_dataset(dataset_id=dataset_id, user_id=user.id)
        insights = self.insight_repository.list_for_dataset(dataset_id=dataset_id, user_id=user.id)
        if not charts and not insights:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Generate charts or insights before saving a dashboard.",
            )

        title = payload.title or f"{dataset.name} dashboard"
        layout = build_dashboard_layout(chart_count=len(charts), insight_count=len(insights))
        summary = self.dashboard_repository.create_from_items(
            workspace_id=dataset.workspace_id,
            dataset_id=dataset.id,
            owner_id=user.id,
            title=title,
            description=payload.description,
            layout=layout,
            chart_ids=[chart.id for chart in charts],
            insight_ids=[insight.id for insight in insights],
        )
        return DashboardResponse(
            **summary.model_dump(),
            charts=charts,
            insights=insights,
        )

    def list_for_dataset(self, *, user: AuthUser, dataset_id: str) -> DashboardListResponse:
        dataset = self.dataset_repository.get_dataset_for_user(
            dataset_id=dataset_id,
            user_id=user.id,
        )
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found for this workspace.",
            )
        return DashboardListResponse(
            dashboards=self.dashboard_repository.list_for_dataset(
                dataset_id=dataset_id,
                user_id=user.id,
            ),
        )

    def get_dashboard(self, *, user: AuthUser, dashboard_id: str) -> DashboardResponse:
        summary = self.dashboard_repository.get_for_user(
            dashboard_id=dashboard_id,
            user_id=user.id,
        )
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard was not found for this workspace.",
            )

        item_ids = self.dashboard_repository.list_item_ids(dashboard_id=dashboard_id)
        charts = self.chart_repository.list_for_dataset(
            dataset_id=summary.dataset_id,
            user_id=user.id,
        )
        insights = self.insight_repository.list_for_dataset(
            dataset_id=summary.dataset_id,
            user_id=user.id,
        )
        chart_order = {item_id: index for index, item_id in enumerate(item_ids["chart"])}
        insight_order = {item_id: index for index, item_id in enumerate(item_ids["insight"])}
        selected_charts = sorted(
            [chart for chart in charts if chart.id in chart_order],
            key=lambda chart: chart_order[chart.id],
        )
        selected_insights = sorted(
            [insight for insight in insights if insight.id in insight_order],
            key=lambda insight: insight_order[insight.id],
        )
        return DashboardResponse(
            **summary.model_dump(),
            charts=selected_charts,
            insights=selected_insights,
        )


def build_dashboard_layout(*, chart_count: int, insight_count: int) -> dict[str, object]:
    items = []
    for index in range(chart_count):
        items.append(
            {
                "type": "chart",
                "position": index,
                "grid": {
                    "x": (index % 2) * 6,
                    "y": (index // 2) * 5,
                    "w": 6,
                    "h": 5,
                },
            },
        )
    insight_start_y = ((chart_count + 1) // 2) * 5
    for index in range(insight_count):
        items.append(
            {
                "type": "insight",
                "position": chart_count + index,
                "grid": {
                    "x": 0,
                    "y": insight_start_y + index * 2,
                    "w": 12,
                    "h": 2,
                },
            },
        )
    return {"version": 1, "columns": 12, "items": items}

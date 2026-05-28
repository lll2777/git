import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.records import normalize_record, normalize_records
from app.schemas.dashboard import DashboardSummaryResponse


class DashboardRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_from_items(
        self,
        *,
        workspace_id: str,
        dataset_id: str,
        owner_id: str,
        title: str,
        description: str | None,
        layout: dict[str, Any],
        chart_ids: list[str],
        insight_ids: list[str],
    ) -> DashboardSummaryResponse:
        row = self.session.execute(
            text(
                """
                insert into dashboards (
                  id,
                  workspace_id,
                  dataset_id,
                  owner_id,
                  title,
                  description,
                  layout,
                  status
                )
                values (
                  gen_random_uuid(),
                  :workspace_id,
                  :dataset_id,
                  :owner_id,
                  :title,
                  :description,
                  cast(:layout as jsonb),
                  'active'
                )
                returning
                  id,
                  workspace_id,
                  dataset_id,
                  title,
                  description,
                  layout,
                  status,
                  created_at::text as created_at,
                  updated_at::text as updated_at
                """,
            ),
            {
                "workspace_id": workspace_id,
                "dataset_id": dataset_id,
                "owner_id": owner_id,
                "title": title,
                "description": description,
                "layout": json.dumps(layout),
            },
        ).mappings().one()

        position = 0
        for chart_id in chart_ids:
            self._insert_item(
                dashboard_id=str(row["id"]),
                item_type="chart",
                item_id=chart_id,
                position=position,
            )
            position += 1

        for insight_id in insight_ids:
            self._insert_item(
                dashboard_id=str(row["id"]),
                item_type="insight",
                item_id=insight_id,
                position=position,
            )
            position += 1

        self.session.commit()
        return DashboardSummaryResponse(
            **normalize_record(row),
            chart_count=len(chart_ids),
            insight_count=len(insight_ids),
        )

    def list_for_dataset(
        self,
        *,
        dataset_id: str,
        user_id: str,
    ) -> list[DashboardSummaryResponse]:
        rows = self.session.execute(
            text(
                """
                select
                  d.id,
                  d.workspace_id,
                  d.dataset_id,
                  d.title,
                  d.description,
                  d.layout,
                  d.status,
                  d.created_at::text as created_at,
                  d.updated_at::text as updated_at,
                  count(di.id) filter (where di.item_type = 'chart') as chart_count,
                  count(di.id) filter (where di.item_type = 'insight') as insight_count
                from dashboards d
                join workspace_members wm on wm.workspace_id = d.workspace_id
                left join dashboard_items di on di.dashboard_id = d.id
                where d.dataset_id = :dataset_id and wm.user_id = :user_id
                group by d.id
                order by d.updated_at desc
                """,
            ),
            {"dataset_id": dataset_id, "user_id": user_id},
        ).mappings().all()
        return [DashboardSummaryResponse(**row) for row in normalize_records(rows)]

    def get_for_user(
        self,
        *,
        dashboard_id: str,
        user_id: str,
    ) -> DashboardSummaryResponse | None:
        row = self.session.execute(
            text(
                """
                select
                  d.id,
                  d.workspace_id,
                  d.dataset_id,
                  d.title,
                  d.description,
                  d.layout,
                  d.status,
                  d.created_at::text as created_at,
                  d.updated_at::text as updated_at,
                  count(di.id) filter (where di.item_type = 'chart') as chart_count,
                  count(di.id) filter (where di.item_type = 'insight') as insight_count
                from dashboards d
                join workspace_members wm on wm.workspace_id = d.workspace_id
                left join dashboard_items di on di.dashboard_id = d.id
                where d.id = :dashboard_id and wm.user_id = :user_id
                group by d.id
                limit 1
                """,
            ),
            {"dashboard_id": dashboard_id, "user_id": user_id},
        ).mappings().first()
        return DashboardSummaryResponse(**normalize_record(row)) if row else None

    def list_item_ids(self, *, dashboard_id: str) -> dict[str, list[str]]:
        rows = self.session.execute(
            text(
                """
                select item_type, item_id::text as item_id
                from dashboard_items
                where dashboard_id = :dashboard_id
                order by position asc, created_at asc
                """,
            ),
            {"dashboard_id": dashboard_id},
        ).mappings().all()
        result = {"chart": [], "insight": []}
        for row in rows:
            if row["item_type"] in result:
                result[row["item_type"]].append(row["item_id"])
        return result

    def _insert_item(
        self,
        *,
        dashboard_id: str,
        item_type: str,
        item_id: str,
        position: int,
    ) -> None:
        self.session.execute(
            text(
                """
                insert into dashboard_items (
                  id,
                  dashboard_id,
                  item_type,
                  item_id,
                  position
                )
                values (
                  gen_random_uuid(),
                  :dashboard_id,
                  :item_type,
                  :item_id,
                  :position
                )
                """,
            ),
            {
                "dashboard_id": dashboard_id,
                "item_type": item_type,
                "item_id": item_id,
                "position": position,
            },
        )

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.records import normalize_record, normalize_records
from app.schemas.chart import ChartResponse


class ChartRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_recommendations(
        self,
        *,
        dataset_id: str,
        recommendations: list[dict[str, Any]],
    ) -> list[ChartResponse]:
        self.session.execute(
            text(
                """
                delete from charts
                where dataset_id = :dataset_id and created_by = 'system'
                """,
            ),
            {"dataset_id": dataset_id},
        )

        rows = []
        for recommendation in recommendations:
            row = self.session.execute(
                text(
                    """
                    insert into charts (
                      id,
                      dataset_id,
                      title,
                      chart_type,
                      config,
                      query_spec,
                      created_by
                    )
                    values (
                      gen_random_uuid(),
                      :dataset_id,
                      :title,
                      :chart_type,
                      cast(:config as jsonb),
                      cast(:query_spec as jsonb),
                      'system'
                    )
                    returning id, dataset_id, title, chart_type, config, query_spec, created_by
                    """,
                ),
                {
                    "dataset_id": dataset_id,
                    "title": recommendation["title"],
                    "chart_type": recommendation["chart_type"],
                    "config": json.dumps(recommendation["config"]),
                    "query_spec": json.dumps(recommendation["query_spec"]),
                },
            ).mappings().one()
            rows.append(ChartResponse(**normalize_record(row)))

        self.session.commit()
        return rows

    def list_for_dataset(self, *, dataset_id: str, user_id: str) -> list[ChartResponse]:
        rows = self.session.execute(
            text(
                """
                select c.id, c.dataset_id, c.title, c.chart_type, c.config, c.query_spec, c.created_by
                from charts c
                join datasets d on d.id = c.dataset_id
                join workspace_members wm on wm.workspace_id = d.workspace_id
                where c.dataset_id = :dataset_id and wm.user_id = :user_id
                order by c.created_at asc
                """,
            ),
            {"dataset_id": dataset_id, "user_id": user_id},
        ).mappings().all()
        return [ChartResponse(**row) for row in normalize_records(rows)]

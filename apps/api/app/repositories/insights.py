import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.records import normalize_record, normalize_records
from app.schemas.insight import InsightResponse


class InsightRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def replace_generated_insights(
        self,
        *,
        dataset_id: str,
        workspace_id: str,
        insights: list[dict[str, Any]],
    ) -> list[InsightResponse]:
        self.session.execute(
            text(
                """
                delete from insights
                where dataset_id = :dataset_id and source in ('deterministic', 'ai')
                """,
            ),
            {"dataset_id": dataset_id},
        )

        rows = []
        for insight in insights:
            row = self.session.execute(
                text(
                    """
                    insert into insights (
                      id,
                      workspace_id,
                      dataset_id,
                      title,
                      summary,
                      insight_type,
                      severity,
                      evidence,
                      provider,
                      model,
                      source
                    )
                    values (
                      gen_random_uuid(),
                      :workspace_id,
                      :dataset_id,
                      :title,
                      :summary,
                      :insight_type,
                      :severity,
                      cast(:evidence as jsonb),
                      :provider,
                      :model,
                      :source
                    )
                    returning
                      id,
                      dataset_id,
                      title,
                      summary,
                      insight_type,
                      severity,
                      evidence,
                      provider,
                      model,
                      source,
                      created_at::text as created_at
                    """,
                ),
                {
                    "workspace_id": workspace_id,
                    "dataset_id": dataset_id,
                    "title": insight["title"],
                    "summary": insight["summary"],
                    "insight_type": insight["insight_type"],
                    "severity": insight["severity"],
                    "evidence": json.dumps(insight.get("evidence") or {}),
                    "provider": insight.get("provider"),
                    "model": insight.get("model"),
                    "source": insight["source"],
                },
            ).mappings().one()
            rows.append(InsightResponse(**normalize_record(row)))

        self.session.commit()
        return rows

    def list_for_dataset(self, *, dataset_id: str, user_id: str) -> list[InsightResponse]:
        rows = self.session.execute(
            text(
                """
                select
                  i.id,
                  i.dataset_id,
                  i.title,
                  i.summary,
                  i.insight_type,
                  i.severity,
                  i.evidence,
                  i.provider,
                  i.model,
                  i.source,
                  i.created_at::text as created_at
                from insights i
                join datasets d on d.id = i.dataset_id
                join workspace_members wm on wm.workspace_id = d.workspace_id
                where i.dataset_id = :dataset_id and wm.user_id = :user_id
                order by
                  case i.severity
                    when 'high' then 1
                    when 'medium' then 2
                    when 'low' then 3
                    else 4
                  end,
                  i.created_at desc
                """,
            ),
            {"dataset_id": dataset_id, "user_id": user_id},
        ).mappings().all()
        return [InsightResponse(**row) for row in normalize_records(rows)]

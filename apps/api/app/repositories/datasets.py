import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.records import normalize_record, normalize_records
from app.schemas.dataset import (
    DatasetColumnProfile,
    DatasetPreviewResponse,
    DatasetProfileResponse,
    DatasetResponse,
)


class DatasetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_default_workspace_id(self, user_id: str) -> str | None:
        row = self.session.execute(
            text(
                """
                select workspace_id
                from workspace_members
                where user_id = :user_id
                order by created_at asc
                limit 1
                """,
            ),
            {"user_id": user_id},
        ).mappings().first()
        return str(row["workspace_id"]) if row else None

    def user_can_access_workspace(self, user_id: str, workspace_id: str) -> bool:
        row = self.session.execute(
            text(
                """
                select 1
                from workspace_members
                where user_id = :user_id and workspace_id = :workspace_id
                limit 1
                """,
            ),
            {"user_id": user_id, "workspace_id": workspace_id},
        ).first()
        return row is not None

    def create_dataset(
        self,
        *,
        dataset_id: str,
        workspace_id: str,
        owner_id: str,
        name: str,
        bucket: str,
        path: str,
        original_filename: str,
        content_type: str,
        size_bytes: int,
    ) -> DatasetResponse:
        row = self.session.execute(
            text(
                """
                insert into datasets (
                  id,
                  workspace_id,
                  owner_id,
                  name,
                  status,
                  storage_bucket,
                  storage_path,
                  original_filename,
                  content_type,
                  size_bytes
                )
                values (
                  :id,
                  :workspace_id,
                  :owner_id,
                  :name,
                  'created',
                  :storage_bucket,
                  :storage_path,
                  :original_filename,
                  :content_type,
                  :size_bytes
                )
                returning
                  id,
                  workspace_id,
                  owner_id,
                  name,
                  status,
                  row_count,
                  column_count,
                  storage_bucket,
                  storage_path,
                  original_filename,
                  content_type,
                  size_bytes,
                  error_message
                """,
            ),
            {
                "id": dataset_id,
                "workspace_id": workspace_id,
                "owner_id": owner_id,
                "name": name,
                "storage_bucket": bucket,
                "storage_path": path,
                "original_filename": original_filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
            },
        ).mappings().one()
        self.session.commit()
        return DatasetResponse(**normalize_record(row))

    def confirm_upload(
        self,
        *,
        dataset_id: str,
        user_id: str,
        size_bytes: int | None,
        content_type: str | None,
    ) -> DatasetResponse | None:
        row = self.session.execute(
            text(
                """
                update datasets
                set
                  status = 'uploaded',
                  size_bytes = coalesce(:size_bytes, size_bytes),
                  content_type = coalesce(:content_type, content_type),
                  updated_at = now()
                where id = :dataset_id and owner_id = :user_id
                returning
                  id,
                  workspace_id,
                  owner_id,
                  name,
                  status,
                  row_count,
                  column_count,
                  storage_bucket,
                  storage_path,
                  original_filename,
                  content_type,
                  size_bytes,
                  error_message
                """,
            ),
            {
                "dataset_id": dataset_id,
                "user_id": user_id,
                "size_bytes": size_bytes,
                "content_type": content_type,
            },
        ).mappings().first()
        self.session.commit()
        return DatasetResponse(**normalize_record(row)) if row else None

    def list_datasets(self, *, user_id: str, workspace_id: str | None) -> list[DatasetResponse]:
        resolved_workspace_id = workspace_id or self.get_default_workspace_id(user_id)
        if not resolved_workspace_id:
            return []

        rows = self.session.execute(
            text(
                """
                select
                  d.id,
                  d.workspace_id,
                  d.owner_id,
                  d.name,
                  d.status,
                  d.row_count,
                  d.column_count,
                  d.storage_bucket,
                  d.storage_path,
                  d.original_filename,
                  d.content_type,
                  d.size_bytes,
                  d.error_message
                from datasets d
                join workspace_members wm on wm.workspace_id = d.workspace_id
                where wm.user_id = :user_id and d.workspace_id = :workspace_id
                order by d.created_at desc
                """,
            ),
            {"user_id": user_id, "workspace_id": resolved_workspace_id},
        ).mappings().all()
        return [DatasetResponse(**row) for row in normalize_records(rows)]

    def get_dataset_for_user(self, *, dataset_id: str, user_id: str) -> DatasetResponse | None:
        row = self.session.execute(
            text(
                """
                select
                  d.id,
                  d.workspace_id,
                  d.owner_id,
                  d.name,
                  d.status,
                  d.row_count,
                  d.column_count,
                  d.storage_bucket,
                  d.storage_path,
                  d.original_filename,
                  d.content_type,
                  d.size_bytes,
                  d.error_message
                from datasets d
                join workspace_members wm on wm.workspace_id = d.workspace_id
                where d.id = :dataset_id and wm.user_id = :user_id
                limit 1
                """,
            ),
            {"dataset_id": dataset_id, "user_id": user_id},
        ).mappings().first()
        return DatasetResponse(**normalize_record(row)) if row else None

    def mark_processing(self, *, dataset_id: str) -> None:
        self.session.execute(
            text(
                """
                update datasets
                set status = 'processing', error_message = null, updated_at = now()
                where id = :dataset_id
                """,
            ),
            {"dataset_id": dataset_id},
        )
        self.session.commit()

    def mark_failed(self, *, dataset_id: str, error_message: str) -> DatasetResponse | None:
        row = self.session.execute(
            text(
                """
                update datasets
                set status = 'failed', error_message = :error_message, updated_at = now()
                where id = :dataset_id
                returning
                  id,
                  workspace_id,
                  owner_id,
                  name,
                  status,
                  row_count,
                  column_count,
                  storage_bucket,
                  storage_path,
                  original_filename,
                  content_type,
                  size_bytes,
                  error_message
                """,
            ),
            {"dataset_id": dataset_id, "error_message": error_message[:1000]},
        ).mappings().first()
        self.session.commit()
        return DatasetResponse(**normalize_record(row)) if row else None

    def save_analysis(
        self,
        *,
        dataset_id: str,
        row_count: int,
        column_count: int,
        columns: list[DatasetColumnProfile],
        preview_columns: list[str],
        preview_rows: list[dict[str, Any]],
        summary: dict[str, Any],
        missing_values: dict[str, Any],
        outliers: dict[str, Any],
        correlations: dict[str, Any],
        time_series: dict[str, Any],
        categorical_aggregates: dict[str, Any],
    ) -> DatasetResponse:
        dataset_row = self.session.execute(
            text(
                """
                update datasets
                set
                  status = 'ready',
                  row_count = :row_count,
                  column_count = :column_count,
                  error_message = null,
                  updated_at = now()
                where id = :dataset_id
                returning
                  id,
                  workspace_id,
                  owner_id,
                  name,
                  status,
                  row_count,
                  column_count,
                  storage_bucket,
                  storage_path,
                  original_filename,
                  content_type,
                  size_bytes,
                  error_message
                """,
            ),
            {
                "dataset_id": dataset_id,
                "row_count": row_count,
                "column_count": column_count,
            },
        ).mappings().one()

        self.session.execute(text("delete from dataset_columns where dataset_id = :dataset_id"), {"dataset_id": dataset_id})
        for column in columns:
            self.session.execute(
                text(
                    """
                    insert into dataset_columns (
                      id,
                      dataset_id,
                      name,
                      original_name,
                      data_type,
                      semantic_type,
                      nullable,
                      missing_count,
                      unique_count,
                      min_value,
                      max_value,
                      mean_value,
                      median_value,
                      stddev_value,
                      profile
                    )
                    values (
                      gen_random_uuid(),
                      :dataset_id,
                      :name,
                      :original_name,
                      :data_type,
                      :semantic_type,
                      :nullable,
                      :missing_count,
                      :unique_count,
                      :min_value,
                      :max_value,
                      :mean_value,
                      :median_value,
                      :stddev_value,
                      cast(:profile as jsonb)
                    )
                    """,
                ),
                {
                    "dataset_id": dataset_id,
                    "name": column.name,
                    "original_name": column.original_name,
                    "data_type": column.data_type,
                    "semantic_type": column.semantic_type,
                    "nullable": column.nullable,
                    "missing_count": column.missing_count,
                    "unique_count": column.unique_count,
                    "min_value": column.min_value,
                    "max_value": column.max_value,
                    "mean_value": column.mean_value,
                    "median_value": column.median_value,
                    "stddev_value": column.stddev_value,
                    "profile": json.dumps(column.profile),
                },
            )

        self.session.execute(
            text(
                """
                insert into dataset_profiles (
                  dataset_id,
                  summary,
                  missing_values,
                  outliers,
                  correlations,
                  time_series,
                  categorical_aggregates,
                  generated_at
                )
                values (
                  :dataset_id,
                  cast(:summary as jsonb),
                  cast(:missing_values as jsonb),
                  cast(:outliers as jsonb),
                  cast(:correlations as jsonb),
                  cast(:time_series as jsonb),
                  cast(:categorical_aggregates as jsonb),
                  now()
                )
                on conflict (dataset_id) do update set
                  summary = excluded.summary,
                  missing_values = excluded.missing_values,
                  outliers = excluded.outliers,
                  correlations = excluded.correlations,
                  time_series = excluded.time_series,
                  categorical_aggregates = excluded.categorical_aggregates,
                  generated_at = now()
                """,
            ),
            {
                "dataset_id": dataset_id,
                "summary": json.dumps(summary),
                "missing_values": json.dumps(missing_values),
                "outliers": json.dumps(outliers),
                "correlations": json.dumps(correlations),
                "time_series": json.dumps(time_series),
                "categorical_aggregates": json.dumps(categorical_aggregates),
            },
        )

        self.session.execute(
            text(
                """
                insert into dataset_previews (dataset_id, columns, rows, generated_at)
                values (:dataset_id, cast(:columns as jsonb), cast(:rows as jsonb), now())
                on conflict (dataset_id) do update set
                  columns = excluded.columns,
                  rows = excluded.rows,
                  generated_at = now()
                """,
            ),
            {
                "dataset_id": dataset_id,
                "columns": json.dumps(preview_columns),
                "rows": json.dumps(preview_rows),
            },
        )

        self.session.commit()
        return DatasetResponse(**normalize_record(dataset_row))

    def get_profile(self, *, dataset_id: str, user_id: str) -> DatasetProfileResponse | None:
        dataset = self.get_dataset_for_user(dataset_id=dataset_id, user_id=user_id)
        if not dataset:
            return None

        profile_row = self.session.execute(
            text(
                """
                select
                  summary,
                  missing_values,
                  outliers,
                  correlations,
                  time_series,
                  categorical_aggregates
                from dataset_profiles
                where dataset_id = :dataset_id
                """,
            ),
            {"dataset_id": dataset_id},
        ).mappings().first()
        if not profile_row:
            return None

        column_rows = self.session.execute(
            text(
                """
                select
                  name,
                  original_name,
                  data_type,
                  semantic_type,
                  nullable,
                  missing_count,
                  unique_count,
                  min_value,
                  max_value,
                  mean_value,
                  median_value,
                  stddev_value,
                  profile
                from dataset_columns
                where dataset_id = :dataset_id
                order by created_at asc
                """,
            ),
            {"dataset_id": dataset_id},
        ).mappings().all()

        return DatasetProfileResponse(
            dataset=dataset,
            columns=[DatasetColumnProfile(**row) for row in normalize_records(column_rows)],
            summary=profile_row["summary"],
            missing_values=profile_row["missing_values"],
            outliers=profile_row["outliers"],
            correlations=profile_row["correlations"],
            time_series=profile_row["time_series"],
            categorical_aggregates=profile_row["categorical_aggregates"],
        )

    def get_preview(self, *, dataset_id: str, user_id: str) -> DatasetPreviewResponse | None:
        dataset = self.get_dataset_for_user(dataset_id=dataset_id, user_id=user_id)
        if not dataset:
            return None

        row = self.session.execute(
            text(
                """
                select columns, rows
                from dataset_previews
                where dataset_id = :dataset_id
                """,
            ),
            {"dataset_id": dataset_id},
        ).mappings().first()
        if not row:
            return None

        rows = row["rows"]
        return DatasetPreviewResponse(
            dataset_id=dataset_id,
            columns=row["columns"],
            rows=rows,
            row_count=len(rows),
        )

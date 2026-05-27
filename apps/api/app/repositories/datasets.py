from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.dataset import DatasetResponse


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
        return DatasetResponse(**row)

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
        return DatasetResponse(**row) if row else None

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
        return [DatasetResponse(**row) for row in rows]


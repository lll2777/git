import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.records import normalize_record, normalize_records
from app.schemas.ai import AIConversationResponse, AIMessageResponse


class AIConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_user(
        self,
        *,
        conversation_id: str,
        user_id: str,
    ) -> AIConversationResponse | None:
        row = self.session.execute(
            text(
                """
                select c.id, c.dataset_id, c.title, c.status
                from ai_conversations c
                join datasets d on d.id = c.dataset_id
                join workspace_members wm on wm.workspace_id = d.workspace_id
                where c.id = :conversation_id and wm.user_id = :user_id
                limit 1
                """,
            ),
            {"conversation_id": conversation_id, "user_id": user_id},
        ).mappings().first()
        return AIConversationResponse(**normalize_record(row)) if row else None

    def create(
        self,
        *,
        dataset_id: str,
        workspace_id: str,
        owner_id: str,
        title: str,
    ) -> AIConversationResponse:
        row = self.session.execute(
            text(
                """
                insert into ai_conversations (
                  id,
                  workspace_id,
                  dataset_id,
                  owner_id,
                  title,
                  status
                )
                values (
                  gen_random_uuid(),
                  :workspace_id,
                  :dataset_id,
                  :owner_id,
                  :title,
                  'active'
                )
                returning id, dataset_id, title, status
                """,
            ),
            {
                "workspace_id": workspace_id,
                "dataset_id": dataset_id,
                "owner_id": owner_id,
                "title": title,
            },
        ).mappings().one()
        self.session.commit()
        return AIConversationResponse(**normalize_record(row))

    def list_messages(
        self,
        *,
        conversation_id: str,
        limit: int = 20,
    ) -> list[AIMessageResponse]:
        rows = self.session.execute(
            text(
                """
                select
                  id,
                  conversation_id,
                  role,
                  content,
                  provider,
                  model,
                  metadata,
                  created_at::text as created_at
                from ai_messages
                where conversation_id = :conversation_id
                order by created_at desc
                limit :limit
                """,
            ),
            {"conversation_id": conversation_id, "limit": limit},
        ).mappings().all()
        return [AIMessageResponse(**row) for row in normalize_records(list(reversed(rows)))]

    def add_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        provider: str | None = None,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIMessageResponse:
        row = self.session.execute(
            text(
                """
                insert into ai_messages (
                  id,
                  conversation_id,
                  role,
                  content,
                  provider,
                  model,
                  metadata
                )
                values (
                  gen_random_uuid(),
                  :conversation_id,
                  :role,
                  :content,
                  :provider,
                  :model,
                  cast(:metadata as jsonb)
                )
                returning
                  id,
                  conversation_id,
                  role,
                  content,
                  provider,
                  model,
                  metadata,
                  created_at::text as created_at
                """,
            ),
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "provider": provider,
                "model": model,
                "metadata": json.dumps(metadata or {}),
            },
        ).mappings().one()
        self.session.commit()
        return AIMessageResponse(**normalize_record(row))

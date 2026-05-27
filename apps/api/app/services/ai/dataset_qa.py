import json
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.ai_conversations import AIConversationRepository
from app.repositories.charts import ChartRepository
from app.repositories.datasets import DatasetRepository
from app.schemas.ai import DatasetChatRequest, DatasetChatResponse
from app.schemas.auth import AuthUser
from app.schemas.dataset import DatasetProfileResponse, DatasetPreviewResponse
from app.services.ai.service import AIService


class DatasetQuestionService:
    def __init__(self, session: Session, ai_service: AIService | None = None) -> None:
        self.dataset_repository = DatasetRepository(session)
        self.chart_repository = ChartRepository(session)
        self.conversation_repository = AIConversationRepository(session)
        self.ai_service = ai_service or AIService()

    async def ask(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
        payload: DatasetChatRequest,
    ) -> DatasetChatResponse:
        profile = self.dataset_repository.get_profile(dataset_id=dataset_id, user_id=user.id)
        preview = self.dataset_repository.get_preview(dataset_id=dataset_id, user_id=user.id)
        if not profile or not preview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset profile and preview are required before AI Q&A.",
            )

        conversation = self._resolve_conversation(
            user=user,
            dataset_id=dataset_id,
            payload=payload,
            profile=profile,
        )
        self.conversation_repository.add_message(
            conversation_id=conversation.id,
            role="user",
            content=payload.question,
        )
        recent_messages = self.conversation_repository.list_messages(
            conversation_id=conversation.id,
            limit=12,
        )

        charts = self.chart_repository.list_for_dataset(dataset_id=dataset_id, user_id=user.id)
        ai_result = await self._call_ai(
            profile=profile,
            preview=preview,
            charts=[chart.model_dump() for chart in charts],
            recent_messages=recent_messages,
        )
        answer = self.conversation_repository.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_result.get("content") or "I could not generate an answer.",
            provider=ai_result.get("provider"),
            model=ai_result.get("model"),
            metadata={
                "usage": ai_result.get("usage") or {},
                "tool_calls": ai_result.get("tool_calls") or [],
                "provider_metadata": ai_result.get("metadata") or {},
            },
        )
        messages = self.conversation_repository.list_messages(
            conversation_id=conversation.id,
            limit=20,
        )
        return DatasetChatResponse(
            conversation=conversation,
            answer=answer,
            messages=messages,
            tool_calls=ai_result.get("tool_calls") or [],
        )

    def _resolve_conversation(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
        payload: DatasetChatRequest,
        profile: DatasetProfileResponse,
    ):
        if payload.conversation_id:
            conversation = self.conversation_repository.get_for_user(
                conversation_id=payload.conversation_id,
                user_id=user.id,
            )
            if conversation and conversation.dataset_id == dataset_id:
                return conversation
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI conversation was not found for this dataset.",
            )

        question_title = payload.question.strip().splitlines()[0][:80]
        title = question_title or f"Ask about {profile.dataset.name}"
        return self.conversation_repository.create(
            dataset_id=dataset_id,
            workspace_id=profile.dataset.workspace_id,
            owner_id=user.id,
            title=title,
        )

    async def _call_ai(
        self,
        *,
        profile: DatasetProfileResponse,
        preview: DatasetPreviewResponse,
        charts: list[dict[str, Any]],
        recent_messages,
    ) -> dict[str, Any]:
        try:
            return await self.ai_service.chat(
                messages=build_messages(
                    profile=profile,
                    preview=preview,
                    charts=charts,
                    recent_messages=recent_messages,
                ),
                tools=DATASET_QA_TOOLS,
                metadata={
                    "capability": "dataset_qa",
                    "dataset_id": profile.dataset.id,
                },
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI provider request failed with status {exc.response.status_code}.",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI provider is temporarily unavailable.",
            ) from exc


def build_messages(
    *,
    profile: DatasetProfileResponse,
    preview: DatasetPreviewResponse,
    charts: list[dict[str, Any]],
    recent_messages,
) -> list[dict[str, str]]:
    context = build_dataset_context(profile=profile, preview=preview, charts=charts)
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI data analyst inside a production SaaS product. "
                "Answer using only the provided dataset context. "
                "Be concise, mention uncertainty, and do not invent columns or rows. "
                "When helpful, cite the exact columns or chart configs you used."
            ),
        },
        {
            "role": "system",
            "content": f"Dataset context JSON:\n{json.dumps(context, ensure_ascii=False)}",
        },
    ]
    messages.extend(
        {"role": message.role, "content": message.content}
        for message in recent_messages
        if message.role in {"user", "assistant"}
    )
    return messages


def build_dataset_context(
    *,
    profile: DatasetProfileResponse,
    preview: DatasetPreviewResponse,
    charts: list[dict[str, Any]],
) -> dict[str, Any]:
    columns = [
        {
            "name": column.name,
            "data_type": column.data_type,
            "semantic_type": column.semantic_type,
            "missing_count": column.missing_count,
            "unique_count": column.unique_count,
            "profile": column.profile,
        }
        for column in profile.columns[:40]
    ]
    return {
        "dataset": {
            "id": profile.dataset.id,
            "name": profile.dataset.name,
            "row_count": profile.dataset.row_count,
            "column_count": profile.dataset.column_count,
        },
        "columns": columns,
        "summary": profile.summary,
        "missing_values": profile.missing_values,
        "outliers": profile.outliers,
        "correlations": profile.correlations,
        "time_series": profile.time_series,
        "categorical_aggregates": profile.categorical_aggregates,
        "preview_rows": preview.rows[:20],
        "charts": [
            {
                "title": chart["title"],
                "chart_type": chart["chart_type"],
                "query_spec": chart["query_spec"],
            }
            for chart in charts[:10]
        ],
    }


DATASET_QA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "describe_dataset_context",
            "description": "Inspect the dataset profile, inferred schema, preview rows, and saved chart configs already supplied in context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus": {
                        "type": "string",
                        "description": "The part of the dataset context to inspect, such as columns, missing_values, outliers, correlations, or charts.",
                    },
                },
                "required": ["focus"],
            },
        },
    },
]

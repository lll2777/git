import json
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.charts import ChartRepository
from app.repositories.datasets import DatasetRepository
from app.repositories.insights import InsightRepository
from app.schemas.auth import AuthUser
from app.schemas.dataset import DatasetProfileResponse, DatasetPreviewResponse
from app.schemas.insight import InsightGenerationResponse, InsightListResponse
from app.services.ai.dataset_qa import build_dataset_context
from app.services.ai.service import AIService


class InsightService:
    def __init__(self, session: Session, ai_service: AIService | None = None) -> None:
        self.dataset_repository = DatasetRepository(session)
        self.chart_repository = ChartRepository(session)
        self.insight_repository = InsightRepository(session)
        self.ai_service = ai_service or AIService()

    async def generate_insights(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
    ) -> InsightGenerationResponse:
        profile = self.dataset_repository.get_profile(dataset_id=dataset_id, user_id=user.id)
        preview = self.dataset_repository.get_preview(dataset_id=dataset_id, user_id=user.id)
        if not profile or not preview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset profile and preview are required before insight generation.",
            )

        charts = self.chart_repository.list_for_dataset(dataset_id=dataset_id, user_id=user.id)
        chart_context = [chart.model_dump() for chart in charts]
        generated = build_deterministic_insights(profile=profile, preview=preview)
        generated.extend(
            await self._generate_ai_insights(
                profile=profile,
                preview=preview,
                chart_context=chart_context,
            ),
        )

        insights = self.insight_repository.replace_generated_insights(
            dataset_id=dataset_id,
            workspace_id=profile.dataset.workspace_id,
            insights=generated[:8],
        )
        return InsightGenerationResponse(insights=insights)

    def list_insights(self, *, user: AuthUser, dataset_id: str) -> InsightListResponse:
        return InsightListResponse(
            insights=self.insight_repository.list_for_dataset(
                dataset_id=dataset_id,
                user_id=user.id,
            ),
        )

    async def _generate_ai_insights(
        self,
        *,
        profile: DatasetProfileResponse,
        preview: DatasetPreviewResponse,
        chart_context: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        context = build_dataset_context(
            profile=profile,
            preview=preview,
            charts=chart_context,
        )
        try:
            result = await self.ai_service.generate_insight(
                dataset_profile=context,
                chart_context={"charts": chart_context[:10]},
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

        parsed = parse_ai_insights(result.get("content") or "")
        if not parsed:
            parsed = [
                {
                    "title": "AI insight provider needs configuration",
                    "summary": result.get("content")
                    or "No AI insight content was returned by the provider.",
                    "insight_type": "warning",
                    "severity": "low",
                    "evidence": {"capability": "generate_insight"},
                },
            ]

        for insight in parsed:
            insight["provider"] = result.get("provider")
            insight["model"] = result.get("model")
            insight["source"] = "ai"
        return parsed[:3]


def build_deterministic_insights(
    *,
    profile: DatasetProfileResponse,
    preview: DatasetPreviewResponse,
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    row_count = profile.dataset.row_count or profile.summary.get("row_count")
    column_count = profile.dataset.column_count or profile.summary.get("column_count")
    insights.append(
        {
            "title": "Dataset is ready for analysis",
            "summary": f"{profile.dataset.name} contains {row_count} rows and {column_count} columns after parsing.",
            "insight_type": "summary",
            "severity": "info",
            "evidence": {
                "row_count": row_count,
                "column_count": column_count,
                "preview_rows": preview.row_count,
            },
            "source": "deterministic",
        },
    )

    missing_columns = [
        column
        for column in profile.columns
        if column.missing_count > 0
    ]
    if missing_columns:
        top_missing = sorted(
            missing_columns,
            key=lambda column: column.missing_count,
            reverse=True,
        )[:3]
        insights.append(
            {
                "title": "Missing values may affect analysis quality",
                "summary": ", ".join(
                    f"{column.name} has {column.missing_count} missing values"
                    for column in top_missing
                ),
                "insight_type": "warning",
                "severity": "medium",
                "evidence": {
                    column.name: column.missing_count for column in top_missing
                },
                "source": "deterministic",
            },
        )

    outlier_columns = [
        {"name": name, **value}
        for name, value in profile.outliers.items()
        if isinstance(value, dict) and int(value.get("outlier_count") or 0) > 0
    ]
    if outlier_columns:
        top_outlier = sorted(
            outlier_columns,
            key=lambda item: int(item.get("outlier_count") or 0),
            reverse=True,
        )[0]
        insights.append(
            {
                "title": "Outliers detected in numeric data",
                "summary": f"{top_outlier['name']} has {top_outlier.get('outlier_count')} values outside the IQR bounds.",
                "insight_type": "anomaly",
                "severity": "medium",
                "evidence": top_outlier,
                "source": "deterministic",
            },
        )

    strongest_correlation = find_strongest_correlation(profile.correlations)
    if strongest_correlation:
        insights.append(
            {
                "title": "Strong correlation found",
                "summary": (
                    f"{strongest_correlation['x']} and {strongest_correlation['y']} "
                    f"have correlation {strongest_correlation['value']}."
                ),
                "insight_type": "correlation",
                "severity": "low",
                "evidence": strongest_correlation,
                "source": "deterministic",
            },
        )

    if profile.time_series:
        insights.append(
            {
                "title": "Time-based fields are available",
                "summary": "The dataset includes date or time fields, so trend analysis and period comparisons are possible.",
                "insight_type": "trend",
                "severity": "info",
                "evidence": profile.time_series,
                "source": "deterministic",
            },
        )

    return insights


def parse_ai_insights(content: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(strip_json_fence(content))
    except json.JSONDecodeError:
        return []

    raw_insights = payload.get("insights") if isinstance(payload, dict) else payload
    if not isinstance(raw_insights, list):
        return []

    insights = []
    for raw in raw_insights:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "AI insight")[:140]
        summary = str(raw.get("summary") or raw.get("content") or "")[:2000]
        if not summary:
            continue
        insights.append(
            {
                "title": title,
                "summary": summary,
                "insight_type": normalize_choice(
                    raw.get("insight_type"),
                    {"summary", "trend", "anomaly", "correlation", "business", "warning"},
                    "business",
                ),
                "severity": normalize_choice(
                    raw.get("severity"),
                    {"info", "low", "medium", "high"},
                    "info",
                ),
                "evidence": raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {},
            },
        )
    return insights


def strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```json"):
        return stripped.removeprefix("```json").removesuffix("```").strip()
    if stripped.startswith("```"):
        return stripped.removeprefix("```").removesuffix("```").strip()
    return stripped


def normalize_choice(value: Any, allowed: set[str], fallback: str) -> str:
    normalized = str(value or "").lower()
    return normalized if normalized in allowed else fallback


def find_strongest_correlation(correlations: dict[str, Any]) -> dict[str, Any] | None:
    strongest: dict[str, Any] | None = None
    for x_key, values in correlations.items():
        if not isinstance(values, dict):
            continue
        for y_key, value in values.items():
            if x_key == y_key:
                continue
            try:
                numeric_value = round(float(value), 4)
            except (TypeError, ValueError):
                continue
            if abs(numeric_value) < 0.65:
                continue
            if strongest is None or abs(numeric_value) > abs(strongest["value"]):
                strongest = {"x": x_key, "y": y_key, "value": numeric_value}
    return strongest

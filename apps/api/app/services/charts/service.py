from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.charts import ChartRepository
from app.repositories.datasets import DatasetRepository
from app.schemas.auth import AuthUser
from app.schemas.chart import ChartRecommendationResponse
from app.services.charts.recommender import ChartRecommender


class ChartService:
    def __init__(self, session: Session) -> None:
        self.chart_repository = ChartRepository(session)
        self.dataset_repository = DatasetRepository(session)

    def recommend_charts(self, *, user: AuthUser, dataset_id: str) -> ChartRecommendationResponse:
        profile = self.dataset_repository.get_profile(dataset_id=dataset_id, user_id=user.id)
        preview = self.dataset_repository.get_preview(dataset_id=dataset_id, user_id=user.id)
        if not profile or not preview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset profile and preview are required before chart recommendation.",
            )

        recommendations = ChartRecommender().recommend(profile=profile, preview=preview)
        charts = self.chart_repository.save_recommendations(
            dataset_id=dataset_id,
            recommendations=recommendations,
        )
        return ChartRecommendationResponse(charts=charts)

    def list_charts(self, *, user: AuthUser, dataset_id: str) -> ChartRecommendationResponse:
        return ChartRecommendationResponse(
            charts=self.chart_repository.list_for_dataset(
                dataset_id=dataset_id,
                user_id=user.id,
            ),
        )


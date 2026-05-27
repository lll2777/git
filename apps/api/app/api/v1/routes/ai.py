from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.ai import DatasetChatRequest, DatasetChatResponse
from app.schemas.auth import AuthUser
from app.services.ai.dataset_qa import DatasetQuestionService

router = APIRouter(prefix="/datasets/{dataset_id}/ai")


@router.post("/chat", response_model=DatasetChatResponse)
async def ask_dataset_question(
    dataset_id: str,
    payload: DatasetChatRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetChatResponse:
    try:
        return await DatasetQuestionService(session).ask(
            user=current_user,
            dataset_id=dataset_id,
            payload=payload,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for AI Q&A.",
        ) from exc

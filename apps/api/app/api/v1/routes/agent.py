from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.agent import AgentRunListResponse, AgentRunRequest, AgentRunResponse
from app.schemas.auth import AuthUser
from app.services.agent import AgentService

router = APIRouter()


@router.post("/datasets/{dataset_id}/agent-runs", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
async def run_dataset_agent(
    dataset_id: str,
    payload: AgentRunRequest,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AgentRunResponse:
    try:
        return await AgentService(session).run_agent(
            user=current_user,
            dataset_id=dataset_id,
            payload=payload,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for agent execution.",
        ) from exc


@router.get("/datasets/{dataset_id}/agent-runs", response_model=AgentRunListResponse)
async def list_dataset_agent_runs(
    dataset_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AgentRunListResponse:
    try:
        return AgentService(session).list_runs(user=current_user, dataset_id=dataset_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for agent run lookup.",
        ) from exc


@router.get("/agent-runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    current_user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AgentRunResponse:
    try:
        return AgentService(session).get_run(user=current_user, run_id=run_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable for agent run lookup.",
        ) from exc

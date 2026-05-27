from typing import Any, Callable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.agent_runs import AgentRunRepository
from app.repositories.datasets import DatasetRepository
from app.schemas.agent import AgentRunListResponse, AgentRunRequest, AgentRunResponse
from app.schemas.auth import AuthUser
from app.schemas.dashboard import DashboardCreateRequest
from app.services.charts.service import ChartService
from app.services.dashboards import DashboardService
from app.services.insights import InsightService
from app.services.jobs import JobService


class AgentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.dataset_repository = DatasetRepository(session)
        self.agent_repository = AgentRunRepository(session)

    async def run_agent(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
        payload: AgentRunRequest,
    ) -> AgentRunResponse:
        dataset = self.dataset_repository.get_dataset_for_user(
            dataset_id=dataset_id,
            user_id=user.id,
        )
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found.",
            )

        run = self.agent_repository.create_run(
            workspace_id=dataset.workspace_id,
            dataset_id=dataset.id,
            owner_id=user.id,
            objective=payload.objective,
        )

        try:
            result = await self._execute_workflow(
                user=user,
                dataset_id=dataset.id,
                objective=payload.objective,
                run_id=run.id,
            )
            return self.agent_repository.mark_run_succeeded(
                run_id=run.id,
                result=result,
            )
        except HTTPException as exc:
            self.agent_repository.mark_run_failed(
                run_id=run.id,
                error_message=str(exc.detail),
            )
            raise
        except Exception as exc:
            failed = self.agent_repository.mark_run_failed(
                run_id=run.id,
                error_message=str(exc),
            )
            failed.steps = self.agent_repository.list_steps(run_id=run.id)
            return failed

    def list_runs(self, *, user: AuthUser, dataset_id: str) -> AgentRunListResponse:
        dataset = self.dataset_repository.get_dataset_for_user(
            dataset_id=dataset_id,
            user_id=user.id,
        )
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset was not found.",
            )
        return AgentRunListResponse(
            runs=self.agent_repository.list_for_dataset(
                dataset_id=dataset_id,
                user_id=user.id,
            ),
        )

    def get_run(self, *, user: AuthUser, run_id: str) -> AgentRunResponse:
        run = self.agent_repository.get_for_user(run_id=run_id, user_id=user.id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent run was not found.",
            )
        return run

    async def _execute_workflow(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
        objective: str,
        run_id: str,
    ) -> dict[str, Any]:
        normalized = objective.strip().lower().replace(" ", "_")
        if normalized in {"prepare_dashboard", "dashboard", "full_analysis"}:
            return await self._prepare_dashboard(user=user, dataset_id=dataset_id, run_id=run_id)
        if normalized in {"refresh_analysis", "queue_analysis"}:
            return self._run_tool(
                run_id=run_id,
                step_name="queue_analysis_job",
                input_payload={"dataset_id": dataset_id},
                tool=lambda: JobService(self.session)
                .enqueue_dataset_analysis(user=user, dataset_id=dataset_id)
                .model_dump(),
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported agent objective. Use prepare_dashboard or queue_analysis.",
        )

    async def _prepare_dashboard(
        self,
        *,
        user: AuthUser,
        dataset_id: str,
        run_id: str,
    ) -> dict[str, Any]:
        charts = self._run_tool(
            run_id=run_id,
            step_name="recommend_charts",
            input_payload={"dataset_id": dataset_id},
            tool=lambda: ChartService(self.session)
            .recommend_charts(user=user, dataset_id=dataset_id)
            .model_dump(),
        )
        insights = await self._run_async_tool(
            run_id=run_id,
            step_name="generate_insights",
            input_payload={"dataset_id": dataset_id},
            tool=lambda: InsightService(self.session)
            .generate_insights(user=user, dataset_id=dataset_id),
        )
        dashboard = self._run_tool(
            run_id=run_id,
            step_name="save_dashboard",
            input_payload={"dataset_id": dataset_id},
            tool=lambda: DashboardService(self.session)
            .save_from_dataset(
                user=user,
                dataset_id=dataset_id,
                payload=DashboardCreateRequest(title=None, description="Created by AI Agent."),
            )
            .model_dump(),
        )
        return {
            "objective": "prepare_dashboard",
            "chart_count": len(charts.get("charts", [])),
            "insight_count": len(insights.get("insights", [])),
            "dashboard_id": dashboard.get("id"),
        }

    def _run_tool(
        self,
        *,
        run_id: str,
        step_name: str,
        input_payload: dict[str, Any],
        tool: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        step = self.agent_repository.start_step(
            run_id=run_id,
            step_name=step_name,
            input_payload=input_payload,
        )
        try:
            output = tool()
        except Exception as exc:
            self.agent_repository.fail_step(step_id=step.id, error_message=str(exc))
            raise
        self.agent_repository.complete_step(step_id=step.id, output=output)
        return output

    async def _run_async_tool(
        self,
        *,
        run_id: str,
        step_name: str,
        input_payload: dict[str, Any],
        tool,
    ) -> dict[str, Any]:
        step = self.agent_repository.start_step(
            run_id=run_id,
            step_name=step_name,
            input_payload=input_payload,
        )
        try:
            result = await tool()
            output = result.model_dump()
        except Exception as exc:
            self.agent_repository.fail_step(step_id=step.id, error_message=str(exc))
            raise
        self.agent_repository.complete_step(step_id=step.id, output=output)
        return output

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.agent import AgentRunResponse, AgentStepResponse


class AgentRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(
        self,
        *,
        workspace_id: str,
        dataset_id: str,
        owner_id: str,
        objective: str,
    ) -> AgentRunResponse:
        row = self.session.execute(
            text(
                """
                insert into agent_runs (
                  id,
                  workspace_id,
                  dataset_id,
                  owner_id,
                  objective,
                  status,
                  result
                )
                values (
                  gen_random_uuid(),
                  :workspace_id,
                  :dataset_id,
                  :owner_id,
                  :objective,
                  'running',
                  '{}'::jsonb
                )
                returning
                  id,
                  workspace_id,
                  dataset_id,
                  objective,
                  status,
                  result,
                  error_message,
                  created_at::text as created_at,
                  updated_at::text as updated_at
                """,
            ),
            {
                "workspace_id": workspace_id,
                "dataset_id": dataset_id,
                "owner_id": owner_id,
                "objective": objective,
            },
        ).mappings().one()
        self.session.commit()
        return AgentRunResponse(**row, steps=[])

    def start_step(
        self,
        *,
        run_id: str,
        step_name: str,
        input_payload: dict[str, Any],
    ) -> AgentStepResponse:
        row = self.session.execute(
            text(
                """
                insert into agent_steps (
                  id,
                  run_id,
                  step_name,
                  status,
                  input,
                  output,
                  started_at
                )
                values (
                  gen_random_uuid(),
                  :run_id,
                  :step_name,
                  'running',
                  cast(:input as jsonb),
                  '{}'::jsonb,
                  now()
                )
                returning
                  id,
                  run_id,
                  step_name,
                  status,
                  input,
                  output,
                  error_message,
                  started_at::text as started_at,
                  completed_at::text as completed_at
                """,
            ),
            {
                "run_id": run_id,
                "step_name": step_name,
                "input": json.dumps(input_payload),
            },
        ).mappings().one()
        self.session.commit()
        return AgentStepResponse(**row)

    def complete_step(
        self,
        *,
        step_id: str,
        output: dict[str, Any],
    ) -> AgentStepResponse:
        return self._update_step(
            step_id=step_id,
            status="succeeded",
            output=output,
            error_message=None,
        )

    def fail_step(self, *, step_id: str, error_message: str) -> AgentStepResponse:
        return self._update_step(
            step_id=step_id,
            status="failed",
            output={},
            error_message=error_message[:1000],
        )

    def mark_run_succeeded(
        self,
        *,
        run_id: str,
        result: dict[str, Any],
    ) -> AgentRunResponse:
        return self._update_run(
            run_id=run_id,
            status="succeeded",
            result=result,
            error_message=None,
        )

    def mark_run_failed(self, *, run_id: str, error_message: str) -> AgentRunResponse:
        return self._update_run(
            run_id=run_id,
            status="failed",
            result={},
            error_message=error_message[:1000],
        )

    def get_for_user(self, *, run_id: str, user_id: str) -> AgentRunResponse | None:
        row = self.session.execute(
            text(
                """
                select
                  ar.id,
                  ar.workspace_id,
                  ar.dataset_id,
                  ar.objective,
                  ar.status,
                  ar.result,
                  ar.error_message,
                  ar.created_at::text as created_at,
                  ar.updated_at::text as updated_at
                from agent_runs ar
                join workspace_members wm on wm.workspace_id = ar.workspace_id
                where ar.id = :run_id and wm.user_id = :user_id
                limit 1
                """,
            ),
            {"run_id": run_id, "user_id": user_id},
        ).mappings().first()
        if not row:
            return None
        return AgentRunResponse(**row, steps=self.list_steps(run_id=run_id))

    def list_for_dataset(self, *, dataset_id: str, user_id: str) -> list[AgentRunResponse]:
        rows = self.session.execute(
            text(
                """
                select
                  ar.id,
                  ar.workspace_id,
                  ar.dataset_id,
                  ar.objective,
                  ar.status,
                  ar.result,
                  ar.error_message,
                  ar.created_at::text as created_at,
                  ar.updated_at::text as updated_at
                from agent_runs ar
                join workspace_members wm on wm.workspace_id = ar.workspace_id
                where ar.dataset_id = :dataset_id and wm.user_id = :user_id
                order by ar.created_at desc
                limit 10
                """,
            ),
            {"dataset_id": dataset_id, "user_id": user_id},
        ).mappings().all()
        return [
            AgentRunResponse(**row, steps=self.list_steps(run_id=str(row["id"])))
            for row in rows
        ]

    def list_steps(self, *, run_id: str) -> list[AgentStepResponse]:
        rows = self.session.execute(
            text(
                """
                select
                  id,
                  run_id,
                  step_name,
                  status,
                  input,
                  output,
                  error_message,
                  started_at::text as started_at,
                  completed_at::text as completed_at
                from agent_steps
                where run_id = :run_id
                order by started_at asc, created_at asc
                """,
            ),
            {"run_id": run_id},
        ).mappings().all()
        return [AgentStepResponse(**row) for row in rows]

    def _update_step(
        self,
        *,
        step_id: str,
        status: str,
        output: dict[str, Any],
        error_message: str | None,
    ) -> AgentStepResponse:
        row = self.session.execute(
            text(
                """
                update agent_steps
                set
                  status = :status,
                  output = cast(:output as jsonb),
                  error_message = :error_message,
                  completed_at = now()
                where id = :step_id
                returning
                  id,
                  run_id,
                  step_name,
                  status,
                  input,
                  output,
                  error_message,
                  started_at::text as started_at,
                  completed_at::text as completed_at
                """,
            ),
            {
                "step_id": step_id,
                "status": status,
                "output": json.dumps(output),
                "error_message": error_message,
            },
        ).mappings().one()
        self.session.commit()
        return AgentStepResponse(**row)

    def _update_run(
        self,
        *,
        run_id: str,
        status: str,
        result: dict[str, Any],
        error_message: str | None,
    ) -> AgentRunResponse:
        row = self.session.execute(
            text(
                """
                update agent_runs
                set
                  status = :status,
                  result = cast(:result as jsonb),
                  error_message = :error_message,
                  updated_at = now()
                where id = :run_id
                returning
                  id,
                  workspace_id,
                  dataset_id,
                  objective,
                  status,
                  result,
                  error_message,
                  created_at::text as created_at,
                  updated_at::text as updated_at
                """,
            ),
            {
                "run_id": run_id,
                "status": status,
                "result": json.dumps(result),
                "error_message": error_message,
            },
        ).mappings().one()
        self.session.commit()
        return AgentRunResponse(**row, steps=self.list_steps(run_id=run_id))

from typing import Any

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    objective: str = Field(default="prepare_dashboard", min_length=1, max_length=200)


class AgentStepResponse(BaseModel):
    id: str
    run_id: str
    step_name: str
    status: str
    input: dict[str, Any]
    output: dict[str, Any]
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class AgentRunResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: str
    objective: str
    status: str
    result: dict[str, Any]
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    steps: list[AgentStepResponse] = []


class AgentRunListResponse(BaseModel):
    runs: list[AgentRunResponse]

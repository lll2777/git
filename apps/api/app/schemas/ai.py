from typing import Any

from pydantic import BaseModel, Field


class DatasetChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class AIMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    metadata: dict[str, Any]
    created_at: str | None = None


class AIConversationResponse(BaseModel):
    id: str
    dataset_id: str
    title: str
    status: str


class DatasetChatResponse(BaseModel):
    conversation: AIConversationResponse
    answer: AIMessageResponse
    messages: list[AIMessageResponse]
    tool_calls: list[dict[str, Any]]

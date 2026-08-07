from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Natural-language business question",
    )


class QueryResponse(BaseModel):
    status: Literal["success", "clarification", "error"]
    message: Optional[str] = None
    sql: Optional[str] = None
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
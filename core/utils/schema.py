from pydantic import BaseModel, Field, field_validator
from typing import Union, List


class RankedTrend(BaseModel):
    id: int
    title: str
    score: float
    reason: str
    content_type: str

    @field_validator("score")
    def score_range(cls, v):
        if not (0 <= v <= 10):
            raise ValueError("Score must be between 0 and 10")
        return v

    @field_validator("content_type")
    def valid_content_type(cls, v):
        allowed = ["short", "medium", "thread"]
        if v not in allowed:
            raise ValueError(f"content_type must be one of {allowed}")
        return v


class GeneratedContent(BaseModel):
    content_type: str
    angle: str = Field(..., min_length=5)
    hook: str = Field(..., min_length=10, max_length=300)
    content: Union[str, List[str]]
    takeaway: str = Field(..., min_length=10, max_length=300)

    @field_validator("content_type")
    def validate_content_type(cls, v):
        allowed = ["short", "medium", "thread"]
        if v not in allowed:
            raise ValueError(f"Invalid content_type: {v}")
        return v

    @field_validator("content")
    def validate_content(cls, v, info):
        content_type = info.data.get("content_type")

        if content_type == "thread":
            if not isinstance(v, list):
                raise ValueError("Thread content must be a list")

            if len(v) < 2:
                raise ValueError("Thread must have at least 2 parts")

            if len(v) > 10:
                raise ValueError("Thread too long (max 10 parts)")

            for chunk in v:
                if not isinstance(chunk, str):
                    raise ValueError("Each thread chunk must be a string")

                if len(chunk) > 450:
                    raise ValueError("Each thread chunk must be ≤ 450 characters")

        else:
            if not isinstance(v, str):
                raise ValueError("Content must be a string")

            if content_type == "short" and len(v) > 250:
                raise ValueError("Short content must be ≤ 250 characters")

            if content_type == "medium" and len(v) > 450:
                raise ValueError("Medium content must be ≤ 450 characters")

            if len(v) < 10:
                raise ValueError("Content too short")

        return v


class RankedTrendList(BaseModel):
    trends: List[RankedTrend]
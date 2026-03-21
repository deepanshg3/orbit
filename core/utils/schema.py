from pydantic import BaseModel, Field, field_validator
from typing import List


class RankedTrend(BaseModel):
    id: int
    title: str
    score: float
    reason: str

    @field_validator("score")
    def score_range(cls, v):
        if not (0 <= v <= 10):
            raise ValueError("Score must be between 0 and 10")
        return v
    
class GeneratedContent(BaseModel):
    angle: str = Field(..., min_length=5)
    hook: str = Field(..., min_length=5)
    content: str = Field(..., min_length=20)
    takeaway: str = Field(..., min_length=5)


class RankedTrendList(BaseModel):
    trends: List[RankedTrend]
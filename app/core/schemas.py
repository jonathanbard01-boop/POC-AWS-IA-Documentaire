from pydantic import BaseModel
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str

class EngineResult(BaseModel):
    top_type: Optional[str] = None
    score: float = 0.0
    second_type: Optional[str] = None
    second_score: Optional[float] = None
    margin: Optional[float] = None

class Decision(BaseModel):
    status: str
    proposed_type: str
    risk_level: str
    requires_human_review: bool
    reasons: list[str]

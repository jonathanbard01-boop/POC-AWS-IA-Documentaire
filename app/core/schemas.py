from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    status: str
    content_type: Optional[str] = None
    size_bytes: int = 0
    local_path: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    result_s3_bucket: Optional[str] = None
    result_s3_key: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    final_type: Optional[str] = None
    final_decision: Optional[str] = None
    risk_level: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentRecord]


class DocumentResultResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    result_available: bool
    result: Optional[dict] = None


class ProcessingJob(BaseModel):
    job_id: str
    document_id: str
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None


class ProcessingJobResponse(BaseModel):
    job: ProcessingJob


class ProcessingQueueResponse(BaseModel):
    jobs: list[ProcessingJob]


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

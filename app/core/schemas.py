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


class CorpusDocumentSummary(BaseModel):
    document_type: str
    filename: str
    char_count: int
    word_count: int
    token_count: int
    preview: str
    active: bool = True
    version: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    updated_at: Optional[datetime] = None


class CorpusResponse(BaseModel):
    source: str
    document_count: int
    documents: list[CorpusDocumentSummary]


class CorpusTextUpsertRequest(BaseModel):
    text: str
    version: Optional[str] = None
    active: bool = True


class CorpusUpsertResponse(BaseModel):
    document_type: str
    filename: str
    active: bool
    version: str
    char_count: int
    word_count: int
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    updated_at: datetime


class ClassificationTestRequest(BaseModel):
    text: str


class ClassificationTestResponse(BaseModel):
    text_length: int
    bm25_result: EngineResult
    decision: Decision


class HumanValidationRequest(BaseModel):
    comment: Optional[str] = None


class HumanCorrectionRequest(BaseModel):
    corrected_type: str
    comment: Optional[str] = None


class HumanValidationRecord(BaseModel):
    correction_id: str
    document_id: str
    action: str
    previous_type: Optional[str] = None
    corrected_type: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanValidationResponse(BaseModel):
    document_id: str
    status: str
    final_type: Optional[str] = None
    correction: HumanValidationRecord
    result: dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.schemas import (
    DocumentListResponse,
    DocumentRecord,
    DocumentResultResponse,
    HealthResponse,
    ProcessingJobResponse,
    ProcessingQueueResponse,
    UploadResponse,
)
from app.services.document_analysis_service import analyze_document
from app.services.ingest_service import (
    create_document,
    get_document,
    get_document_result,
    list_documents,
)
from app.services.processing_queue_service import local_processing_queue

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="eva-poc-api", version="1.0.0")


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    document = await create_document(file)
    return UploadResponse(**document)


@router.get("/documents", response_model=DocumentListResponse)
def get_documents() -> DocumentListResponse:
    return DocumentListResponse(documents=list_documents())


@router.get("/documents/{document_id}", response_model=DocumentRecord)
def get_document_by_id(document_id: str) -> DocumentRecord:
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/documents/{document_id}/analyze", response_model=DocumentResultResponse)
def analyze_document_by_id(document_id: str) -> DocumentResultResponse:
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    result = analyze_document(document)
    return DocumentResultResponse(
        document_id=document.document_id,
        filename=document.filename,
        status=result["status"],
        result_available=True,
        result=result,
    )


@router.post("/documents/{document_id}/enqueue", response_model=ProcessingJobResponse)
def enqueue_document(document_id: str) -> ProcessingJobResponse:
    try:
        job = local_processing_queue.enqueue(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProcessingJobResponse(job=job)


@router.get("/processing/queue", response_model=ProcessingQueueResponse)
def get_processing_queue() -> ProcessingQueueResponse:
    return ProcessingQueueResponse(jobs=local_processing_queue.list_jobs())


@router.post("/processing/run-next", response_model=ProcessingJobResponse)
def run_next_processing_job() -> ProcessingJobResponse:
    job = local_processing_queue.run_next()
    if not job:
        raise HTTPException(status_code=404, detail="No queued job")
    return ProcessingJobResponse(job=job)


@router.get("/documents/{document_id}/result", response_model=DocumentResultResponse)
def get_result_by_document_id(document_id: str) -> DocumentResultResponse:
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    result = get_document_result(document_id)
    return DocumentResultResponse(
        document_id=document.document_id,
        filename=document.filename,
        status=document.status,
        result_available=result is not None,
        result=result,
    )


@router.get("/document-types")
def get_document_types():
    return [
        "formulaire_famille",
        "formulaire_logement",
        "facture_creche",
        "facture_centre_loisirs",
        "rib",
        "justificatif_domicile",
        "piece_identite",
        "document_inconnu",
    ]

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.schemas import (
    ClassificationTestRequest,
    ClassificationTestResponse,
    CorpusResponse,
    CorpusTextUpsertRequest,
    CorpusUpsertResponse,
    DocumentListResponse,
    DocumentRecord,
    DocumentResultResponse,
    HealthResponse,
    HumanCorrectionRequest,
    HumanValidationRequest,
    HumanValidationResponse,
    ProcessingJobResponse,
    ProcessingQueueResponse,
    UploadResponse,
)
from app.services.classification_diagnostic_service import classify_text_for_diagnostic, get_corpus_summary
from app.services.document_analysis_service import analyze_document
from app.services.human_validation_service import (
    HumanValidationError,
    correct_document,
    reject_document,
    validate_document,
)
from app.services.ingest_service import create_document, get_document, get_document_result, list_documents
from app.services.queue_selector import get_processing_queue as selected_processing_queue
from app.services.runtime_corpus_service import get_runtime_document_types, upsert_corpus_text

router = APIRouter()


def _human_validation_http_error(exc: HumanValidationError) -> HTTPException:
    message = str(exc)
    if "not found" in message.lower():
        return HTTPException(status_code=404, detail=message)
    return HTTPException(status_code=409, detail=message)


@router.get("/", response_class=HTMLResponse)
def backoffice() -> HTMLResponse:
    return HTMLResponse(
        """
        <html lang="fr">
          <head><meta charset="utf-8"><title>POC AWS IA Documentaire</title></head>
          <body>
            <h1>POC AWS IA Documentaire</h1>
            <p>API opérationnelle. Utiliser <a href="/docs">/docs</a> pour tester les endpoints.</p>
            <ul>
              <li>Corpus dynamique : <code>GET /corpus</code>, <code>PUT /corpus/{document_type}</code>, <code>POST /corpus/{document_type}/upload</code></li>
              <li>Diagnostic : <code>POST /classification/test</code></li>
              <li>Chaîne : upload, enqueue, worker, result, validate/correct/reject</li>
            </ul>
          </body>
        </html>
        """
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="eva-poc-api", version="2.0.0")


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
    if settings.is_aws:
        raise HTTPException(
            status_code=409,
            detail="Direct synchronous analysis is disabled in AWS mode. Use /enqueue and the worker.",
        )

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
        job = selected_processing_queue().enqueue(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProcessingJobResponse(job=job)


@router.get("/processing/queue", response_model=ProcessingQueueResponse)
def get_processing_queue() -> ProcessingQueueResponse:
    return ProcessingQueueResponse(jobs=selected_processing_queue().list_jobs())


@router.post("/processing/run-next", response_model=ProcessingJobResponse)
def run_next_processing_job() -> ProcessingJobResponse:
    if settings.is_aws:
        raise HTTPException(
            status_code=409,
            detail="Manual run-next is disabled in AWS mode. The ECS worker consumes SQS.",
        )

    job = selected_processing_queue().run_next()
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


@router.post("/documents/{document_id}/validate", response_model=HumanValidationResponse)
def validate_document_by_id(
    document_id: str,
    payload: HumanValidationRequest | None = None,
) -> HumanValidationResponse:
    try:
        return validate_document(document_id, comment=payload.comment if payload else None)
    except HumanValidationError as exc:
        raise _human_validation_http_error(exc) from exc


@router.post("/documents/{document_id}/correct", response_model=HumanValidationResponse)
def correct_document_by_id(document_id: str, payload: HumanCorrectionRequest) -> HumanValidationResponse:
    try:
        return correct_document(document_id, corrected_type=payload.corrected_type, comment=payload.comment)
    except HumanValidationError as exc:
        raise _human_validation_http_error(exc) from exc


@router.post("/documents/{document_id}/reject", response_model=HumanValidationResponse)
def reject_document_by_id(
    document_id: str,
    payload: HumanValidationRequest | None = None,
) -> HumanValidationResponse:
    try:
        return reject_document(document_id, comment=payload.comment if payload else None)
    except HumanValidationError as exc:
        raise _human_validation_http_error(exc) from exc


@router.get("/classification/corpus", response_model=CorpusResponse)
def get_classification_corpus() -> CorpusResponse:
    return get_corpus_summary()


@router.post("/classification/test", response_model=ClassificationTestResponse)
def test_classification(payload: ClassificationTestRequest) -> ClassificationTestResponse:
    return classify_text_for_diagnostic(payload.text)


@router.get("/corpus", response_model=CorpusResponse)
def get_corpus() -> CorpusResponse:
    return get_corpus_summary()


@router.put("/corpus/{document_type}", response_model=CorpusUpsertResponse)
def put_corpus_text(document_type: str, payload: CorpusTextUpsertRequest) -> CorpusUpsertResponse:
    try:
        return upsert_corpus_text(
            document_type,
            payload.text,
            version=payload.version,
            active=payload.active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/corpus/{document_type}/upload", response_model=CorpusUpsertResponse)
async def upload_corpus_file(
    document_type: str,
    file: UploadFile = File(...),
    version: str | None = None,
    active: bool = True,
) -> CorpusUpsertResponse:
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Corpus file must be UTF-8 text") from exc

    try:
        return upsert_corpus_text(document_type, text, version=version, active=active)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/document-types")
def get_document_types() -> list[str]:
    document_types = get_runtime_document_types()
    if document_types:
        return document_types
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

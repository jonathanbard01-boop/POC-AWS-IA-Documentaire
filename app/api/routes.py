from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.schemas import (
    DocumentListResponse,
    DocumentRecord,
    DocumentResultResponse,
    HealthResponse,
    UploadResponse,
)
from app.services.document_analysis_service import analyze_document
from app.services.ingest_service import (
    create_document,
    get_document,
    get_document_result,
    list_documents,
)

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

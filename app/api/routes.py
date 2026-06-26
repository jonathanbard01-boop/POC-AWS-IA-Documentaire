from fastapi import APIRouter, UploadFile, File
from app.core.schemas import HealthResponse, UploadResponse
from app.services.ingest_service import create_document

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="eva-poc-api", version="1.0.0")

@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    document = await create_document(file)
    return UploadResponse(**document)

@router.get("/document-types")
def list_document_types():
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

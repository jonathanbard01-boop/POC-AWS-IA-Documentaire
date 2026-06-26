from __future__ import annotations

from app.core.decision_engine import decide
from app.core.schemas import DocumentRecord, EngineResult
from app.services.bm25_classifier_service import get_default_bm25_classifier
from app.services.ocr_tesseract_service import extract_text
from app.storage.local_storage import local_document_store


def analyze_document(record: DocumentRecord) -> dict:
    """Run the first local analysis pipeline on one document.

    Pipeline V1 local:
    - read text or OCR image;
    - classify with BM25;
    - apply decision engine;
    - store result in the local document store.
    """

    if not record.local_path:
        raise ValueError("Document has no local path")

    ocr = extract_text(record.local_path)
    bm25 = get_default_bm25_classifier().classify(ocr["text"])
    graphic = EngineResult(top_type="document_inconnu", score=0.0)

    decision = decide(
        ocr_confidence=float(ocr["confidence"]),
        is_blank=ocr["word_count"] == 0,
        bm25=bm25,
        graphic=graphic,
    )

    result = {
        "document_id": record.document_id,
        "filename": record.filename,
        "status": decision.status,
        "final_type": decision.proposed_type,
        "final_decision": decision.status,
        "risk_level": decision.risk_level,
        "pages": [
            {
                "page_index": 1,
                "ocr": {
                    "confidence": ocr["confidence"],
                    "word_count": ocr["word_count"],
                    "text_excerpt": ocr["text"][:500],
                    "engine": ocr["engine"],
                    "error": ocr["error"],
                },
                "image_quality": {
                    "is_blank": ocr["word_count"] == 0,
                    "blur_score": None,
                    "quality_score": None,
                },
                "barcode": {
                    "found": False,
                    "value": None,
                    "type": None,
                    "coherent_with_ai": None,
                },
                "graphic_result": graphic.model_dump(),
                "bm25_result": bm25.model_dump(),
                "decision": decision.model_dump(),
            }
        ],
    }
    local_document_store.set_result(record.document_id, result)
    return result

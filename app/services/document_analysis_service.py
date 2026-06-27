from __future__ import annotations

from app.core.decision_engine import decide
from app.core.schemas import DocumentRecord, EngineResult
from app.services.image_preprocess_service import analyze_image_quality
from app.services.ocr_tesseract_service import extract_text
from app.services.runtime_corpus_service import classify_runtime_text
from app.storage.document_store import get_document_store


def analyze_document(record: DocumentRecord) -> dict:
    if not record.local_path:
        raise ValueError("Document has no local path")

    image_quality = analyze_image_quality(record.local_path)
    ocr = extract_text(record.local_path)
    bm25 = classify_runtime_text(ocr["text"])
    graphic = EngineResult(top_type="document_inconnu", score=0.0)

    is_blank = bool(image_quality["is_blank"]) if image_quality["is_blank"] is not None else ocr["word_count"] == 0

    decision = decide(
        ocr_confidence=float(ocr["confidence"]),
        is_blank=is_blank,
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
                    "is_image": image_quality["is_image"],
                    "is_blank": is_blank,
                    "blur_score": image_quality["blur_score"],
                    "quality_score": image_quality["quality_score"],
                    "error": image_quality["error"],
                },
                "barcode": {"found": False, "value": None, "type": None, "coherent_with_ai": None},
                "graphic_result": graphic.model_dump(),
                "bm25_result": bm25.model_dump(),
                "decision": decision.model_dump(),
            }
        ],
    }
    get_document_store().set_result(record.document_id, result)
    return result

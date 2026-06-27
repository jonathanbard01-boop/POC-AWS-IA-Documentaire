from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.core.decision_engine import UNKNOWN
from app.core.schemas import HumanValidationRecord, HumanValidationResponse
from app.storage.document_store import get_document_store


class HumanValidationError(ValueError):
    pass


def validate_document(document_id: str, *, comment: str | None = None) -> HumanValidationResponse:
    return _apply_human_decision(document_id, action="validate", corrected_type=None, comment=comment)


def correct_document(document_id: str, *, corrected_type: str, comment: str | None = None) -> HumanValidationResponse:
    if not corrected_type.strip():
        raise HumanValidationError("corrected_type is required")
    return _apply_human_decision(document_id, action="correct", corrected_type=corrected_type.strip(), comment=comment)


def reject_document(document_id: str, *, comment: str | None = None) -> HumanValidationResponse:
    return _apply_human_decision(document_id, action="reject", corrected_type=UNKNOWN, comment=comment)


def _apply_human_decision(
    document_id: str,
    *,
    action: str,
    corrected_type: str | None,
    comment: str | None,
) -> HumanValidationResponse:
    store = get_document_store()
    document = store.get_document(document_id)
    if not document:
        raise HumanValidationError("Document not found")

    result = store.get_result(document_id)
    if not result:
        raise HumanValidationError("Document result not available")

    previous_type = result.get("final_type") or document.final_type or UNKNOWN
    now = datetime.now(timezone.utc)

    if action == "validate":
        final_type = previous_type
        status = "validated"
        final_decision = "human_validated"
        risk_level = "low"
    elif action == "correct":
        final_type = corrected_type or previous_type
        status = "corrected"
        final_decision = "human_corrected"
        risk_level = "low"
    elif action == "reject":
        final_type = UNKNOWN
        status = "rejected"
        final_decision = "human_rejected"
        risk_level = "high"
    else:
        raise HumanValidationError(f"Unsupported human action: {action}")

    correction = HumanValidationRecord(
        correction_id=str(uuid4()),
        document_id=document_id,
        action=action,
        previous_type=previous_type,
        corrected_type=final_type,
        comment=comment,
        created_at=now,
    )

    payload = correction.model_dump(mode="json")
    result["status"] = status
    result["final_type"] = final_type
    result["final_decision"] = final_decision
    result["risk_level"] = risk_level
    result["human_validation"] = payload

    if result.get("pages"):
        result["pages"][0]["human_validation"] = payload

    store.set_result(document_id, result)
    if hasattr(store, "save_human_correction"):
        store.save_human_correction(correction)

    return HumanValidationResponse(
        document_id=document_id,
        status=status,
        final_type=final_type,
        correction=correction,
        result=result,
    )

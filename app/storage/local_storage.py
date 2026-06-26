from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.schemas import DocumentRecord


class LocalDocumentStore:
    """Simple in-process document store for local POC runs.

    This is intentionally not durable metadata storage. The AWS version will
    replace this service with S3 + DynamoDB + SQS.
    """

    def __init__(self, base_dir: str = "/tmp/eva-document-ai-poc") -> None:
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir / "input"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, DocumentRecord] = {}
        self._results: dict[str, dict] = {}

    async def save_upload(self, *, document_id: str, file: UploadFile) -> DocumentRecord:
        filename = file.filename or "unknown"
        target_dir = self.input_dir / document_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        content = await file.read()
        target_path.write_bytes(content)

        now = datetime.now(timezone.utc)
        record = DocumentRecord(
            document_id=document_id,
            filename=filename,
            status="uploaded",
            content_type=file.content_type,
            size_bytes=len(content),
            local_path=str(target_path),
            created_at=now,
            updated_at=now,
        )
        self._records[document_id] = record
        return record

    def list_documents(self) -> list[DocumentRecord]:
        return sorted(self._records.values(), key=lambda doc: doc.created_at, reverse=True)

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        return self._records.get(document_id)

    def set_result(self, document_id: str, result: dict) -> None:
        self._results[document_id] = result
        if document_id in self._records:
            record = self._records[document_id]
            self._records[document_id] = record.model_copy(
                update={
                    "status": result.get("status", record.status),
                    "updated_at": datetime.now(timezone.utc),
                    "final_type": result.get("final_type"),
                    "final_decision": result.get("final_decision"),
                    "risk_level": result.get("risk_level"),
                }
            )

    def get_result(self, document_id: str) -> Optional[dict]:
        return self._results.get(document_id)


local_document_store = LocalDocumentStore()

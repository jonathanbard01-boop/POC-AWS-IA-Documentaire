from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.schemas import DocumentRecord


class LocalDocumentStore:
    """Small filesystem-backed document store for local POC runs.

    The AWS version will replace this service with S3 + DynamoDB + SQS, but the
    local version intentionally persists metadata as JSON so the API and worker
    can be exercised in a more realistic way.
    """

    def __init__(self, base_dir: str = "/tmp/eva-document-ai-poc") -> None:
        self.base_dir = Path(base_dir)
        self.input_dir = self.base_dir / "input"
        self.records_dir = self.base_dir / "records"
        self.results_dir = self.base_dir / "results"
        for directory in (self.input_dir, self.records_dir, self.results_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, DocumentRecord] = {}
        self._results: dict[str, dict] = {}
        self._load_records()
        self._load_results()

    def _record_path(self, document_id: str) -> Path:
        return self.records_dir / f"{document_id}.json"

    def _result_path(self, document_id: str) -> Path:
        return self.results_dir / f"{document_id}.json"

    def _load_records(self) -> None:
        for path in self.records_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                record = DocumentRecord.model_validate(data)
                self._records[record.document_id] = record
            except Exception:
                continue

    def _load_results(self) -> None:
        for path in self.results_dir.glob("*.json"):
            try:
                document_id = path.stem
                self._results[document_id] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

    def _save_record(self, record: DocumentRecord) -> None:
        self._records[record.document_id] = record
        self._record_path(record.document_id).write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )

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
        self._save_record(record)
        return record

    def list_documents(self) -> list[DocumentRecord]:
        return sorted(self._records.values(), key=lambda doc: doc.created_at, reverse=True)

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        return self._records.get(document_id)

    def update_status(self, document_id: str, status: str) -> Optional[DocumentRecord]:
        record = self.get_document(document_id)
        if not record:
            return None
        updated = record.model_copy(
            update={"status": status, "updated_at": datetime.now(timezone.utc)}
        )
        self._save_record(updated)
        return updated

    def set_result(self, document_id: str, result: dict) -> None:
        self._results[document_id] = result
        self._result_path(document_id).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if document_id in self._records:
            record = self._records[document_id]
            updated = record.model_copy(
                update={
                    "status": result.get("status", record.status),
                    "updated_at": datetime.now(timezone.utc),
                    "final_type": result.get("final_type"),
                    "final_decision": result.get("final_decision"),
                    "risk_level": result.get("risk_level"),
                }
            )
            self._save_record(updated)

    def get_result(self, document_id: str) -> Optional[dict]:
        return self._results.get(document_id)


local_document_store = LocalDocumentStore()

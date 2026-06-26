from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import boto3
from fastapi import UploadFile

from app.core.config import settings
from app.core.schemas import DocumentRecord


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_dt(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class AWSDocumentStore:
    """S3 + DynamoDB document store for AWS runtime.

    Input files are stored in S3. Metadata and result pointers are stored in
    DynamoDB. Result JSON is stored in the results bucket.
    """

    def __init__(self) -> None:
        self.s3 = boto3.client("s3", region_name=settings.aws_region)
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.documents_table = self.dynamodb.Table(settings.dynamodb_documents_table)

    async def save_upload(self, *, document_id: str, file: UploadFile) -> DocumentRecord:
        filename = file.filename or "unknown"
        content = await file.read()
        now = datetime.now(timezone.utc)
        s3_key = f"input/{document_id}/{filename}"

        self.s3.put_object(
            Bucket=settings.s3_input_bucket,
            Key=s3_key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
            Metadata={"document_id": document_id, "filename": filename},
        )

        record = DocumentRecord(
            document_id=document_id,
            filename=filename,
            status="uploaded",
            content_type=file.content_type,
            size_bytes=len(content),
            s3_bucket=settings.s3_input_bucket,
            s3_key=s3_key,
            created_at=now,
            updated_at=now,
        )
        self._put_record(record)
        return record

    def _put_record(self, record: DocumentRecord) -> None:
        item = record.model_dump(mode="json", exclude_none=True)
        # DynamoDB stores all timestamps as ISO strings via mode=json.
        self.documents_table.put_item(Item=item)

    def list_documents(self) -> list[DocumentRecord]:
        response = self.documents_table.scan(Limit=100)
        records = [self._record_from_item(item) for item in response.get("Items", [])]
        return sorted(records, key=lambda doc: doc.created_at, reverse=True)

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        response = self.documents_table.get_item(Key={"document_id": document_id})
        item = response.get("Item")
        if not item:
            return None
        return self._record_from_item(item)

    def update_status(self, document_id: str, status: str) -> Optional[DocumentRecord]:
        record = self.get_document(document_id)
        if not record:
            return None
        updated = record.model_copy(
            update={"status": status, "updated_at": datetime.now(timezone.utc)}
        )
        self._put_record(updated)
        return updated

    def set_result(self, document_id: str, result: dict) -> None:
        record = self.get_document(document_id)
        if not record:
            raise ValueError("Document not found")

        result_key = f"results/{document_id}/result.json"
        self.s3.put_object(
            Bucket=settings.s3_results_bucket,
            Key=result_key,
            Body=json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json",
            Metadata={"document_id": document_id},
        )

        updated = record.model_copy(
            update={
                "status": result.get("status", record.status),
                "updated_at": datetime.now(timezone.utc),
                "final_type": result.get("final_type"),
                "final_decision": result.get("final_decision"),
                "risk_level": result.get("risk_level"),
                "result_s3_bucket": settings.s3_results_bucket,
                "result_s3_key": result_key,
            }
        )
        self._put_record(updated)

    def get_result(self, document_id: str) -> Optional[dict]:
        record = self.get_document(document_id)
        if not record or not record.result_s3_bucket or not record.result_s3_key:
            return None
        response = self.s3.get_object(Bucket=record.result_s3_bucket, Key=record.result_s3_key)
        return json.loads(response["Body"].read().decode("utf-8"))

    def download_input_to(self, record: DocumentRecord, target_path: str) -> str:
        if not record.s3_bucket or not record.s3_key:
            raise ValueError("Document has no S3 input location")
        self.s3.download_file(record.s3_bucket, record.s3_key, target_path)
        return target_path

    def _record_from_item(self, item: dict) -> DocumentRecord:
        data = dict(item)
        data["created_at"] = _parse_dt(data.get("created_at"))
        data["updated_at"] = _parse_dt(data.get("updated_at"))
        return DocumentRecord.model_validate(data)


aws_document_store = AWSDocumentStore()

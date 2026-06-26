from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3

from app.core.config import settings
from app.services.document_analysis_service import analyze_document
from app.storage.document_store import get_document_store


class AWSSQSWorker:
    """Worker that consumes SQS messages and processes documents from S3."""

    def __init__(self) -> None:
        self.sqs = boto3.client("sqs", region_name=settings.aws_region)
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.jobs_table = self.dynamodb.Table(settings.dynamodb_processing_jobs_table)
        self.document_store = get_document_store()

    def run_forever(self, sleep_seconds: int = 5) -> None:
        while True:
            processed = self.run_once()
            if not processed:
                time.sleep(sleep_seconds)

    def run_once(self) -> bool:
        response = self.sqs.receive_message(
            QueueUrl=settings.sqs_processing_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,
            VisibilityTimeout=900,
        )
        messages = response.get("Messages", [])
        if not messages:
            return False

        message = messages[0]
        receipt_handle = message["ReceiptHandle"]
        payload = json.loads(message["Body"])
        job_id = payload["job_id"]
        document_id = payload["document_id"]

        try:
            self._update_job(job_id, "running")
            self.document_store.update_status(document_id, "processing")

            record = self.document_store.get_document(document_id)
            if not record:
                raise ValueError(f"Document not found: {document_id}")

            local_path = self._download_document(record)
            processing_record = record.model_copy(update={"local_path": local_path})
            analyze_document(processing_record)

            self._update_job(job_id, "done")
            self.sqs.delete_message(
                QueueUrl=settings.sqs_processing_queue_url,
                ReceiptHandle=receipt_handle,
            )
            return True
        except Exception as exc:
            self._update_job(job_id, "failed", str(exc))
            self.document_store.update_status(document_id, "error")
            # Keep the worker alive. The message is intentionally not deleted so
            # SQS can retry and then route it to the DLQ after maxReceiveCount.
            print(f"Document processing failed for {document_id}: {exc}")
            return True

    def _download_document(self, record) -> str:
        work_dir = Path("/tmp/eva-document-ai-poc-worker") / record.document_id
        work_dir.mkdir(parents=True, exist_ok=True)
        local_path = str(work_dir / record.filename)
        self.document_store.download_input_to(record, local_path)
        return local_path

    def _update_job(self, job_id: str, status: str, error_message: str | None = None) -> None:
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {
            ":status": status,
            ":updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if error_message:
            update_expression += ", error_message = :error_message"
            expression_attribute_values[":error_message"] = error_message

        self.jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import boto3

from app.core.config import settings
from app.core.schemas import ProcessingJob
from app.storage.document_store import get_document_store


class AWSProcessingQueue:
    """SQS + DynamoDB processing queue service for AWS runtime."""

    def __init__(self) -> None:
        self.sqs = boto3.client("sqs", region_name=settings.aws_region)
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.jobs_table = self.dynamodb.Table(settings.dynamodb_processing_jobs_table)

    def enqueue(self, document_id: str) -> ProcessingJob:
        document_store = get_document_store()
        document = document_store.get_document(document_id)
        if not document:
            raise ValueError("Document not found")
        if not settings.sqs_processing_queue_url:
            raise ValueError("SQS processing queue URL is not configured")

        now = datetime.now(timezone.utc)
        job = ProcessingJob(
            job_id=str(uuid4()),
            document_id=document_id,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        self._put_job(job)
        document_store.update_status(document_id, "queued")

        self.sqs.send_message(
            QueueUrl=settings.sqs_processing_queue_url,
            MessageBody=json.dumps(
                {
                    "job_id": job.job_id,
                    "document_id": document_id,
                    "s3_bucket": document.s3_bucket,
                    "s3_key": document.s3_key,
                }
            ),
        )
        return job

    def list_jobs(self) -> list[ProcessingJob]:
        response = self.jobs_table.scan(Limit=100)
        jobs = [self._job_from_item(item) for item in response.get("Items", [])]
        return sorted(jobs, key=lambda job: job.created_at, reverse=True)

    def run_next(self) -> ProcessingJob | None:
        raise NotImplementedError("AWS worker consumes SQS asynchronously. Use ECS worker service instead.")

    def _put_job(self, job: ProcessingJob) -> None:
        self.jobs_table.put_item(Item=job.model_dump(mode="json", exclude_none=True))

    def _job_from_item(self, item: dict) -> ProcessingJob:
        data = dict(item)
        data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        return ProcessingJob.model_validate(data)


aws_processing_queue = AWSProcessingQueue()

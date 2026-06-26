from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.schemas import ProcessingJob
from app.services.document_analysis_service import analyze_document
from app.storage.local_storage import local_document_store


class LocalProcessingQueue:
    """Filesystem-backed processing queue for local POC mode.

    This mimics the future SQS + worker behavior without requiring AWS.
    """

    def __init__(self, base_dir: str = "/tmp/eva-document-ai-poc") -> None:
        self.base_dir = Path(base_dir)
        self.jobs_dir = self.base_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, ProcessingJob] = {}
        self._load_jobs()

    def _job_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def _load_jobs(self) -> None:
        for path in self.jobs_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                job = ProcessingJob.model_validate(data)
                self._jobs[job.job_id] = job
            except Exception:
                continue

    def _save_job(self, job: ProcessingJob) -> None:
        self._jobs[job.job_id] = job
        self._job_path(job.job_id).write_text(job.model_dump_json(indent=2), encoding="utf-8")

    def enqueue(self, document_id: str) -> ProcessingJob:
        document = local_document_store.get_document(document_id)
        if not document:
            raise ValueError("Document not found")

        now = datetime.now(timezone.utc)
        job = ProcessingJob(
            job_id=str(uuid4()),
            document_id=document_id,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        self._save_job(job)
        local_document_store.update_status(document_id, "queued")
        return job

    def list_jobs(self) -> list[ProcessingJob]:
        return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    def get_next_queued_job(self) -> ProcessingJob | None:
        queued = [job for job in self._jobs.values() if job.status == "queued"]
        if not queued:
            return None
        return sorted(queued, key=lambda job: job.created_at)[0]

    def run_next(self) -> ProcessingJob | None:
        job = self.get_next_queued_job()
        if not job:
            return None
        return self.run_job(job.job_id)

    def run_job(self, job_id: str) -> ProcessingJob:
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError("Job not found")

        now = datetime.now(timezone.utc)
        running = job.model_copy(update={"status": "running", "updated_at": now})
        self._save_job(running)
        local_document_store.update_status(job.document_id, "processing")

        try:
            document = local_document_store.get_document(job.document_id)
            if not document:
                raise ValueError("Document not found")
            analyze_document(document)
            done = running.model_copy(
                update={"status": "done", "updated_at": datetime.now(timezone.utc), "error_message": None}
            )
            self._save_job(done)
            return done
        except Exception as exc:
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "updated_at": datetime.now(timezone.utc),
                    "error_message": str(exc),
                }
            )
            self._save_job(failed)
            local_document_store.update_status(job.document_id, "error")
            return failed


local_processing_queue = LocalProcessingQueue()

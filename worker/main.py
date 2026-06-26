from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.schemas import DocumentRecord
from app.services.document_analysis_service import analyze_document
from app.services.processing_queue_service import local_processing_queue


def analyze_local_file(path: str) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    record = DocumentRecord(
        document_id=str(uuid4()),
        filename=file_path.name,
        status="uploaded",
        content_type=None,
        size_bytes=file_path.stat().st_size,
        local_path=str(file_path),
    )
    return analyze_document(record)


def main() -> None:
    parser = argparse.ArgumentParser(description="EVA POC worker")
    parser.add_argument("--file", help="Local file to analyze without AWS")
    parser.add_argument("--run-next", action="store_true", help="Run the next queued local processing job")
    parser.add_argument("--once", action="store_true", help="In AWS mode, process one SQS message and exit")
    args = parser.parse_args()

    if args.file:
        result = analyze_local_file(args.file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if settings.is_aws:
        from worker.aws_worker import AWSSQSWorker

        worker = AWSSQSWorker()
        if args.once:
            processed = worker.run_once()
            print("Processed one message" if processed else "No SQS message available")
            return
        print("EVA POC AWS worker started. Polling SQS.")
        worker.run_forever()
        return

    if args.run_next:
        job = local_processing_queue.run_next()
        if not job:
            print("No queued job")
            return
        print(job.model_dump_json(indent=2))
        return

    print("EVA POC worker ready. Use --file <path> or --run-next for local processing.")


if __name__ == "__main__":
    main()

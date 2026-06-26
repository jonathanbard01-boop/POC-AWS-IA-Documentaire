from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from app.core.schemas import DocumentRecord
from app.services.document_analysis_service import analyze_document


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
    parser = argparse.ArgumentParser(description="EVA POC local worker")
    parser.add_argument("--file", help="Local file to analyze without AWS")
    args = parser.parse_args()

    if not args.file:
        print("EVA POC worker ready. Use --file <path> for local analysis.")
        return

    result = analyze_local_file(args.file)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

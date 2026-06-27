from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.core.schemas import CorpusDocumentSummary, CorpusResponse, CorpusUpsertResponse, EngineResult

TOKEN_PATTERN = re.compile(r"[\wÀ-ÿ']+", re.UNICODE)
DOCUMENT_TYPE_PATTERN = re.compile(r"^[a-z0-9_]+$")
LOCAL_CORPUS_DIR = Path("data/bm25_examples")
ACTIVE_MANIFEST_KEY = "corpus/active_manifest.json"


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _default_version() -> str:
    return _now().strftime("v%Y%m%d%H%M%S")


def _word_count(text: str) -> int:
    return len(tokenize(text))


def _validate_document_type(document_type: str) -> str:
    value = document_type.strip().lower()
    if not DOCUMENT_TYPE_PATTERN.match(value):
        raise ValueError("document_type must be snake_case with letters, digits and underscores only")
    return value


def _parse_dt(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _local_documents() -> list[tuple[str, str, dict[str, Any]]]:
    documents: list[tuple[str, str, dict[str, Any]]] = []
    for path in sorted(LOCAL_CORPUS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            documents.append((path.stem, text, {"filename": path.name, "active": True}))
    return documents


def _s3_client():
    return boto3.client("s3", region_name=settings.aws_region)


def _dynamodb():
    return boto3.resource("dynamodb", region_name=settings.aws_region)


def _read_manifest() -> dict[str, Any]:
    try:
        response = _s3_client().get_object(Bucket=settings.s3_results_bucket, Key=ACTIVE_MANIFEST_KEY)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"NoSuchKey", "404", "NoSuchBucket"}:
            return {"documents": []}
        raise
    return json.loads(response["Body"].read().decode("utf-8"))


def _write_manifest(manifest: dict[str, Any]) -> None:
    _s3_client().put_object(
        Bucket=settings.s3_results_bucket,
        Key=ACTIVE_MANIFEST_KEY,
        Body=json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def _aws_documents() -> list[tuple[str, str, dict[str, Any]]]:
    manifest = _read_manifest()
    documents: list[tuple[str, str, dict[str, Any]]] = []

    for item in manifest.get("documents", []):
        if item.get("active", True) is False:
            continue
        document_type = item.get("document_type")
        bucket = item.get("s3_bucket") or settings.s3_results_bucket
        key = item.get("s3_key")
        if not document_type or not key:
            continue
        response = _s3_client().get_object(Bucket=bucket, Key=key)
        text = response["Body"].read().decode("utf-8").strip()
        if text:
            documents.append((document_type, text, item))

    return documents


def load_runtime_documents() -> tuple[str, list[tuple[str, str, dict[str, Any]]]]:
    if settings.is_aws:
        try:
            documents = _aws_documents()
            if documents:
                return "aws-s3", documents
        except Exception:
            pass

    return "local-files", _local_documents()


def list_runtime_corpus() -> CorpusResponse:
    source, documents = load_runtime_documents()
    summaries: list[CorpusDocumentSummary] = []

    for document_type, text, metadata in documents:
        summaries.append(
            CorpusDocumentSummary(
                document_type=document_type,
                filename=metadata.get("filename") or f"{document_type}.txt",
                char_count=len(text),
                word_count=_word_count(text),
                token_count=len(tokenize(text)),
                preview=text[:240],
                active=metadata.get("active", True),
                version=metadata.get("version"),
                s3_bucket=metadata.get("s3_bucket"),
                s3_key=metadata.get("s3_key"),
                updated_at=_parse_dt(metadata.get("updated_at")),
            )
        )

    return CorpusResponse(source=source, document_count=len(summaries), documents=summaries)


def get_runtime_document_types() -> list[str]:
    _source, documents = load_runtime_documents()
    return sorted({document_type for document_type, _text, _metadata in documents})


def classify_runtime_text(text: str) -> EngineResult:
    _source, documents = load_runtime_documents()
    if not text.strip() or not documents:
        return EngineResult(top_type="document_inconnu", score=0.0)

    query_tokens = tokenize(text)
    corpus_tokens = [tokenize(document_text) for _document_type, document_text, _metadata in documents]
    if not query_tokens or not corpus_tokens:
        return EngineResult(top_type="document_inconnu", score=0.0)

    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(zip(documents, scores, strict=True), key=lambda item: float(item[1]), reverse=True)

    top_document, top_score = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    second_type = second[0][0] if second else None
    second_score = float(second[1]) if second else None
    margin = float(top_score) - second_score if second_score is not None else None

    return EngineResult(
        top_type=top_document[0],
        score=float(top_score),
        second_type=second_type,
        second_score=second_score,
        margin=margin,
    )


def upsert_corpus_text(
    document_type: str,
    text: str,
    *,
    version: str | None = None,
    active: bool = True,
) -> CorpusUpsertResponse:
    document_type = _validate_document_type(document_type)
    text = text.strip()
    if not text:
        raise ValueError("Corpus text cannot be empty")

    version_value = version or _default_version()
    updated_at = _now()
    filename = f"{document_type}.txt"

    if not settings.is_aws:
        LOCAL_CORPUS_DIR.mkdir(parents=True, exist_ok=True)
        path = LOCAL_CORPUS_DIR / filename
        path.write_text(text, encoding="utf-8")
        return CorpusUpsertResponse(
            document_type=document_type,
            filename=filename,
            active=active,
            version=version_value,
            char_count=len(text),
            word_count=_word_count(text),
            updated_at=updated_at,
        )

    s3_key = f"corpus/{version_value}/{filename}"
    _s3_client().put_object(
        Bucket=settings.s3_results_bucket,
        Key=s3_key,
        Body=text.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
        Metadata={"document_type": document_type, "version": version_value},
    )

    item = {
        "document_type": document_type,
        "filename": filename,
        "active": active,
        "version": version_value,
        "char_count": len(text),
        "word_count": _word_count(text),
        "s3_bucket": settings.s3_results_bucket,
        "s3_key": s3_key,
        "updated_at": updated_at.isoformat(),
    }

    manifest = _read_manifest()
    documents = [entry for entry in manifest.get("documents", []) if entry.get("document_type") != document_type]
    documents.append(item)
    manifest["documents"] = sorted(documents, key=lambda entry: entry["document_type"])
    manifest["updated_at"] = updated_at.isoformat()
    _write_manifest(manifest)

    try:
        _dynamodb().Table(settings.dynamodb_document_types_table).put_item(Item=item)
    except Exception:
        pass

    return CorpusUpsertResponse(
        document_type=document_type,
        filename=filename,
        active=active,
        version=version_value,
        char_count=len(text),
        word_count=_word_count(text),
        s3_bucket=settings.s3_results_bucket,
        s3_key=s3_key,
        updated_at=updated_at,
    )

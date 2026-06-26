from uuid import uuid4

from fastapi import UploadFile

from app.core.schemas import DocumentRecord
from app.storage.document_store import get_document_store


def _store():
    return get_document_store()


async def create_document(file: UploadFile) -> dict:
    """Create a document record.

    Local mode stores files under /tmp. AWS mode stores input bytes in S3 and
    metadata in DynamoDB.
    """

    document_id = str(uuid4())
    record = await _store().save_upload(document_id=document_id, file=file)
    return record.model_dump(mode="json")


def list_documents() -> list[DocumentRecord]:
    return _store().list_documents()


def get_document(document_id: str) -> DocumentRecord | None:
    return _store().get_document(document_id)


def get_document_result(document_id: str) -> dict | None:
    return _store().get_result(document_id)

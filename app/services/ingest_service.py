from uuid import uuid4

from fastapi import UploadFile

from app.core.schemas import DocumentRecord
from app.storage.local_storage import local_document_store


async def create_document(file: UploadFile) -> dict:
    """Create a local document record.

    Palier 1 local mode: store the file under /tmp and keep metadata in memory.
    AWS mode will later persist bytes in S3, metadata in DynamoDB, and enqueue
    the processing request in SQS.
    """

    document_id = str(uuid4())
    record = await local_document_store.save_upload(document_id=document_id, file=file)
    return record.model_dump(mode="json")


def list_documents() -> list[DocumentRecord]:
    return local_document_store.list_documents()


def get_document(document_id: str) -> DocumentRecord | None:
    return local_document_store.get_document(document_id)


def get_document_result(document_id: str) -> dict | None:
    return local_document_store.get_result(document_id)

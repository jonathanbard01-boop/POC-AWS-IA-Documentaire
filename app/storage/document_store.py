from __future__ import annotations

from app.core.config import settings
from app.storage.local_storage import local_document_store


def get_document_store():
    if settings.is_aws:
        from app.storage.aws_storage import aws_document_store

        return aws_document_store
    return local_document_store

from __future__ import annotations

from app.core.config import settings
from app.services.processing_queue_service import local_processing_queue


def get_processing_queue():
    if settings.is_aws:
        from app.services.aws_processing_queue_service import aws_processing_queue

        return aws_processing_queue
    return local_processing_queue

from uuid import uuid4
from fastapi import UploadFile

async def create_document(file: UploadFile) -> dict:
    # V1 local stub. AWS implementation will write to S3, DynamoDB and SQS.
    document_id = str(uuid4())
    return {
        "document_id": document_id,
        "filename": file.filename or "unknown",
        "status": "uploaded",
    }

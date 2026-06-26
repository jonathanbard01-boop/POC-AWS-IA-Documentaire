from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    aws_region: str = "eu-west-3"

    s3_input_bucket: str = "eva-poc-input"
    s3_processed_bucket: str = "eva-poc-processed"
    s3_results_bucket: str = "eva-poc-results"
    s3_errors_bucket: str = "eva-poc-errors"
    s3_training_bucket: str = "eva-poc-training"

    sqs_processing_queue_url: str = ""

    dynamodb_documents_table: str = "eva-poc-documents"
    dynamodb_processing_jobs_table: str = "eva-poc-processing-jobs"
    dynamodb_validation_tasks_table: str = "eva-poc-validation-tasks"
    dynamodb_document_types_table: str = "eva-poc-document-types"
    dynamodb_human_corrections_table: str = "eva-poc-human-corrections"

    decision_thresholds_path: str = "config/decision_thresholds.yml"

    @property
    def is_aws(self) -> bool:
        return self.app_env.lower() == "aws"

    class Config:
        env_file = ".env"


settings = Settings()

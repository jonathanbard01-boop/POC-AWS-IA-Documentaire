from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "local"
    aws_region: str = "eu-west-3"
    s3_input_bucket: str = "eva-poc-input"
    s3_processed_bucket: str = "eva-poc-processed"
    s3_results_bucket: str = "eva-poc-results"
    sqs_processing_queue_url: str = ""
    dynamodb_documents_table: str = "eva-poc-documents"
    dynamodb_validation_tasks_table: str = "eva-poc-validation-tasks"
    decision_thresholds_path: str = "config/decision_thresholds.yml"

    class Config:
        env_file = ".env"

settings = Settings()

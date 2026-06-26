# Architecture AWS Palier 1

```text
Front-office -> ALB -> FastAPI -> S3 input -> SQS -> Worker -> S3 results + DynamoDB -> Back-office
```

Le Palier 1 reste CPU-first. Les briques GPU, SageMaker, Qwen, Mistral et VLM sont prévues pour les paliers suivants.

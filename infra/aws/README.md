# Infrastructure AWS

Ressources Palier 1 :

- S3 : input, processed, results, errors, training
- DynamoDB : documents, processing jobs, validation tasks, document types, corrections
- SQS : processing queue
- ECR : api, worker
- ECS Fargate : api service, worker service
- Cognito : front_user, videotypeur, superviseur, admin
- CloudWatch : logs et métriques

Voir `architecture.md` pour le détail.

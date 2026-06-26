# EVA Document AI POC

POC AWS de reconnaissance documentaire open source : dépôt de documents, OCR Tesseract, prétraitement OpenCV, classification BM25, lecture code-barres / QR code, moteur de décision, front-office et back-office.

## Objectif

Démontrer une chaîne documentaire de bout en bout :

1. dépôt PDF / image ;
2. stockage dans S3 ;
3. traitement asynchrone par worker ;
4. OCR et scoring qualité ;
5. typage documentaire ;
6. décision `automatic`, `human_review` ou `rejected` ;
7. consultation dans un front-office ;
8. validation dans un back-office.

## Architecture Palier 1

```text
Front-office React
  -> API FastAPI sur ECS Fargate
  -> S3 input
  -> SQS processing queue
  -> Worker IA ECS Fargate
  -> S3 results + DynamoDB
  -> Back-office React
```

## Briques IA V1

- Tesseract OCR
- OpenCV
- BM25 textuel
- Lecture QR code / code-barres
- Moteur de décision explicable

## Hors périmètre V1

- Qwen-VL / Pixtral
- LLM open source d'arbitrage final
- Embeddings sémantiques lourds
- SageMaker / GPU
- Fine-tuning

## Déployer le socle AWS

Depuis AWS CloudShell ou un poste avec AWS CLI configuré :

```bash
git clone https://github.com/jonathanbard01-boop/POC-AWS-IA-Documentaire.git
cd POC-AWS-IA-Documentaire
chmod +x scripts/aws_deploy_foundation.sh
AWS_REGION=eu-west-3 ./scripts/aws_deploy_foundation.sh
```

Ce premier déploiement crée :

- buckets S3 : input, processed, results, errors, training ;
- tables DynamoDB : documents, processing jobs, validation tasks, document types, corrections ;
- file SQS et DLQ ;
- repositories ECR API et worker ;
- rôles IAM API / worker ;
- log groups CloudWatch.

Guide détaillé : `docs/aws-deployment-step-by-step.md`.

## Lancement local

```bash
cp .env.example .env
docker compose up --build
```

API : http://localhost:8000/health

## Tester le flux local par API

Uploader un fichier texte de test :

```bash
curl -F "file=@data/bm25_examples/facture_creche.txt" \
  http://localhost:8000/documents/upload
```

Analyser le document avec l'identifiant retourné :

```bash
curl -X POST http://localhost:8000/documents/<document_id>/analyze
```

Consulter le résultat :

```bash
curl http://localhost:8000/documents/<document_id>/result
```

## Tester le worker local sans API

```bash
python -m worker.main --file data/bm25_examples/facture_creche.txt
```

Cette commande produit directement un JSON d'analyse local : OCR texte, BM25, décision et motifs.

Endpoints disponibles :

```text
GET  /health
POST /documents/upload
GET  /documents
GET  /documents/{document_id}
POST /documents/{document_id}/analyze
POST /documents/{document_id}/enqueue
GET  /processing/queue
POST /processing/run-next
GET  /documents/{document_id}/result
GET  /document-types
```

## Structure

```text
app/          API FastAPI
worker/       Worker de traitement documentaire
data/         Exemples BM25, templates, samples
config/       Seuils de décision
frontend/     Front-office utilisateur
backoffice/   Back-office de validation
infra/aws/    Notes de déploiement AWS
docs/         Documentation projet
scripts/      Scripts utilitaires
tests/        Tests unitaires
```

## Prochaine étape

Créer le deuxième template AWS : ECS Fargate, Application Load Balancer, task definitions API/worker, variables d'environnement et service discovery minimal.

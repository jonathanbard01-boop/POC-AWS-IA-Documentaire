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

## Lancement local

```bash
cp .env.example .env
docker compose up --build
```

API : http://localhost:8000/health

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

Implémenter Lot 1 + Lot 2 : infrastructure AWS minimale et API d'ingestion.

# Déploiement V2 corpus dynamique

## Objectif

Cette version permet de modifier le corpus de typage sans reconstruire l'image Docker.

Le corpus actif est stocké dans le bucket S3 results, sous le préfixe `corpus/`, avec un manifeste actif :

```text
corpus/active_manifest.json
corpus/<version>/<document_type>.txt
```

Ce choix utilise les permissions AWS déjà validées pour l'API et le worker, sans patch IAM complémentaire avant la démonstration.

## Endpoints

```text
GET  /corpus
PUT  /corpus/{document_type}
POST /corpus/{document_type}/upload
GET  /classification/corpus
POST /classification/test
```

## Injecter un fichier texte

```bash
curl -X POST "$API_URL/corpus/facture_creche/upload" \
  -F "file=@data/bm25_examples/facture_creche.txt"
```

## Injecter un texte JSON

```bash
curl -X PUT "$API_URL/corpus/facture_creche" \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "text": "Texte du corpus facture crèche...",
  "active": true
}
JSON
```

## Tester le corpus

```bash
curl "$API_URL/corpus"

curl -X POST "$API_URL/classification/test" \
  -H "Content-Type: application/json" \
  -d '{"text":"Facture crèche enfant montant janvier 2026"}'
```

## Chaîne complète de démonstration

1. Injecter les fichiers `.txt` du corpus.
2. Tester `/classification/test`.
3. Uploader un document.
4. Appeler `/documents/{document_id}/enqueue`.
5. Attendre le worker ECS.
6. Consulter `/documents/{document_id}/result`.
7. Valider, corriger ou rejeter le résultat.

## Build depuis la branche propre

```bash
AWS_REGION=eu-west-3 \
GIT_BRANCH=feature/poc-v3-backoffice-validation \
IMAGE_TAG=v3 \
./scripts/aws_deploy_codebuild_image_builder.sh
```

## Redéploiement ECS

```bash
AWS_REGION=eu-west-3 \
IMAGE_TAG=v3 \
./scripts/aws_deploy_ecs.sh
```

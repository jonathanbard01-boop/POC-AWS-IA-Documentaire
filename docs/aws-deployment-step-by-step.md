# Déploiement AWS - Palier 1

Ce guide explique comment créer le socle AWS du POC IA documentaire.

## Prérequis

- Un compte AWS accessible.
- AWS CLI configuré, ou AWS CloudShell.
- Région recommandée : `eu-west-3`.
- Droits nécessaires : CloudFormation, S3, DynamoDB, SQS, ECR, IAM et CloudWatch Logs.

## Ressources créées

Le template `infra/aws/cloudformation/palier1-foundation.yml` crée :

- 5 buckets S3 : input, processed, results, errors, training ;
- 5 tables DynamoDB : documents, processing jobs, validation tasks, document types, corrections ;
- 1 file SQS de traitement ;
- 1 DLQ SQS ;
- 2 repositories ECR : API et worker ;
- 2 log groups CloudWatch ;
- 3 rôles IAM : execution ECS, API task role, worker task role.

## Déploiement depuis AWS CloudShell

Cloner le dépôt :

```bash
git clone https://github.com/jonathanbard01-boop/POC-AWS-IA-Documentaire.git
cd POC-AWS-IA-Documentaire
```

Lancer le déploiement :

```bash
chmod +x scripts/aws_deploy_foundation.sh
AWS_REGION=eu-west-3 ./scripts/aws_deploy_foundation.sh
```

## Déploiement direct AWS CLI

```bash
aws cloudformation deploy \
  --region eu-west-3 \
  --stack-name eva-document-ai-poc-foundation \
  --template-file infra/aws/cloudformation/palier1-foundation.yml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName=eva-document-ai \
    EnvName=poc
```

## Vérifier les sorties

```bash
aws cloudformation describe-stacks \
  --region eu-west-3 \
  --stack-name eva-document-ai-poc-foundation \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Résultat attendu

La stack doit retourner les noms des buckets, tables DynamoDB, URL de file SQS, URI ECR et rôles IAM.

Ces outputs seront utilisés ensuite pour :

1. construire les images Docker API et worker ;
2. les pousser dans ECR ;
3. créer le cluster ECS Fargate ;
4. déployer l’API et le worker ;
5. brancher le front-office et le back-office.

## Nettoyage

Pour supprimer le socle :

```bash
aws cloudformation delete-stack \
  --region eu-west-3 \
  --stack-name eva-document-ai-poc-foundation
```

Attention : les buckets S3 doivent être vides avant suppression complète de la stack.

## Limite de ce premier template

Ce template crée le socle de données et de traitement. Il ne déploie pas encore ECS Fargate, l’ALB, Cognito, ni le front-office. Ces éléments sont prévus dans le template suivant.

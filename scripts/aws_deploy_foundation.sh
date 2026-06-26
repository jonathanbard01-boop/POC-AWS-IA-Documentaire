#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-eu-west-3}"
STACK_NAME="${STACK_NAME:-eva-document-ai-poc-foundation}"
PROJECT_NAME="${PROJECT_NAME:-eva-document-ai}"
ENV_NAME="${ENV_NAME:-poc}"
TEMPLATE="infra/aws/cloudformation/palier1-foundation.yml"

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is required. Install or run this script from AWS CloudShell." >&2
  exit 1
fi

echo "Deploying foundation stack: ${STACK_NAME}"
echo "Region: ${REGION}"
echo "ProjectName: ${PROJECT_NAME}"
echo "EnvName: ${ENV_NAME}"

aws cloudformation deploy \
  --region "${REGION}" \
  --stack-name "${STACK_NAME}" \
  --template-file "${TEMPLATE}" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    EnvName="${ENV_NAME}"

echo "Stack outputs:"
aws cloudformation describe-stacks \
  --region "${REGION}" \
  --stack-name "${STACK_NAME}" \
  --query 'Stacks[0].Outputs' \
  --output table

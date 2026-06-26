#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-eu-west-3}"
STACK_NAME="${STACK_NAME:-eva-document-ai-poc-foundation}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is required. Run this from AWS CloudShell or a workstation with AWS CLI." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to build images. Run this from an environment where Docker is available." >&2
  exit 1
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
API_REPO_URI="$(aws cloudformation describe-stacks --region "${REGION}" --stack-name "${STACK_NAME}" --query "Stacks[0].Outputs[?OutputKey=='ApiRepositoryUri'].OutputValue" --output text)"
WORKER_REPO_URI="$(aws cloudformation describe-stacks --region "${REGION}" --stack-name "${STACK_NAME}" --query "Stacks[0].Outputs[?OutputKey=='WorkerRepositoryUri'].OutputValue" --output text)"

if [[ -z "${API_REPO_URI}" || -z "${WORKER_REPO_URI}" ]]; then
  echo "Unable to retrieve ECR repository URIs from stack outputs." >&2
  exit 1
fi

echo "Logging in to ECR ${ACCOUNT_ID} in ${REGION}"
aws ecr get-login-password --region "${REGION}" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "Building API image: ${API_REPO_URI}:${IMAGE_TAG}"
docker build -f Dockerfile.api -t "${API_REPO_URI}:${IMAGE_TAG}" .

echo "Pushing API image"
docker push "${API_REPO_URI}:${IMAGE_TAG}"

echo "Building worker image: ${WORKER_REPO_URI}:${IMAGE_TAG}"
docker build -f Dockerfile.worker -t "${WORKER_REPO_URI}:${IMAGE_TAG}" .

echo "Pushing worker image"
docker push "${WORKER_REPO_URI}:${IMAGE_TAG}"

echo "Images pushed successfully"
echo "API_IMAGE=${API_REPO_URI}:${IMAGE_TAG}"
echo "WORKER_IMAGE=${WORKER_REPO_URI}:${IMAGE_TAG}"

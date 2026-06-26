#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-eu-west-3}"
FOUNDATION_STACK_NAME="${FOUNDATION_STACK_NAME:-eva-document-ai-poc-foundation}"
CODEBUILD_STACK_NAME="${CODEBUILD_STACK_NAME:-eva-document-ai-poc-codebuild}"
PROJECT_NAME="${PROJECT_NAME:-eva-document-ai}"
ENV_NAME="${ENV_NAME:-poc}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
GIT_REPOSITORY_URL="${GIT_REPOSITORY_URL:-https://github.com/jonathanbard01-boop/POC-AWS-IA-Documentaire.git}"
GIT_BRANCH="${GIT_BRANCH:-main}"
TEMPLATE="infra/aws/cloudformation/palier1-codebuild.yml"

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is required. Run this from AWS CloudShell." >&2
  exit 1
fi

get_output() {
  local key="$1"
  aws cloudformation describe-stacks \
    --region "${REGION}" \
    --stack-name "${FOUNDATION_STACK_NAME}" \
    --query "Stacks[0].Outputs[?OutputKey=='${key}'].OutputValue" \
    --output text
}

API_REPO_URI="$(get_output ApiRepositoryUri)"
WORKER_REPO_URI="$(get_output WorkerRepositoryUri)"

if [[ -z "${API_REPO_URI}" || -z "${WORKER_REPO_URI}" ]]; then
  echo "Unable to retrieve ECR repository URIs from foundation stack outputs." >&2
  exit 1
fi

echo "Deploying CodeBuild image builder stack: ${CODEBUILD_STACK_NAME}"
aws cloudformation deploy \
  --region "${REGION}" \
  --stack-name "${CODEBUILD_STACK_NAME}" \
  --template-file "${TEMPLATE}" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    EnvName="${ENV_NAME}" \
    GitRepositoryUrl="${GIT_REPOSITORY_URL}" \
    GitBranch="${GIT_BRANCH}" \
    ImageTag="${IMAGE_TAG}" \
    ApiRepositoryUri="${API_REPO_URI}" \
    WorkerRepositoryUri="${WORKER_REPO_URI}"

PROJECT_NAME_OUTPUT="$(aws cloudformation describe-stacks \
  --region "${REGION}" \
  --stack-name "${CODEBUILD_STACK_NAME}" \
  --query "Stacks[0].Outputs[?OutputKey=='CodeBuildProjectName'].OutputValue" \
  --output text)"

echo "Starting CodeBuild project: ${PROJECT_NAME_OUTPUT}"
BUILD_ID="$(aws codebuild start-build \
  --region "${REGION}" \
  --project-name "${PROJECT_NAME_OUTPUT}" \
  --query 'build.id' \
  --output text)"

echo "Build started: ${BUILD_ID}"
echo "Follow status with:"
echo "aws codebuild batch-get-builds --region ${REGION} --ids ${BUILD_ID} --query 'builds[0].buildStatus' --output text"
echo "Follow logs in CloudWatch log group: /codebuild/${PROJECT_NAME}-${ENV_NAME}-image-builder"

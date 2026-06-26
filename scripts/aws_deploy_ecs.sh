#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-eu-west-3}"
FOUNDATION_STACK_NAME="${FOUNDATION_STACK_NAME:-eva-document-ai-poc-foundation}"
ECS_STACK_NAME="${ECS_STACK_NAME:-eva-document-ai-poc-ecs}"
PROJECT_NAME="${PROJECT_NAME:-eva-document-ai}"
ENV_NAME="${ENV_NAME:-poc}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ALLOWED_INGRESS_CIDR="${ALLOWED_INGRESS_CIDR:-0.0.0.0/0}"
API_DESIRED_COUNT="${API_DESIRED_COUNT:-1}"
WORKER_DESIRED_COUNT="${WORKER_DESIRED_COUNT:-1}"
TEMPLATE="infra/aws/cloudformation/palier1-ecs.yml"

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI is required. Run this from AWS CloudShell or a workstation with AWS CLI." >&2
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
INPUT_BUCKET_NAME="$(get_output InputBucketName)"
PROCESSED_BUCKET_NAME="$(get_output ProcessedBucketName)"
RESULTS_BUCKET_NAME="$(get_output ResultsBucketName)"
ERRORS_BUCKET_NAME="$(get_output ErrorsBucketName)"
TRAINING_BUCKET_NAME="$(get_output TrainingBucketName)"
PROCESSING_QUEUE_URL="$(get_output ProcessingQueueUrl)"
ECS_TASK_EXECUTION_ROLE_ARN="$(get_output EcsTaskExecutionRoleArn)"
API_TASK_ROLE_ARN="$(get_output ApiTaskRoleArn)"
WORKER_TASK_ROLE_ARN="$(get_output WorkerTaskRoleArn)"
DOCUMENTS_TABLE_NAME="$(get_output DocumentsTableName)"
PROCESSING_JOBS_TABLE_NAME="$(get_output ProcessingJobsTableName)"
VALIDATION_TASKS_TABLE_NAME="$(get_output ValidationTasksTableName)"
DOCUMENT_TYPES_TABLE_NAME="$(get_output DocumentTypesTableName)"
HUMAN_CORRECTIONS_TABLE_NAME="$(get_output HumanCorrectionsTableName)"

VPC_ID="${VPC_ID:-}"
if [[ -z "${VPC_ID}" ]]; then
  VPC_ID="$(aws ec2 describe-vpcs \
    --region "${REGION}" \
    --filters Name=isDefault,Values=true \
    --query 'Vpcs[0].VpcId' \
    --output text)"
fi

if [[ -z "${VPC_ID}" || "${VPC_ID}" == "None" ]]; then
  echo "No default VPC found in ${REGION}. Set VPC_ID and SUBNET_IDS explicitly." >&2
  exit 1
fi

SUBNET_IDS="${SUBNET_IDS:-}"
if [[ -z "${SUBNET_IDS}" ]]; then
  SUBNET_IDS="$(aws ec2 describe-subnets \
    --region "${REGION}" \
    --filters Name=vpc-id,Values="${VPC_ID}" Name=state,Values=available \
    --query 'Subnets[].SubnetId' \
    --output text | tr '\t' ',')"
fi

if [[ -z "${SUBNET_IDS}" || "${SUBNET_IDS}" == "None" ]]; then
  echo "No subnet found for VPC ${VPC_ID}. Set SUBNET_IDS=subnet-xxx,subnet-yyy explicitly." >&2
  exit 1
fi

API_IMAGE="${API_REPO_URI}:${IMAGE_TAG}"
WORKER_IMAGE="${WORKER_REPO_URI}:${IMAGE_TAG}"

echo "Deploying ECS stack: ${ECS_STACK_NAME}"
echo "Region: ${REGION}"
echo "VPC: ${VPC_ID}"
echo "Subnets: ${SUBNET_IDS}"
echo "API image: ${API_IMAGE}"
echo "Worker image: ${WORKER_IMAGE}"
echo "API desired count: ${API_DESIRED_COUNT}"
echo "Worker desired count: ${WORKER_DESIRED_COUNT}"

aws cloudformation deploy \
  --region "${REGION}" \
  --stack-name "${ECS_STACK_NAME}" \
  --template-file "${TEMPLATE}" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName="${PROJECT_NAME}" \
    EnvName="${ENV_NAME}" \
    VpcId="${VPC_ID}" \
    PublicSubnetIds="${SUBNET_IDS}" \
    AllowedIngressCidr="${ALLOWED_INGRESS_CIDR}" \
    ApiImage="${API_IMAGE}" \
    WorkerImage="${WORKER_IMAGE}" \
    EcsTaskExecutionRoleArn="${ECS_TASK_EXECUTION_ROLE_ARN}" \
    ApiTaskRoleArn="${API_TASK_ROLE_ARN}" \
    WorkerTaskRoleArn="${WORKER_TASK_ROLE_ARN}" \
    InputBucketName="${INPUT_BUCKET_NAME}" \
    ProcessedBucketName="${PROCESSED_BUCKET_NAME}" \
    ResultsBucketName="${RESULTS_BUCKET_NAME}" \
    ErrorsBucketName="${ERRORS_BUCKET_NAME}" \
    TrainingBucketName="${TRAINING_BUCKET_NAME}" \
    ProcessingQueueUrl="${PROCESSING_QUEUE_URL}" \
    DocumentsTableName="${DOCUMENTS_TABLE_NAME}" \
    ProcessingJobsTableName="${PROCESSING_JOBS_TABLE_NAME}" \
    ValidationTasksTableName="${VALIDATION_TASKS_TABLE_NAME}" \
    DocumentTypesTableName="${DOCUMENT_TYPES_TABLE_NAME}" \
    HumanCorrectionsTableName="${HUMAN_CORRECTIONS_TABLE_NAME}" \
    ApiDesiredCount="${API_DESIRED_COUNT}" \
    WorkerDesiredCount="${WORKER_DESIRED_COUNT}"

echo "ECS stack outputs:"
aws cloudformation describe-stacks \
  --region "${REGION}" \
  --stack-name "${ECS_STACK_NAME}" \
  --query 'Stacks[0].Outputs' \
  --output table

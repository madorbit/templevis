#!/bin/bash

###############################################################################
# Deploy TempleVis Lambda Function and Infrastructure
#
# This script:
# 1. Builds Lambda layer with dependencies
# 2. Packages Lambda function code
# 3. Uploads artifacts to S3
# 4. Deploys CloudFormation stack
# 5. Verifies SES email addresses
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Python 3.11+
#   - Docker (for building Lambda layers)
#   - jq (for JSON parsing)
#
# Usage:
#   ./deploy.sh [dev|staging|prod] [from-email] [receipt-email]
#
# Example:
#   ./deploy.sh prod notify@temple.org schedule@temple.org
#
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-dev}"
FROM_EMAIL="${2:-}"
RECEIPT_EMAIL="${3:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Derived values
STACK_NAME="templevis-pdf-processor-${ENVIRONMENT}"
LAYER_BUCKET="templevis-lambda-layers-$(aws sts get-caller-identity --query Account --output text)-${AWS_REGION}"
CODE_BUCKET="templevis-lambda-code-$(aws sts get-caller-identity --query Account --output text)-${AWS_REGION}"

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

validate_inputs() {
    log_info "Validating deployment inputs..."
    
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT"
        exit 1
    fi
    
    if [[ -z "$FROM_EMAIL" ]]; then
        log_error "FROM_EMAIL is required"
        exit 1
    fi
    
    if [[ -z "$RECEIPT_EMAIL" ]]; then
        log_error "RECEIPT_EMAIL is required"
        exit 1
    fi
    
    # Verify AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "AWS credentials not configured"
        exit 1
    fi
    
    log_success "Input validation passed"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    for tool in aws python3 pip jq; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install missing tools and try again"
        exit 1
    fi
    
    log_success "All prerequisites installed"
}

build_lambda_layer() {
    log_info "Building Lambda layer..."
    
    local layer_dir="${SCRIPT_DIR}/build/layer"
    local requirements="${PROJECT_ROOT}/requirements.txt"
    
    # Create directory structure
    mkdir -p "${layer_dir}/python/lib/python3.11/site-packages"
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install \
        --platform manylinux2014_x86_64 \
        --target "${layer_dir}/python/lib/python3.11/site-packages" \
        --python-version 3.11 \
        --only-binary=:all: \
        --upgrade \
        -r "${requirements}"
    
    # Also install the TempleVis package
    log_info "Installing TempleVis package..."
    pip install \
        --platform manylinux2014_x86_64 \
        --target "${layer_dir}/python/lib/python3.11/site-packages" \
        --python-version 3.11 \
        --only-binary=:all: \
        --upgrade \
        -e "${PROJECT_ROOT}"
    
    # Create zip archive
    local layer_zip="${SCRIPT_DIR}/build/templevis-layer.zip"
    log_info "Creating layer archive: $layer_zip"
    cd "${layer_dir}"
    zip -r -q "${layer_zip}" .
    cd - > /dev/null
    
    log_success "Lambda layer built: $layer_zip"
    echo "$layer_zip"
}

build_lambda_code() {
    log_info "Building Lambda function code..."
    
    local code_dir="${SCRIPT_DIR}/build/code"
    local code_zip="${SCRIPT_DIR}/build/lambda_handler.zip"
    
    mkdir -p "$code_dir"
    
    # Copy Lambda handler
    cp "${SCRIPT_DIR}/lambda_handler.py" "${code_dir}/"
    
    # Create zip archive
    log_info "Creating code archive: $code_zip"
    cd "${code_dir}"
    zip -r -q "${code_zip}" .
    cd - > /dev/null
    
    log_success "Lambda code built: $code_zip"
    echo "$code_zip"
}

create_s3_buckets() {
    log_info "Creating S3 buckets for Lambda artifacts..."
    
    for bucket in "$LAYER_BUCKET" "$CODE_BUCKET"; do
        if aws s3 ls "s3://${bucket}" 2>/dev/null; then
            log_info "Bucket already exists: $bucket"
        else
            log_info "Creating bucket: $bucket"
            aws s3 mb "s3://${bucket}" --region "$AWS_REGION"
            
            # Enable versioning
            aws s3api put-bucket-versioning \
                --bucket "$bucket" \
                --versioning-configuration Status=Enabled \
                --region "$AWS_REGION"
            
            log_success "Bucket created: $bucket"
        fi
    done
}

upload_artifacts() {
    local layer_zip="$1"
    local code_zip="$2"
    
    log_info "Uploading artifacts to S3..."
    
    # Upload layer
    log_info "Uploading Lambda layer to s3://$LAYER_BUCKET/templevis-layer.zip"
    aws s3 cp "$layer_zip" "s3://${LAYER_BUCKET}/templevis-layer.zip" \
        --region "$AWS_REGION"
    log_success "Layer uploaded"
    
    # Upload code
    log_info "Uploading Lambda code to s3://$CODE_BUCKET/lambda_handler.zip"
    aws s3 cp "$code_zip" "s3://${CODE_BUCKET}/lambda_handler.zip" \
        --region "$AWS_REGION"
    log_success "Code uploaded"
}

verify_ses_email_addresses() {
    log_info "Verifying SES email addresses..."
    
    for email in "$FROM_EMAIL" "$RECEIPT_EMAIL"; do
        log_info "Verifying: $email"
        
        # Check if already verified
        if aws ses get-account-sending-enabled --region "$AWS_REGION" &>/dev/null; then
            status=$(aws ses get-identity-verification-attributes \
                --identities "$email" \
                --region "$AWS_REGION" \
                --query "VerificationAttributes.\"${email}\".VerificationStatus" \
                --output text 2>/dev/null || echo "NotFound")
            
            if [[ "$status" == "Success" ]]; then
                log_success "Email already verified: $email"
            else
                log_info "Sending verification email to: $email"
                aws ses verify-email-identity \
                    --email-address "$email" \
                    --region "$AWS_REGION"
                
                log_warning "Verification email sent to $email"
                log_info "Please click the verification link in the email to proceed"
            fi
        fi
    done
}

deploy_cloudformation() {
    log_info "Deploying CloudFormation stack: $STACK_NAME"
    
    local template="${SCRIPT_DIR}/cloudformation-template.yaml"
    
    if [[ ! -f "$template" ]]; then
        log_error "CloudFormation template not found: $template"
        exit 1
    fi
    
    aws cloudformation deploy \
        --template-file "$template" \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            FromEmail="$FROM_EMAIL" \
            ReceiptEmail="$RECEIPT_EMAIL" \
            VirusScanEnabled="false" \
        --capabilities CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset
    
    log_success "CloudFormation stack deployed"
}

display_deployment_info() {
    log_info "Retrieving stack outputs..."
    
    local outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs' \
        --output json)
    
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo "Stack Name: $STACK_NAME"
    echo "Environment: $ENVIRONMENT"
    echo "Region: $AWS_REGION"
    echo ""
    echo "Outputs:"
    echo "$outputs" | jq -r '.[] | "  \(.OutputKey): \(.OutputValue)"'
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Verify email addresses in SES (check email for verification links)"
    echo "2. Test by sending a PDF to: $RECEIPT_EMAIL"
    echo "3. Monitor Lambda execution in CloudWatch Logs"
    echo ""
}

cleanup_build_artifacts() {
    if [[ "$KEEP_BUILD_ARTIFACTS" != "true" ]]; then
        log_info "Cleaning up build artifacts..."
        rm -rf "${SCRIPT_DIR}/build"
        log_success "Build artifacts cleaned up"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         TempleVis Lambda Deployment Script                 ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    validate_inputs
    check_prerequisites
    
    create_s3_buckets
    
    local layer_zip=$(build_lambda_layer)
    local code_zip=$(build_lambda_code)
    
    upload_artifacts "$layer_zip" "$code_zip"
    
    verify_ses_email_addresses
    
    deploy_cloudformation
    
    display_deployment_info
    
    cleanup_build_artifacts
    
    echo -e "${GREEN}Deployment successful!${NC}"
    echo ""
}

main "$@"

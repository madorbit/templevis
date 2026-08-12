"""
AWS Terraform Configuration for TempleVis Lambda Processing Pipeline

Alternative to CloudFormation for infrastructure as code.
Deploy with: terraform init && terraform apply

Variables:
  - environment: dev, staging, or prod
  - from_email: Verified SES sender email
  - receipt_email: Email to receive PDFs
  - aws_region: AWS region (default: us-east-1)
"""

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote state
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "templevis/lambda/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TempleVis"
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

# ============================================================================
# Variables
# ============================================================================

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "from_email" {
  description = "Verified SES email address to send from"
  type        = string
  sensitive   = true
}

variable "receipt_email" {
  description = "Email address to receive PDF files"
  type        = string
  sensitive   = true
}

variable "virus_scan_enabled" {
  description = "Enable virus scanning with ClamAV"
  type        = bool
  default     = false
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 1024
  validation {
    condition     = var.lambda_memory >= 128 && var.lambda_memory <= 10240
    error_message = "Lambda memory must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "max_pdf_pages" {
  description = "Maximum allowed pages in PDF"
  type        = number
  default     = 5
}

variable "settings_secret_arn" {
  description = "Optional Secrets Manager secret ARN containing Lambda runtime settings JSON"
  type        = string
  default     = ""
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_caller_identity" "current" {}

data "aws_region" "current" {
  provider = aws
}

# ============================================================================
# S3 Buckets
# ============================================================================

resource "aws_s3_bucket" "email_bucket" {
  bucket = "templevis-emails-${data.aws_caller_identity.current.account_id}-${var.aws_region}"

  tags = {
    Name = "TempleVis Email Bucket"
  }
}

resource "aws_s3_bucket_versioning" "email_bucket" {
  bucket = aws_s3_bucket.email_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "email_bucket" {
  bucket = aws_s3_bucket.email_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "email_bucket" {
  bucket = aws_s3_bucket.email_bucket.id

  rule {
    id     = "DeleteOldEmails"
    status = "Enabled"

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

resource "aws_s3_bucket_policy" "email_bucket_ses" {
  bucket = aws_s3_bucket.email_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSESWriteEmailObjects"
        Effect = "Allow"
        Principal = {
          Service = "ses.amazonaws.com"
        }
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.email_bucket.arn}/emails/*"
        Condition = {
          StringEquals = {
            "AWS:Referer" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "AllowSESReadBucketAcl"
        Effect = "Allow"
        Principal = {
          Service = "ses.amazonaws.com"
        }
        Action   = ["s3:GetBucketAcl"]
        Resource = aws_s3_bucket.email_bucket.arn
        Condition = {
          StringEquals = {
            "AWS:Referer" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket" "output_bucket" {
  bucket = "templevis-output-${data.aws_caller_identity.current.account_id}-${var.aws_region}"

  tags = {
    Name = "TempleVis Output Bucket"
  }
}

resource "aws_s3_bucket_versioning" "output_bucket" {
  bucket = aws_s3_bucket.output_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "output_bucket" {
  bucket = aws_s3_bucket.output_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "output_bucket" {
  bucket = aws_s3_bucket.output_bucket.id

  rule {
    id     = "DeleteOldOutputs"
    status = "Enabled"

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# ============================================================================
# SNS Topic
# ============================================================================

resource "aws_sns_topic" "email_notifications" {
  name              = "templevis-email-notifications-${var.environment}"
  display_name      = "TempleVis Email Notification Topic"
  kms_master_key_id = "alias/aws/sns"

  tags = {
    Name = "TempleVis Email Notifications"
  }
}

resource "aws_sns_topic_policy" "allow_ses_publish" {
  arn = aws_sns_topic.email_notifications.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSESPublish"
        Effect = "Allow"
        Principal = {
          Service = "ses.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.email_notifications.arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# ============================================================================
# IAM Role and Policies
# ============================================================================

resource "aws_iam_role" "lambda_execution" {
  name = "templevis-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "TempleVis Lambda Execution Role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "templevis-lambda-s3-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${aws_s3_bucket.email_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${aws_s3_bucket.output_bucket.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_ses_access" {
  name = "templevis-lambda-ses-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_secrets_access" {
  count = var.settings_secret_arn != "" ? 1 : 0

  name = "templevis-lambda-secrets-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.settings_secret_arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "secretsmanager.${var.aws_region}.amazonaws.com"
          }
        }
      }
    ]
  })
}

# ============================================================================
# Lambda Function and Layer
# ============================================================================

# Note: You'll need to build and create the layer ZIP file separately
# Run: python3 lambda/build_layer.py

resource "aws_lambda_layer_version" "dependencies" {
  filename   = "templevis-layer.zip"
  layer_name = "templevis-dependencies-${var.environment}"

  source_code_hash = filebase64sha256("templevis-layer.zip")

  compatible_runtimes = ["python3.11", "python3.12"]

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution
  ]
}

resource "aws_lambda_function" "processor" {
  filename      = "lambda_handler.zip"
  function_name = "templevis-pdf-processor-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "lambda_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory

  source_code_hash = filebase64sha256("lambda_handler.zip")

  ephemeral_storage {
    size = 10240
  }

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      OUTPUT_BUCKET        = aws_s3_bucket.output_bucket.id
      FROM_EMAIL           = var.from_email
      VIRUS_SCAN_ENABLED   = var.virus_scan_enabled ? "true" : "false"
      TEMPLEVIS_SETTINGS_SECRET_ID = var.settings_secret_arn
      ENVIRONMENT          = var.environment
      LOG_LEVEL            = var.environment == "prod" ? "INFO" : "DEBUG"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_s3_access,
    aws_iam_role_policy.lambda_ses_access
  ]

  tags = {
    Name = "TempleVis PDF Processor"
  }
}

resource "aws_lambda_permission" "allow_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.email_notifications.arn
}

resource "aws_sns_topic_subscription" "lambda" {
  topic_arn = aws_sns_topic.email_notifications.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.processor.arn
}

# ============================================================================
# SES Receipt Rules
# ============================================================================

resource "aws_ses_receipt_rule_set" "main" {
  rule_set_name = "templevis-ruleset-${var.environment}"
}

resource "aws_ses_active_receipt_rule_set" "main" {
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
}

resource "aws_ses_receipt_rule" "store_and_notify" {
  name          = "templevis-receipt-${var.environment}"
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
  recipients    = [var.receipt_email]
  enabled       = true
  scan_enabled  = true
  tls_policy    = "Require"

  s3_action {
    bucket_name       = aws_s3_bucket.email_bucket.id
    object_key_prefix = "emails/"
    topic_arn         = aws_sns_topic.email_notifications.arn
    position          = 1
  }

  stop_action {
    scope     = "RuleSet"
    topic_arn = aws_sns_topic.email_notifications.arn
    position  = 2
  }
}

# ============================================================================
# CloudWatch Alarms
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "templevis-lambda-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert on Lambda processing errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }

  tags = {
    Name = "TempleVis Lambda Errors"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "templevis-lambda-throttles-${var.environment}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alert on Lambda throttling"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.processor.function_name
  }

  tags = {
    Name = "TempleVis Lambda Throttles"
  }
}

# ============================================================================
# Outputs
# ============================================================================

output "lambda_function_arn" {
  description = "ARN of the TempleVis Lambda processor function"
  value       = aws_lambda_function.processor.arn
}

output "lambda_function_name" {
  description = "Name of the TempleVis Lambda processor function"
  value       = aws_lambda_function.processor.function_name
}

output "email_bucket_name" {
  description = "Name of the email receipt S3 bucket"
  value       = aws_s3_bucket.email_bucket.id
}

output "output_bucket_name" {
  description = "Name of the processed output S3 bucket"
  value       = aws_s3_bucket.output_bucket.id
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for email notifications"
  value       = aws_sns_topic.email_notifications.arn
}

output "ses_rule_set_name" {
  description = "Name of the SES receipt rule set"
  value       = aws_ses_receipt_rule_set.main.rule_set_name
}

output "deployment_info" {
  description = "Deployment information summary"
  value = {
    environment       = var.environment
    region            = var.aws_region
    lambda_function   = aws_lambda_function.processor.function_name
    receipt_email     = var.receipt_email
    from_email        = var.from_email
    virus_scan        = var.virus_scan_enabled
  }
  sensitive = true
}

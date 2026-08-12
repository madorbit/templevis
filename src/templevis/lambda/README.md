# AWS Lambda Integration for TempleVis

This directory contains everything needed to deploy TempleVis as an AWS Lambda function that processes PDF files received via email.

## Overview

The Lambda integration provides:

- **Automated email processing**: Receive PDF files via email and automatically process them
- **File validation**: Check file format, page count (max 5 pages), and content structure
- **Virus scanning**: Optional ClamAV integration for security scanning
- **Error notifications**: Automatically email errors back to the sender
- **Result delivery**: Send processed Excel files back to the sender via email
- **Production ready**: CloudFormation/Terraform infrastructure, monitoring, and logging

## Architecture

```
Email → SES → S3 Bucket → SNS Topic → Lambda Function → Process PDF → S3 Output → SES → Email
         (Receipt)                    (S3 Trigger)                                    (Response)
```

### Components

1. **SES Receipt Rules**: Captures incoming emails and stores attachments in S3
2. **S3 Email Bucket**: Stores received PDF files
3. **SNS Topic**: Notifies Lambda of new email receipts
4. **Lambda Function**: Main processor that validates and converts PDFs
5. **S3 Output Bucket**: Stores processed Excel files
6. **SES**: Sends success/error emails back to sender
7. **CloudWatch**: Logs and monitoring

## Prerequisites

### AWS Requirements

- AWS Account with appropriate permissions
- SES configured in the region (may need sandbox request approval for prod)
- Verified email addresses for sending/receiving

### Local Development Requirements

- Python 3.11 or higher
- AWS CLI v2 configured with credentials
- Bash shell
- Docker (optional, for Lambda layer building)
- jq (for JSON processing in deployment scripts)

### Python Dependencies

See [requirements.txt](../../requirements.txt) for the complete list. Key dependencies:

- `pdfplumber`: PDF table extraction
- `openpyxl`: Excel file generation
- `pandas`: Data manipulation

## Quick Start

### 1. Verify Prerequisites

```bash
# Check AWS CLI
aws --version

# Check Python
python3 --version

# Verify AWS credentials
aws sts get-caller-identity
```

### 2. Prepare Email Addresses

You need two verified SES email addresses:
- **FROM_EMAIL**: Email address that sends responses (must be verified in SES)
- **RECEIPT_EMAIL**: Email address that receives PDFs (must be verified in SES)

To verify an email in SES:
```bash
aws ses verify-email-identity --email-address your-email@example.com
```

### 3. Deploy Infrastructure

#### Option A: Using CloudFormation (Recommended)

```bash
cd src/templevis/lambda

# Make deploy script executable
chmod +x deploy.sh

# Deploy to development environment
./deploy.sh dev notify@temple.org schedule@temple.org

# Or production
./deploy.sh prod notify@temple.org schedule@temple.org
```

#### Option B: Using Terraform

```bash
cd src/templevis/lambda

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan \
  -var="from_email=notify@temple.org" \
  -var="receipt_email=schedule@temple.org" \
  -var="environment=dev"

# Apply the configuration
terraform apply \
  -var="from_email=notify@temple.org" \
  -var="receipt_email=schedule@temple.org" \
  -var="environment=dev"
```

### 4. Verify Deployment

```bash
# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name templevis-pdf-processor-dev

# Check Lambda function
aws lambda list-functions --query 'Functions[?contains(FunctionName, `templevis`)]'

# Check SES receipt rules
aws ses list-receipt-rule-sets
```

## Usage

### Sending a PDF for Processing

1. Send an email to the **RECEIPT_EMAIL** address
2. Attach your temple schedule PDF file
3. Within minutes:
   - If successful: Receive an email with processed Excel file details
   - If failed: Receive an error email with details about what went wrong

### Email Response Examples

**Success Response:**
```
Subject: TempleVis: Schedule Processed Successfully - abc12345

Your temple worker schedule PDF has been processed successfully.
Message ID: abc12345...
File: s3://templevis-output-123456789.../processed/abc12345/schedule.xlsx
```

**Error Response:**
```
Subject: TempleVis: Schedule Processing Failed - abc12345

Error: PDF has 8 pages but maximum allowed is 5

Please verify:
- PDF is in the correct temple schedule format
- PDF is not more than 5 pages
- PDF contains a valid worker schedule table
- Table includes recognized task codes (INI, CH, EO, etc.)
```

## Configuration

### Lambda Environment Variables

Set via CloudFormation parameters or Terraform variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT_BUCKET` | *(required)* | S3 bucket for processed Excel files |
| `FROM_EMAIL` | *(required)* | SES verified email for sending responses |
| `VIRUS_SCAN_ENABLED` | `false` | Enable ClamAV virus scanning |
| `ENVIRONMENT` | `dev` | Deployment environment (dev/staging/prod) |
| `LOG_LEVEL` | `DEBUG` | CloudWatch log level (DEBUG/INFO/WARNING) |

### Validation Rules

| Check | Limit | Error Message |
|-------|-------|---------------|
| File Extension | `.pdf` | Invalid file type |
| File Size | 50 MB | File size exceeds maximum |
| Page Count | 5 pages | PDF has too many pages |
| Table Structure | ≥3 columns | Does not appear to be valid format |
| Task Codes | Required | Missing recognized task codes |

### Customizing Validation

Edit [lambda_handler.py](lambda_handler.py) to change validation rules:

```python
# Maximum allowed pages
MAX_PAGES = 5

# Minimum expected columns in table
MIN_EXPECTED_COLUMNS = 3

# Recognized task codes
recognized_task_codes = ['INI', 'CH', 'EO', 'V-', 'LAU', 'BCR', 'TRG', 'STU', 'RDA', 'PM']
```

## Monitoring and Troubleshooting

### View Lambda Logs

```bash
# Stream live logs
aws logs tail /aws/lambda/templevis-pdf-processor-dev --follow

# View recent logs
aws logs tail /aws/lambda/templevis-pdf-processor-dev --since 1h
```

### Check Lambda Metrics

```bash
# View invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=templevis-pdf-processor-dev \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### Common Issues

**Lambda times out (duration > 300 seconds)**
- Increase timeout in CloudFormation: `LambdaTimeout` parameter
- Check PDF size and complexity
- Review CloudWatch logs for specific bottlenecks

**"File not found" or S3 access errors**
- Verify IAM role has correct S3 permissions
- Check bucket names match environment
- Ensure Lambda can read from email bucket and write to output bucket

**Email not received**
- Check SES receipt rules are enabled
- Verify email addresses are verified in SES
- Check SES sending limits and sandbox status
- Review SES bounce/complaint notifications

**"Not a valid PDF" errors**
- Verify file is actually a PDF
- Check PDF isn't corrupted
- Try opening with pdfplumber locally

**Virus scan fails**
- Ensure ClamAV layer is deployed
- Check ClamAV daemon is running
- Review Lambda layer for missing dependencies

## Advanced Configuration

### Enabling Virus Scanning

1. Create Lambda layer with ClamAV
2. Update CloudFormation parameter: `VirusScanEnabled: true`
3. Redeploy stack

```bash
./deploy.sh prod notify@temple.org schedule@temple.org --enable-virus-scan
```

### Custom Lambda Layer

If you need additional Python packages:

1. Edit `requirements.txt` to add packages
2. Rebuild layer: `python3 build_layer.py`
3. Upload to S3 and update Lambda layer

```bash
# Build layer
python3 src/templevis/lambda/build_layer.py --output-dir src/templevis/lambda/build

# Upload
aws s3 cp src/templevis/lambda/build/templevis-layer.zip \
  s3://templevis-lambda-layers-YOUR-ACCOUNT-ID-us-east-1/
```

### Using Different AWS Regions

```bash
# Deploy to different region
export AWS_REGION=us-west-2

./deploy.sh prod notify@temple.org schedule@temple.org
```

## Cost Estimation

### Typical Monthly Costs (Development)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 100 invocations × 300s @ 1GB | $0.50 |
| S3 Storage | 100 files × 500KB | $0.01 |
| SES | 100 emails | Free (sandbox) |
| CloudWatch | Logs @ 1GB/month | $0.50 |
| **Total** | | ~$1.00 |

### Production Optimization

- Use Lambda Reserved Concurrency for predictable load
- Enable S3 Intelligent-Tiering for long-term storage
- Set up SES sending limits to match your needs
- Configure CloudWatch Logs retention (e.g., 30 days)

## Deployment Updates

### Update Lambda Code

```bash
# Update handler code
# Edit src/templevis/lambda/lambda_handler.py

# Rebuild and deploy
cd src/templevis/lambda
./deploy.sh prod notify@temple.org schedule@temple.org
```

### Update Dependencies

```bash
# Add new dependency to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Rebuild layer
python3 src/templevis/lambda/build_layer.py

# Redeploy
cd src/templevis/lambda
./deploy.sh prod notify@temple.org schedule@temple.org
```

### Rollback Previous Version

```bash
# List Lambda versions
aws lambda list-versions-by-function \
  --function-name templevis-pdf-processor-prod

# Deploy specific version
aws lambda update-function-configuration \
  --function-name templevis-pdf-processor-prod \
  --environment Variables={VERSION=previous}
```

## Security Best Practices

1. **Email Addresses**: Keep FROM_EMAIL and RECEIPT_EMAIL private
2. **SES Sandbox**: Request production access when ready
3. **IAM Permissions**: Use principle of least privilege
4. **S3 Encryption**: Enable at-rest encryption for buckets
5. **Virus Scanning**: Enable for production deployments
6. **Logging**: Monitor CloudWatch for suspicious activity
7. **VPC**: Consider placing Lambda in VPC for additional security

## Cleanup and Removal

### Remove CloudFormation Stack

```bash
# Warning: This deletes all resources created by the stack
aws cloudformation delete-stack --stack-name templevis-pdf-processor-dev

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name templevis-pdf-processor-dev
```

### Remove Terraform Resources

```bash
cd src/templevis/lambda

# Review resources to be deleted
terraform plan -destroy

# Delete all resources
terraform destroy \
  -var="from_email=notify@temple.org" \
  -var="receipt_email=schedule@temple.org" \
  -var="environment=dev"
```

### Clean Up S3 Buckets

```bash
# List objects and delete
aws s3 rm s3://templevis-emails-YOUR-ACCOUNT-ID-us-east-1 --recursive
aws s3 rm s3://templevis-output-YOUR-ACCOUNT-ID-us-east-1 --recursive

# Delete bucket
aws s3 rb s3://templevis-emails-YOUR-ACCOUNT-ID-us-east-1
aws s3 rb s3://templevis-output-YOUR-ACCOUNT-ID-us-east-1
```

## Support and Troubleshooting

### Getting Help

1. Check CloudWatch logs: `aws logs tail /aws/lambda/templevis-pdf-processor-dev`
2. Review Lambda error details in CloudFormation stack events
3. Test locally with sample PDF: `python3 -m templevis process sample.pdf`
4. Check SES bounce/complaint logs

### Performance Testing

```bash
# Send test email to trigger Lambda
python3 -c "
import boto3
ses = boto3.client('ses')
ses.send_email(
    Source='from@temple.org',
    Destination={'ToAddresses': ['schedule@temple.org']},
    Message={
        'Subject': {'Data': 'Test'},
        'Body': {'Text': {'Data': 'Test'}}
    }
)
"
```

## References

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon SES Documentation](https://docs.aws.amazon.com/ses/)
- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [TempleVis Documentation](../../README.md)

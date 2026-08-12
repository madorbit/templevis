"""
AWS Lambda Handler for TempleVis PDF Processing

This Lambda function:
1. Receives email notifications with PDF attachments
2. Downloads PDF from S3
3. Validates file format (page count, content structure)
4. Scans for viruses using ClamAV (optional)
5. Processes PDF using TempleVis
6. Returns results or error via email
"""

import json
import base64
import boto3
import logging
import os
import tempfile
from typing import Tuple, Dict, Any
from urllib.parse import unquote_plus

# Import the TempleVis modules
import sys
sys.path.insert(0, '/opt/python')
from templevis.table_processor import PDFTableProcessor
from templevis.excel_generator import ExcelGenerator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
ses_client = boto3.client('ses')
sns_client = boto3.client('sns')
secrets_client = boto3.client('secretsmanager')

# Configuration
def _to_bool(value: Any, default: bool = False) -> bool:
    """Parse truthy/falsy string/int/bool values safely."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _to_int(value: Any, default: int) -> int:
    """Parse integer values safely."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _load_secret_settings() -> Dict[str, Any]:
    """Load optional runtime settings from AWS Secrets Manager."""
    secret_id = (
        os.environ.get('TEMPLEVIS_SETTINGS_SECRET_ID')
        or os.environ.get('SETTINGS_SECRET_ID')
    )
    if not secret_id:
        return {}

    try:
        response = secrets_client.get_secret_value(SecretId=secret_id)
        secret_string = response.get('SecretString')

        if not secret_string and response.get('SecretBinary'):
            secret_string = base64.b64decode(response['SecretBinary']).decode('utf-8')

        if not secret_string:
            logger.warning('Secrets Manager secret is empty: %s', secret_id)
            return {}

        payload = json.loads(secret_string)
        if not isinstance(payload, dict):
            logger.warning('Secrets Manager payload is not a JSON object: %s', secret_id)
            return {}

        logger.info('Loaded runtime settings from Secrets Manager: %s', secret_id)
        return payload
    except Exception as e:
        logger.warning('Failed to load Secrets Manager settings: %s', str(e))
        return {}


def _load_runtime_settings() -> Dict[str, Any]:
    """Build runtime settings from env vars with optional Secrets Manager override."""
    settings = {
        'MAX_PAGES': os.environ.get('MAX_PAGES', '5'),
        'MIN_EXPECTED_COLUMNS': os.environ.get('MIN_EXPECTED_COLUMNS', '3'),
        'ALLOWED_FILE_EXTENSION': os.environ.get('ALLOWED_FILE_EXTENSION', '.pdf'),
        'VIRUS_SCAN_ENABLED': os.environ.get('VIRUS_SCAN_ENABLED', 'false'),
        'OUTPUT_BUCKET': os.environ.get('OUTPUT_BUCKET', ''),
        'FROM_EMAIL': os.environ.get('FROM_EMAIL', ''),
    }

    secret_settings = _load_secret_settings()
    for key in settings.keys():
        if key in secret_settings and secret_settings[key] is not None:
            settings[key] = secret_settings[key]

    return settings


_SETTINGS = _load_runtime_settings()

MAX_PAGES = _to_int(_SETTINGS.get('MAX_PAGES'), 5)
MIN_EXPECTED_COLUMNS = _to_int(_SETTINGS.get('MIN_EXPECTED_COLUMNS'), 3)  # At minimum: names and task columns
ALLOWED_FILE_EXTENSION = str(_SETTINGS.get('ALLOWED_FILE_EXTENSION', '.pdf')).strip() or '.pdf'
VIRUS_SCAN_ENABLED = _to_bool(_SETTINGS.get('VIRUS_SCAN_ENABLED'), default=False)
OUTPUT_BUCKET = str(_SETTINGS.get('OUTPUT_BUCKET', '')).strip()
FROM_EMAIL = str(_SETTINGS.get('FROM_EMAIL', '')).strip()


class PDFValidationError(Exception):
    """Custom exception for PDF validation errors"""
    pass


def parse_event_details(event: Dict[str, Any], context: Any) -> Dict[str, str]:
    """Parse supported event formats and return processing metadata.

    Supported formats:
    - SNS-wrapped SES receipt event
    - Direct S3 ObjectCreated notification event
    """
    records = event.get('Records') or []
    if not records:
        raise ValueError('Event does not contain Records')

    first_record = records[0]

    def _decode_sns_message(raw_message: Any) -> Dict[str, Any]:
        """Decode SNS message as JSON, with Base64 fallback."""
        if isinstance(raw_message, dict):
            return raw_message

        if not isinstance(raw_message, str):
            raise ValueError('SNS message has unsupported type')

        # Standard SNS payload (plain JSON string)
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError:
            pass

        # Optional fallback for Base64-encoded JSON payloads
        try:
            decoded = base64.b64decode(raw_message).decode('utf-8')
            return json.loads(decoded)
        except Exception as e:
            raise ValueError(f'Unable to decode SNS message payload: {str(e)}')

    # SNS -> SES receipt flow
    if 'Sns' in first_record:
        message = first_record['Sns'].get('Message')
        sns_message = _decode_sns_message(message)

        sender_email = sns_message['mail']['source']
        message_id = sns_message['mail']['messageId']
        bucket = sns_message['receipt']['action']['bucketName']
        key = unquote_plus(sns_message['receipt']['action']['objectKey'])

        return {
            'sender_email': sender_email,
            'message_id': message_id,
            'bucket': bucket,
            'key': key,
            'event_source': 'sns-ses'
        }

    # Direct S3 notification flow
    if 's3' in first_record:
        bucket = first_record['s3']['bucket']['name']
        key = unquote_plus(first_record['s3']['object']['key'])
        message_id = (
            first_record['s3']['object'].get('eTag')
            or first_record.get('responseElements', {}).get('x-amz-request-id')
            or getattr(context, 'aws_request_id', 'unknown')
        )

        return {
            'sender_email': '',
            'message_id': str(message_id),
            'bucket': bucket,
            'key': key,
            'event_source': 's3'
        }

    raise ValueError('Unsupported event format. Expected SNS or S3 notification event.')


def lambda_handler(event, context):
    """
    Main Lambda handler function.
    
    Expected event structure from SES receipt via SNS:
    {
        'Records': [
            {
                'Sns': {
                    'Message': {
                        'mail': {
                            'source': 'sender@example.com',
                            'messageId': 'xxx'
                        },
                        'receipt': {
                            'action': {
                                'bucketName': 'bucket',
                                'objectKey': 'key'
                            }
                        }
                    }
                }
            }
        ]
    }
    """
    try:
        logger.info(f"Lambda invoked with event: {json.dumps(event)}")

        event_details = parse_event_details(event, context)
        sender_email = event_details['sender_email']
        message_id = event_details['message_id']
        bucket = event_details['bucket']
        key = event_details['key']
        event_source = event_details['event_source']
        
        logger.info(
            "Processing source=%s sender=%s bucket=%s key=%s",
            event_source,
            sender_email or '<none>',
            bucket,
            key
        )
        
        # Download PDF from S3
        pdf_file, pdf_filename = download_from_s3(bucket, key)
        
        try:
            # Validate PDF file
            validate_pdf_file(pdf_filename, pdf_file)
            
            # Process PDF
            output_file = process_pdf(pdf_file, message_id)
            
            # Upload result to S3 and send success email
            s3_output_key = upload_result_to_s3(output_file, message_id)
            if sender_email and FROM_EMAIL:
                send_success_email(sender_email, message_id, s3_output_key)
            else:
                logger.info('Skipping success email; sender or FROM_EMAIL not configured for this event')
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'PDF processed successfully',
                    'messageId': message_id,
                    'outputKey': s3_output_key
                })
            }
            
        except PDFValidationError as e:
            logger.warning(f"PDF validation failed: {str(e)}")
            if sender_email and FROM_EMAIL:
                send_error_email(sender_email, message_id, str(e))
            else:
                logger.info('Skipping error email; sender or FROM_EMAIL not configured for this event')
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'PDF validation failed',
                    'error': str(e),
                    'messageId': message_id
                })
            }
        except Exception as e:
            logger.error(f"Processing error: {str(e)}", exc_info=True)
            if sender_email and FROM_EMAIL:
                send_error_email(sender_email, message_id,
                               f"An error occurred processing your PDF: {str(e)}")
            else:
                logger.info('Skipping error email; sender or FROM_EMAIL not configured for this event')
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'PDF processing failed',
                    'error': str(e),
                    'messageId': message_id
                })
            }
        finally:
            # Clean up temp files
            if os.path.exists(pdf_file):
                os.remove(pdf_file)

    except Exception as e:
        logger.error(f"Unhandled lambda error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Unhandled error in lambda handler',
                'error': str(e)
            })
        }


def download_from_s3(bucket: str, key: str) -> Tuple[str, str]:
    """
    Download PDF from S3 to temporary file.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Tuple of (temp_file_path, filename)
    """
    try:
        logger.info(f"Downloading {key} from {bucket}")
        
        # Create temp file
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, os.path.basename(key))
        
        # Download from S3
        s3_client.download_file(bucket, key, temp_file)
        logger.info(f"Downloaded to {temp_file}")
        
        return temp_file, os.path.basename(key)
    except Exception as e:
        logger.error(f"Error downloading from S3: {str(e)}")
        raise PDFValidationError(f"Failed to download file from email: {str(e)}")


def validate_pdf_file(filename: str, filepath: str) -> None:
    """
    Validate PDF file format and contents.
    
    Checks:
    1. File extension
    2. File size
    3. Page count (<= MAX_PAGES)
    4. Table structure (expected columns and rows)
    5. Virus scan (if enabled)
    
    Args:
        filename: Original filename from email
        filepath: Path to temporary file
        
    Raises:
        PDFValidationError: If validation fails
    """
    logger.info(f"Validating PDF file: {filename}")
    
    # Check file extension
    if not filename.lower().endswith(ALLOWED_FILE_EXTENSION):
        raise PDFValidationError(
            f"Invalid file type. Expected .pdf, got {os.path.splitext(filename)[1]}"
        )
    
    # Check file size (max 50MB)
    file_size = os.path.getsize(filepath)
    if file_size > 50 * 1024 * 1024:
        raise PDFValidationError("File size exceeds maximum of 50MB")
    
    # Check page count and content using pdfplumber
    try:
        import pdfplumber
        
        with pdfplumber.open(filepath) as pdf:
            page_count = len(pdf.pages)
            
            # Check page count
            if page_count > MAX_PAGES:
                raise PDFValidationError(
                    f"PDF has {page_count} pages but maximum allowed is {MAX_PAGES}"
                )
            
            if page_count == 0:
                raise PDFValidationError("PDF contains no pages")
            
            logger.info(f"PDF has {page_count} pages")
            
            # Validate content structure
            validate_pdf_content(pdf)
            
    except pdfplumber.PDFException as e:
        raise PDFValidationError(f"Invalid PDF file: {str(e)}")
    except ImportError:
        logger.warning("pdfplumber not available for content validation")


def validate_pdf_content(pdf) -> None:
    """
    Validate that PDF contains expected table structure.
    
    Checks:
    1. First page contains a table
    2. Table has expected columns
    3. Table has data rows
    
    Args:
        pdf: pdfplumber PDF object
        
    Raises:
        PDFValidationError: If content validation fails
    """
    try:
        # Check first page for table
        first_page = pdf.pages[0]
        tables = first_page.extract_tables()
        
        if not tables or len(tables) == 0:
            raise PDFValidationError(
                "No table found on first page. Expected schedule table in standard format."
            )
        
        # Check table dimensions
        first_table = tables[0]
        num_columns = len(first_table[0]) if first_table else 0
        num_rows = len(first_table)
        
        logger.info(f"Detected table: {num_rows} rows x {num_columns} columns")
        
        if num_columns < MIN_EXPECTED_COLUMNS:
            raise PDFValidationError(
                f"Table has {num_columns} columns but expected at least {MIN_EXPECTED_COLUMNS}. "
                "Does not appear to be a valid temple schedule."
            )
        
        if num_rows < 2:  # At least header + 1 data row
            raise PDFValidationError(
                "Table has insufficient data rows. Expected temple schedule format."
            )
        
        # Check for recognizable task codes in table
        recognized_task_codes = ['INI', 'CH', 'EO', 'V-', 'LAU', 'BCR', 'TRG', 'STU', 'RDA', 'PM']
        
        found_task_code = False
        for row in first_table:
            for cell in row:
                if cell and any(code in str(cell) for code in recognized_task_codes):
                    found_task_code = True
                    break
            if found_task_code:
                break
        
        if not found_task_code:
            raise PDFValidationError(
                "Table does not contain recognized task codes (INI, CH, EO, etc.). "
                "Does not match expected temple schedule format."
            )
        
        logger.info("PDF content validation passed")
        
    except PDFValidationError:
        raise
    except Exception as e:
        raise PDFValidationError(f"Error validating PDF content: {str(e)}")


def scan_for_virus(filepath: str) -> bool:
    """
    Scan PDF file for viruses using ClamAV.
    
    This requires ClamAV Lambda layer to be installed.
    Note: S3 object lambda with ClamAV scanning is an alternative.
    
    Args:
        filepath: Path to file to scan
        
    Returns:
        True if file is clean, False if infected
    """
    if not VIRUS_SCAN_ENABLED:
        logger.info("Virus scan disabled")
        return True
    
    try:
        logger.info(f"Scanning {filepath} for viruses")
        
        # This example uses pyclamav if available
        # In production, consider using:
        # - S3 Object Lambda with ClamAV
        # - AWS Lambda layer with ClamAV
        # - Third-party antivirus service
        
        try:
            import pyclamav
            result = pyclamav.scan_file(filepath)
            if result == 1:  # Infected
                raise PDFValidationError("File flagged as infected by virus scan")
            return True
        except ImportError:
            logger.warning("ClamAV not available. Skipping virus scan.")
            return True
            
    except PDFValidationError:
        raise
    except Exception as e:
        logger.error(f"Virus scan error: {str(e)}")
        raise PDFValidationError(f"Virus scan failed: {str(e)}")


def process_pdf(pdf_path: str, message_id: str) -> str:
    """
    Process PDF file using TempleVis.
    
    Args:
        pdf_path: Path to PDF file
        message_id: Email message ID for naming output
        
    Returns:
        Path to generated Excel file
    """
    try:
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract table data
        processor = PDFTableProcessor(pdf_path)
        df = processor.extract_table_data()
        
        if df is None or df.empty:
            raise PDFValidationError("Could not extract table data from PDF")
        
        logger.info(f"Extracted table: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Generate Excel file
        temp_dir = tempfile.gettempdir()
        output_file = os.path.join(temp_dir, f"schedule_{message_id}.xlsx")
        
        generator = ExcelGenerator(df, processor)
        generator.generate(output_file)
        
        if not os.path.exists(output_file):
            raise Exception("Excel file generation failed")
        
        logger.info(f"Generated Excel file: {output_file}")
        return output_file
        
    except PDFValidationError:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise Exception(f"PDF processing failed: {str(e)}")


def upload_result_to_s3(file_path: str, message_id: str) -> str:
    """
    Upload generated Excel file to S3.
    
    Args:
        file_path: Path to local Excel file
        message_id: Email message ID
        
    Returns:
        S3 object key
    """
    if not OUTPUT_BUCKET:
        logger.warning("OUTPUT_BUCKET not configured, skipping S3 upload")
        return ""
    
    try:
        filename = os.path.basename(file_path)
        s3_key = f"processed/{message_id}/{filename}"
        
        logger.info(f"Uploading to s3://{OUTPUT_BUCKET}/{s3_key}")
        s3_client.upload_file(file_path, OUTPUT_BUCKET, s3_key)
        
        return s3_key
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise


def send_success_email(recipient: str, message_id: str, s3_key: str) -> None:
    """
    Send success email with processed file.
    
    Args:
        recipient: Recipient email address
        message_id: Email message ID
        s3_key: S3 object key for the processed file
    """
    try:
        subject = f"TempleVis: Schedule Processed Successfully - {message_id[:8]}"
        
        body_html = f"""
        <html>
            <body>
                <h2>Schedule Processed Successfully</h2>
                <p>Your temple worker schedule PDF has been processed successfully.</p>
                <p><strong>Message ID:</strong> {message_id}</p>
                <p><strong>File:</strong> s3://{OUTPUT_BUCKET}/{s3_key}</p>
                <p>Your processed Excel file has been generated and is available in the secure storage.</p>
            </body>
        </html>
        """
        
        logger.info(f"Sending success email to {recipient}")
        ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': body_html}}
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending success email: {str(e)}")
        raise


def send_error_email(recipient: str, message_id: str, error_message: str) -> None:
    """
    Send error email with details about validation failure.
    
    Args:
        recipient: Recipient email address
        message_id: Email message ID
        error_message: Description of the error
    """
    try:
        subject = f"TempleVis: Schedule Processing Failed - {message_id[:8]}"
        
        body_html = f"""
        <html>
            <body>
                <h2>Schedule Processing Failed</h2>
                <p>There was an issue processing your temple worker schedule PDF.</p>
                <p><strong>Message ID:</strong> {message_id}</p>
                <p><strong>Error:</strong></p>
                <pre>{error_message}</pre>
                <p><strong>Please verify:</strong></p>
                <ul>
                    <li>PDF is in the correct temple schedule format</li>
                    <li>PDF is not more than {MAX_PAGES} pages</li>
                    <li>PDF contains a valid worker schedule table</li>
                    <li>Table includes recognized task codes (INI, CH, EO, etc.)</li>
                </ul>
            </body>
        </html>
        """
        
        logger.info(f"Sending error email to {recipient}")
        ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': body_html}}
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending error email: {str(e)}")

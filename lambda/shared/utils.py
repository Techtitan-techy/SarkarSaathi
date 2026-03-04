"""
SarkariSaathi - Utility Functions

Common utility functions used across Lambda functions.
"""

import json
import os
import hashlib
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError


# ========================================
# AWS Clients
# ========================================

def get_dynamodb_client():
    """Get DynamoDB client"""
    return boto3.client('dynamodb', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))


def get_dynamodb_resource():
    """Get DynamoDB resource"""
    return boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))


def get_s3_client():
    """Get S3 client"""
    return boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))


def get_bedrock_client():
    """Get Bedrock Runtime client"""
    return boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))


def get_transcribe_client():
    """Get Transcribe client"""
    return boto3.client('transcribe', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))


def get_polly_client():
    """Get Polly client"""
    return boto3.client('polly', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))


def get_kms_client():
    """Get KMS client"""
    return boto3.client('kms', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))


# ========================================
# ID Generation
# ========================================

def generate_user_id() -> str:
    """Generate unique user ID"""
    return f"user_{uuid.uuid4().hex[:16]}"


def generate_session_id() -> str:
    """Generate unique session ID"""
    return f"session_{uuid.uuid4().hex[:16]}"


def generate_application_id() -> str:
    """Generate unique application ID"""
    return f"app_{uuid.uuid4().hex[:16]}"


def generate_scheme_id(scheme_name: str) -> str:
    """Generate scheme ID from name"""
    # Create a hash of the scheme name for consistency
    name_hash = hashlib.md5(scheme_name.encode()).hexdigest()[:8]
    return f"scheme_{name_hash}"


def generate_tracking_number() -> str:
    """Generate application tracking number"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"SS{timestamp}{random_suffix}"


# ========================================
# Time Utilities
# ========================================

def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.utcnow().isoformat() + 'Z'


def get_ttl_timestamp(hours: int = 24) -> int:
    """Get Unix timestamp for DynamoDB TTL"""
    future_time = datetime.utcnow() + timedelta(hours=hours)
    return int(future_time.timestamp())


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO format timestamp string"""
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))


# ========================================
# Response Builders
# ========================================

def build_success_response(data: Any, status_code: int = 200, metadata: Optional[Dict] = None) -> Dict:
    """Build successful API response"""
    response_body = {
        'success': True,
        'data': data
    }
    
    if metadata:
        response_body['metadata'] = metadata
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(response_body)
    }


def build_error_response(
    error_message: str,
    error_code: str = 'INTERNAL_ERROR',
    status_code: int = 500,
    retryable: bool = False
) -> Dict:
    """Build error API response"""
    response_body = {
        'success': False,
        'error': {
            'errorCode': error_code,
            'errorMessage': error_message,
            'retryable': retryable,
            'timestamp': get_current_timestamp()
        }
    }
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(response_body)
    }


# ========================================
# DynamoDB Utilities
# ========================================

def dynamodb_to_dict(item: Dict) -> Dict:
    """Convert DynamoDB item format to regular dict"""
    from boto3.dynamodb.types import TypeDeserializer
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in item.items()}


def dict_to_dynamodb(data: Dict) -> Dict:
    """Convert regular dict to DynamoDB item format"""
    from boto3.dynamodb.types import TypeSerializer
    serializer = TypeSerializer()
    return {k: serializer.serialize(v) for k, v in data.items()}


# ========================================
# S3 Utilities
# ========================================

def generate_presigned_url(bucket: str, key: str, expiration: int = 3600) -> str:
    """Generate presigned URL for S3 object"""
    s3_client = get_s3_client()
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return ""


def upload_to_s3(bucket: str, key: str, data: bytes, content_type: str = 'application/octet-stream') -> bool:
    """Upload data to S3"""
    s3_client = get_s3_client()
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        return True
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return False


def download_from_s3(bucket: str, key: str) -> Optional[bytes]:
    """Download data from S3"""
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        return None


# ========================================
# Caching Utilities
# ========================================

def generate_cache_key(text: str, language: str) -> str:
    """Generate cache key for TTS audio"""
    content = f"{text}_{language}"
    return hashlib.sha256(content.encode()).hexdigest()


def check_cache_exists(bucket: str, cache_key: str) -> bool:
    """Check if cached item exists in S3"""
    s3_client = get_s3_client()
    try:
        s3_client.head_object(Bucket=bucket, Key=cache_key)
        return True
    except ClientError:
        return False


# ========================================
# Language Utilities
# ========================================

LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi'
}


def get_language_name(code: str) -> str:
    """Get language name from code"""
    return LANGUAGE_NAMES.get(code, 'English')


def detect_language(text: str) -> str:
    """Simple language detection (placeholder - use proper library in production)"""
    # This is a simplified version - in production, use a proper language detection library
    # For now, default to Hindi if text contains Devanagari script, else English
    if any('\u0900' <= char <= '\u097F' for char in text):
        return 'hi'
    return 'en'


# ========================================
# Validation Utilities
# ========================================

def validate_required_fields(data: Dict, required_fields: list) -> Optional[str]:
    """Validate that required fields are present"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    return None


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    # Remove any potentially harmful characters
    sanitized = text.strip()[:max_length]
    return sanitized


# ========================================
# Error Handling
# ========================================

def handle_exception(e: Exception, context: str = "") -> Dict:
    """Handle exceptions and return error response"""
    error_message = f"{context}: {str(e)}" if context else str(e)
    print(f"Error: {error_message}")
    
    if isinstance(e, ClientError):
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            return build_error_response(
                error_message="Resource not found",
                error_code="NOT_FOUND",
                status_code=404
            )
        elif error_code == 'ThrottlingException':
            return build_error_response(
                error_message="Rate limit exceeded",
                error_code="RATE_LIMIT_EXCEEDED",
                status_code=429,
                retryable=True
            )
    
    return build_error_response(
        error_message=error_message,
        error_code="INTERNAL_ERROR",
        status_code=500
    )


# ========================================
# Logging Utilities
# ========================================

def log_event(event_type: str, details: Dict):
    """Log structured event"""
    log_entry = {
        'timestamp': get_current_timestamp(),
        'eventType': event_type,
        'details': details
    }
    print(json.dumps(log_entry))


def log_api_call(method: str, path: str, status_code: int, duration_ms: float):
    """Log API call metrics"""
    log_event('api_call', {
        'method': method,
        'path': path,
        'statusCode': status_code,
        'durationMs': duration_ms
    })


# ========================================
# Legacy Compatibility Functions
# ========================================

def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix (legacy compatibility)"""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def create_response(status_code: int, body: Dict) -> Dict:
    """Create API Gateway response (legacy compatibility)"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }


def log_info(message: str):
    """Log info message"""
    print(f"INFO: {message}")


def log_error(message: str):
    """Log error message"""
    print(f"ERROR: {message}")

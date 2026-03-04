"""
Audio Input Handler Lambda Function

Handles audio file uploads from API Gateway.
Validates audio format and size, stores in S3, and returns presigned URL.

Requirements: 1.1, 10.1
"""

import json
import base64
import os
import hashlib
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

# Import shared utilities
from shared.utils import (
    get_s3_client,
    build_success_response,
    build_error_response,
    get_current_timestamp,
    validate_required_fields,
    generate_presigned_url,
    log_event
)

# Environment variables
AUDIO_BUCKET = os.environ.get('AUDIO_BUCKET', 'sarkari-saathi-audio')
MAX_AUDIO_SIZE_MB = int(os.environ.get('MAX_AUDIO_SIZE_MB', '10'))
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024

# Supported audio formats
SUPPORTED_FORMATS = {
    'audio/mpeg': '.mp3',
    'audio/mp3': '.mp3',
    'audio/wav': '.wav',
    'audio/wave': '.wav',
    'audio/x-wav': '.wav'
}

# Magic bytes for format validation
AUDIO_MAGIC_BYTES = {
    'mp3': [b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'],
    'wav': [b'RIFF']
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for audio input processing
    
    Expected request body:
    {
        "audio": "base64_encoded_audio_data",
        "format": "audio/mpeg" or "audio/wav",
        "userId": "user_id",
        "sessionId": "session_id"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "audioId": "unique_audio_id",
            "s3Key": "uploads/audio_id.mp3",
            "presignedUrl": "https://...",
            "expiresIn": 3600,
            "uploadedAt": "2024-01-01T00:00:00Z"
        }
    }
    """
    try:
        log_event('audio_input_handler_invoked', {
            'requestId': context.request_id if context and hasattr(context, 'request_id') else 'local'
        })
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['audio', 'format'])
        if validation_error:
            return build_error_response(
                error_message=validation_error,
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        audio_data_b64 = body['audio']
        content_type = body['format']
        user_id = body.get('userId', 'anonymous')
        session_id = body.get('sessionId', 'unknown')
        
        # Validate audio format
        if content_type not in SUPPORTED_FORMATS:
            return build_error_response(
                error_message=f"Unsupported audio format. Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}",
                error_code='INVALID_FORMAT',
                status_code=400
            )
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data_b64)
        except Exception as e:
            return build_error_response(
                error_message="Invalid base64 encoded audio data",
                error_code='INVALID_ENCODING',
                status_code=400
            )
        
        # Validate audio size
        audio_size_mb = len(audio_bytes) / (1024 * 1024)
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            return build_error_response(
                error_message=f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE_MB}MB, received: {audio_size_mb:.2f}MB",
                error_code='FILE_TOO_LARGE',
                status_code=413
            )
        
        # Validate audio file magic bytes
        file_extension = SUPPORTED_FORMATS[content_type]
        format_key = file_extension.replace('.', '')
        
        if not validate_audio_magic_bytes(audio_bytes, format_key):
            return build_error_response(
                error_message=f"Invalid {format_key.upper()} file format",
                error_code='INVALID_FILE_FORMAT',
                status_code=400
            )
        
        # Generate unique audio ID
        audio_id = generate_audio_id(audio_bytes, user_id, session_id)
        s3_key = f"uploads/{audio_id}{file_extension}"
        
        # Upload to S3
        s3_client = get_s3_client()
        try:
            s3_client.put_object(
                Bucket=AUDIO_BUCKET,
                Key=s3_key,
                Body=audio_bytes,
                ContentType=content_type,
                Metadata={
                    'userId': user_id,
                    'sessionId': session_id,
                    'uploadedAt': get_current_timestamp(),
                    'sizeBytes': str(len(audio_bytes))
                }
            )
            
            log_event('audio_uploaded_to_s3', {
                'audioId': audio_id,
                's3Key': s3_key,
                'sizeBytes': len(audio_bytes),
                'format': format_key
            })
            
        except ClientError as e:
            log_event('s3_upload_failed', {
                'error': str(e),
                'audioId': audio_id
            })
            return build_error_response(
                error_message="Failed to upload audio to storage",
                error_code='STORAGE_ERROR',
                status_code=500,
                retryable=True
            )
        
        # Generate presigned URL for processing (1 hour expiration)
        presigned_url = generate_presigned_url(AUDIO_BUCKET, s3_key, expiration=3600)
        
        if not presigned_url:
            return build_error_response(
                error_message="Failed to generate access URL",
                error_code='URL_GENERATION_ERROR',
                status_code=500
            )
        
        # Return success response
        response_data = {
            'audioId': audio_id,
            's3Key': s3_key,
            's3Bucket': AUDIO_BUCKET,
            'presignedUrl': presigned_url,
            'expiresIn': 3600,
            'uploadedAt': get_current_timestamp(),
            'sizeBytes': len(audio_bytes),
            'format': format_key
        }
        
        return build_success_response(
            data=response_data,
            status_code=200,
            metadata={
                'processingTime': 'fast',
                'userId': user_id
            }
        )
        
    except Exception as e:
        log_event('audio_input_handler_error', {
            'error': str(e),
            'errorType': type(e).__name__
        })
        return build_error_response(
            error_message="Internal server error processing audio input",
            error_code='INTERNAL_ERROR',
            status_code=500
        )


def validate_audio_magic_bytes(audio_bytes: bytes, format_key: str) -> bool:
    """
    Validate audio file format by checking magic bytes
    
    Args:
        audio_bytes: Raw audio file bytes
        format_key: Format key ('mp3' or 'wav')
    
    Returns:
        True if valid format, False otherwise
    """
    if format_key not in AUDIO_MAGIC_BYTES:
        return True  # Skip validation for unknown formats
    
    magic_bytes_list = AUDIO_MAGIC_BYTES[format_key]
    
    for magic_bytes in magic_bytes_list:
        if audio_bytes.startswith(magic_bytes):
            return True
    
    # For WAV files, also check for WAVE format
    if format_key == 'wav' and len(audio_bytes) >= 12:
        if audio_bytes[0:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE':
            return True
    
    return False


def generate_audio_id(audio_bytes: bytes, user_id: str, session_id: str) -> str:
    """
    Generate unique audio ID based on content hash and metadata
    
    Args:
        audio_bytes: Raw audio file bytes
        user_id: User identifier
        session_id: Session identifier
    
    Returns:
        Unique audio ID string
    """
    # Create hash from audio content
    content_hash = hashlib.sha256(audio_bytes).hexdigest()[:16]
    
    # Create hash from metadata
    metadata = f"{user_id}_{session_id}_{get_current_timestamp()}"
    metadata_hash = hashlib.md5(metadata.encode()).hexdigest()[:8]
    
    return f"audio_{content_hash}_{metadata_hash}"

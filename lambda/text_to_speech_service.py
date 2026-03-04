"""
Text-to-Speech Service Lambda Function

Integrates Amazon Polly and Bhashini TTS for multilingual speech synthesis.
Implements S3-based caching with 7-day TTL and CloudFront CDN distribution.

Requirements: 1.2, 2.1
"""

import json
import os
import hashlib
import time
import requests
from typing import Dict, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

# Import shared utilities
from shared.utils import (
    get_s3_client,
    get_polly_client,
    build_success_response,
    build_error_response,
    get_current_timestamp,
    validate_required_fields,
    generate_presigned_url,
    generate_cache_key,
    check_cache_exists,
    log_event
)

# Environment variables
TTS_CACHE_BUCKET = os.environ.get('TTS_CACHE_BUCKET', 'sarkari-saathi-tts-cache')
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', '')
BHASHINI_API_URL = os.environ.get('BHASHINI_API_URL', 'https://dhruva-api.bhashini.gov.in')
BHASHINI_API_KEY = os.environ.get('BHASHINI_API_KEY', '')
ENABLE_BHASHINI = os.environ.get('ENABLE_BHASHINI', 'false').lower() == 'true'
CACHE_TTL_DAYS = int(os.environ.get('CACHE_TTL_DAYS', '7'))
MAX_TEXT_LENGTH = int(os.environ.get('MAX_TEXT_LENGTH', '3000'))

# Voice mappings for Amazon Polly
POLLY_VOICES = {
    'en': {'voiceId': 'Aditi', 'engine': 'neural', 'languageCode': 'en-IN'},
    'en-IN': {'voiceId': 'Aditi', 'engine': 'neural', 'languageCode': 'en-IN'},
    'en-US': {'voiceId': 'Joanna', 'engine': 'neural', 'languageCode': 'en-US'},
    'hi': {'voiceId': 'Aditi', 'engine': 'neural', 'languageCode': 'hi-IN'},
    'hi-IN': {'voiceId': 'Aditi', 'engine': 'neural', 'languageCode': 'hi-IN'},
}

# Bhashini supported languages for TTS
BHASHINI_TTS_LANGUAGES = {
    'ta': 'ta',  # Tamil
    'te': 'te',  # Telugu
    'bn': 'bn',  # Bengali
    'mr': 'mr',  # Marathi
    'gu': 'gu',  # Gujarati
    'kn': 'kn',  # Kannada
    'ml': 'ml',  # Malayalam
    'pa': 'pa',  # Punjabi
    'or': 'or',  # Odia
    'as': 'as',  # Assamese
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for text-to-speech processing
    
    Expected request body:
    {
        "text": "Text to convert to speech",
        "language": "hi" or "en" or "ta" etc.,
        "userId": "user_id",
        "sessionId": "session_id",
        "speed": 1.0 (optional, 0.5 to 2.0)
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "audioUrl": "https://...",
            "audioId": "tts_id",
            "language": "hi",
            "cacheHit": true,
            "duration": 5.2,
            "format": "mp3",
            "expiresIn": 604800,
            "processingMethod": "polly" or "bhashini"
        }
    }
    """
    start_time = time.time()
    
    try:
        log_event('text_to_speech_invoked', {
            'requestId': context.request_id if context and hasattr(context, 'request_id') else 'local'
        })
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['text', 'language'])
        if validation_error:
            return build_error_response(
                error_message=validation_error,
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        text = body['text']
        language = body['language']
        user_id = body.get('userId', 'anonymous')
        session_id = body.get('sessionId', 'unknown')
        speed = body.get('speed', 1.0)
        
        # Validate text length
        if len(text) > MAX_TEXT_LENGTH:
            return build_error_response(
                error_message=f"Text too long. Maximum length: {MAX_TEXT_LENGTH} characters",
                error_code='TEXT_TOO_LONG',
                status_code=400
            )
        
        # Validate speed
        if not (0.5 <= speed <= 2.0):
            return build_error_response(
                error_message="Speed must be between 0.5 and 2.0",
                error_code='INVALID_SPEED',
                status_code=400
            )
        
        # Normalize language
        language = normalize_language(language)
        
        # Generate cache key
        cache_key = generate_tts_cache_key(text, language, speed)
        cache_s3_key = f"cache/{cache_key}.mp3"
        
        # Check cache
        cache_hit = check_cache_exists(TTS_CACHE_BUCKET, cache_s3_key)
        
        if cache_hit:
            log_event('tts_cache_hit', {
                'cacheKey': cache_key,
                'language': language
            })
            
            audio_url = get_audio_url(cache_s3_key)
            
            processing_time = time.time() - start_time
            
            return build_success_response(
                data={
                    'audioUrl': audio_url,
                    'audioId': cache_key,
                    'language': language,
                    'cacheHit': True,
                    'format': 'mp3',
                    'expiresIn': CACHE_TTL_DAYS * 86400,
                    'processingTime': round(processing_time, 2),
                    'processingMethod': 'cache'
                },
                status_code=200
            )
        
        # Cache miss - generate audio
        log_event('tts_cache_miss', {
            'cacheKey': cache_key,
            'language': language
        })
        
        audio_bytes, method = synthesize_with_fallback(text, language, speed)
        
        if not audio_bytes:
            return build_error_response(
                error_message="Failed to synthesize speech. Please try again.",
                error_code='SYNTHESIS_FAILED',
                status_code=500,
                retryable=True
            )
        
        # Store in cache
        s3_client = get_s3_client()
        try:
            s3_client.put_object(
                Bucket=TTS_CACHE_BUCKET,
                Key=cache_s3_key,
                Body=audio_bytes,
                ContentType='audio/mpeg',
                Metadata={
                    'language': language,
                    'textHash': cache_key,
                    'method': method,
                    'createdAt': get_current_timestamp()
                }
            )
            
            log_event('tts_cached', {
                'cacheKey': cache_key,
                'sizeBytes': len(audio_bytes),
                'method': method
            })
            
        except ClientError as e:
            log_event('tts_cache_store_failed', {
                'error': str(e),
                'cacheKey': cache_key
            })
            # Continue even if caching fails
        
        # Get audio URL
        audio_url = get_audio_url(cache_s3_key)
        
        processing_time = time.time() - start_time
        
        log_event('tts_completed', {
            'cacheKey': cache_key,
            'method': method,
            'processingTime': processing_time,
            'audioSize': len(audio_bytes)
        })
        
        return build_success_response(
            data={
                'audioUrl': audio_url,
                'audioId': cache_key,
                'language': language,
                'cacheHit': False,
                'format': 'mp3',
                'expiresIn': CACHE_TTL_DAYS * 86400,
                'processingTime': round(processing_time, 2),
                'processingMethod': method,
                'sizeBytes': len(audio_bytes)
            },
            status_code=200,
            metadata={
                'userId': user_id,
                'sessionId': session_id
            }
        )
        
    except Exception as e:
        log_event('text_to_speech_error', {
            'error': str(e),
            'errorType': type(e).__name__
        })
        return build_error_response(
            error_message="Internal server error during speech synthesis",
            error_code='INTERNAL_ERROR',
            status_code=500
        )


def synthesize_with_fallback(text: str, language: str, speed: float) -> Tuple[Optional[bytes], str]:
    """
    Synthesize speech with fallback: Polly → Bhashini → Error
    
    Args:
        text: Text to synthesize
        language: Language code
        speed: Speech speed (0.5 to 2.0)
    
    Returns:
        Tuple of (audio_bytes, method)
    """
    # Try Amazon Polly first for English and Hindi
    if language in POLLY_VOICES:
        audio_bytes = synthesize_with_polly(text, language, speed)
        if audio_bytes:
            return audio_bytes, 'polly'
        
        log_event('polly_synthesis_failed', {
            'language': language,
            'textLength': len(text)
        })
    
    # Try Bhashini for regional languages or as fallback
    if ENABLE_BHASHINI and language in BHASHINI_TTS_LANGUAGES:
        audio_bytes = synthesize_with_bhashini(text, language)
        if audio_bytes:
            return audio_bytes, 'bhashini'
        
        log_event('bhashini_synthesis_failed', {
            'language': language,
            'textLength': len(text)
        })
    
    # All methods failed
    return None, 'none'


def synthesize_with_polly(text: str, language: str, speed: float) -> Optional[bytes]:
    """
    Synthesize speech using Amazon Polly
    
    Args:
        text: Text to synthesize
        language: Language code
        speed: Speech speed
    
    Returns:
        Audio bytes or None
    """
    try:
        polly_client = get_polly_client()
        
        voice_config = POLLY_VOICES.get(language, POLLY_VOICES['en'])
        
        # Convert speed to Polly prosody rate
        # Speed 1.0 = 100%, 0.5 = 50%, 2.0 = 200%
        rate_percent = int(speed * 100)
        
        # Wrap text in SSML for speed control
        ssml_text = f'<speak><prosody rate="{rate_percent}%">{text}</prosody></speak>'
        
        response = polly_client.synthesize_speech(
            Text=ssml_text,
            TextType='ssml',
            OutputFormat='mp3',
            VoiceId=voice_config['voiceId'],
            Engine=voice_config['engine'],
            LanguageCode=voice_config['languageCode']
        )
        
        audio_stream = response['AudioStream'].read()
        
        log_event('polly_synthesis_success', {
            'language': language,
            'voiceId': voice_config['voiceId'],
            'audioSize': len(audio_stream)
        })
        
        return audio_stream
        
    except ClientError as e:
        log_event('polly_client_error', {
            'error': str(e),
            'language': language
        })
        return None
    except Exception as e:
        log_event('polly_unexpected_error', {
            'error': str(e),
            'errorType': type(e).__name__,
            'language': language
        })
        return None


def synthesize_with_bhashini(text: str, language: str) -> Optional[bytes]:
    """
    Synthesize speech using Bhashini TTS API
    
    Args:
        text: Text to synthesize
        language: Language code
    
    Returns:
        Audio bytes or None
    """
    try:
        if not BHASHINI_API_KEY:
            log_event('bhashini_api_key_missing', {'language': language})
            return None
        
        # Map language to Bhashini language code
        bhashini_lang = BHASHINI_TTS_LANGUAGES.get(language, language)
        
        # Prepare Bhashini API request
        headers = {
            'Authorization': f'Bearer {BHASHINI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Bhashini pipeline configuration request
        config_payload = {
            'pipelineTasks': [
                {
                    'taskType': 'tts',
                    'config': {
                        'language': {
                            'sourceLanguage': bhashini_lang
                        }
                    }
                }
            ]
        }
        
        # Get pipeline configuration
        config_response = requests.post(
            f"{BHASHINI_API_URL}/services/inference/pipeline",
            headers=headers,
            json=config_payload,
            timeout=10
        )
        
        if config_response.status_code != 200:
            log_event('bhashini_tts_config_failed', {
                'statusCode': config_response.status_code,
                'language': language
            })
            return None
        
        config_data = config_response.json()
        
        # Extract TTS service endpoint
        tts_service = None
        for task in config_data.get('pipelineResponseConfig', []):
            if task.get('taskType') == 'tts':
                tts_service = task.get('config', {})
                break
        
        if not tts_service:
            log_event('bhashini_tts_service_not_found', {'language': language})
            return None
        
        # Call TTS service
        # Note: Actual implementation depends on Bhashini API specification
        # This is a placeholder implementation
        
        log_event('bhashini_tts_not_implemented', {
            'language': bhashini_lang,
            'note': 'Bhashini TTS integration requires valid API credentials'
        })
        
        return None
        
    except requests.RequestException as e:
        log_event('bhashini_tts_request_error', {
            'error': str(e),
            'language': language
        })
        return None
    except Exception as e:
        log_event('bhashini_tts_unexpected_error', {
            'error': str(e),
            'errorType': type(e).__name__,
            'language': language
        })
        return None


def generate_tts_cache_key(text: str, language: str, speed: float) -> str:
    """
    Generate cache key based on text hash, language, and speed
    
    Args:
        text: Text content
        language: Language code
        speed: Speech speed
    
    Returns:
        Cache key string
    """
    # Create content string
    content = f"{text}|{language}|{speed}"
    
    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    cache_key = hash_obj.hexdigest()
    
    return cache_key


def normalize_language(language: str) -> str:
    """
    Normalize language code
    
    Args:
        language: Language code
    
    Returns:
        Normalized language code
    """
    lang = language.strip()
    
    # Keep full language codes for Polly (en-IN, hi-IN, en-US) - case insensitive check
    lang_lower = lang.lower()
    for polly_lang in POLLY_VOICES.keys():
        if lang_lower == polly_lang.lower():
            return polly_lang  # Return the exact Polly voice key
    
    # Remove country code for other languages
    if '-' in lang:
        base_lang = lang.split('-')[0].lower()
        return base_lang
    
    return lang.lower()


def get_audio_url(s3_key: str) -> str:
    """
    Get audio URL (CloudFront or S3 presigned)
    
    Args:
        s3_key: S3 object key
    
    Returns:
        Audio URL
    """
    # Use CloudFront if configured
    if CLOUDFRONT_DOMAIN:
        return f"https://{CLOUDFRONT_DOMAIN}/{s3_key}"
    
    # Otherwise use S3 presigned URL (7 days expiration)
    expiration = CACHE_TTL_DAYS * 86400
    return generate_presigned_url(TTS_CACHE_BUCKET, s3_key, expiration)

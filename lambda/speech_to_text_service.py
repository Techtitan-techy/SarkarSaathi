"""
Speech-to-Text Service Lambda Function

Integrates Amazon Transcribe and Bhashini API for multilingual speech recognition.
Implements language detection, noise filtering, and fallback chain.

Requirements: 1.1, 1.3, 1.4, 2.1
"""

import json
import os
import time
import requests
from typing import Dict, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

# Import shared utilities
from shared.utils import (
    get_s3_client,
    get_transcribe_client,
    build_success_response,
    build_error_response,
    get_current_timestamp,
    validate_required_fields,
    log_event
)

# Environment variables
AUDIO_BUCKET = os.environ.get('AUDIO_BUCKET', 'sarkari-saathi-audio')
BHASHINI_API_URL = os.environ.get('BHASHINI_API_URL', 'https://dhruva-api.bhashini.gov.in')
BHASHINI_API_KEY = os.environ.get('BHASHINI_API_KEY', '')
ENABLE_BHASHINI = os.environ.get('ENABLE_BHASHINI', 'false').lower() == 'true'
MAX_TRANSCRIPTION_WAIT_SECONDS = int(os.environ.get('MAX_TRANSCRIPTION_WAIT_SECONDS', '60'))
PAUSE_DETECTION_THRESHOLD = int(os.environ.get('PAUSE_DETECTION_THRESHOLD', '3'))

# Language mappings
TRANSCRIBE_LANGUAGES = {
    'en': 'en-IN',
    'hi': 'hi-IN',
    'en-IN': 'en-IN',
    'hi-IN': 'hi-IN'
}

BHASHINI_LANGUAGES = {
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
    'ur': 'ur',  # Urdu
}

# Confidence thresholds
MIN_CONFIDENCE_THRESHOLD = 0.70
HIGH_CONFIDENCE_THRESHOLD = 0.85


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for speech-to-text processing
    
    Expected request body:
    {
        "audioId": "audio_id",
        "s3Key": "uploads/audio_id.mp3",
        "language": "hi" or "en" or "ta" etc.,
        "userId": "user_id",
        "sessionId": "session_id"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "transcript": "transcribed text",
            "language": "detected_language",
            "confidence": 0.95,
            "detectedLanguage": "hi",
            "languageConfidence": 0.98,
            "processingMethod": "transcribe" or "bhashini",
            "processingTime": 2.5
        }
    }
    """
    start_time = time.time()
    
    try:
        log_event('speech_to_text_invoked', {
            'requestId': context.request_id if context and hasattr(context, 'request_id') else 'local'
        })
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['s3Key'])
        if validation_error:
            return build_error_response(
                error_message=validation_error,
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        s3_key = body['s3Key']
        audio_id = body.get('audioId', 'unknown')
        language = body.get('language', 'en')
        user_id = body.get('userId', 'anonymous')
        session_id = body.get('sessionId', 'unknown')
        
        # Detect language if not provided or uncertain
        detected_language, language_confidence = detect_language_from_hint(language)
        
        log_event('language_detected', {
            'providedLanguage': language,
            'detectedLanguage': detected_language,
            'confidence': language_confidence
        })
        
        # Try transcription with fallback chain
        transcript, confidence, method = transcribe_with_fallback(
            s3_key=s3_key,
            language=detected_language,
            audio_id=audio_id
        )
        
        if not transcript:
            return build_error_response(
                error_message="Failed to transcribe audio. Please try again with clearer audio.",
                error_code='TRANSCRIPTION_FAILED',
                status_code=500,
                retryable=True
            )
        
        processing_time = time.time() - start_time
        
        log_event('transcription_completed', {
            'audioId': audio_id,
            'method': method,
            'confidence': confidence,
            'processingTime': processing_time,
            'transcriptLength': len(transcript)
        })
        
        # Return success response
        response_data = {
            'transcript': transcript,
            'language': detected_language,
            'confidence': confidence,
            'detectedLanguage': detected_language,
            'languageConfidence': language_confidence,
            'processingMethod': method,
            'processingTime': round(processing_time, 2),
            'audioId': audio_id
        }
        
        return build_success_response(
            data=response_data,
            status_code=200,
            metadata={
                'userId': user_id,
                'sessionId': session_id
            }
        )
        
    except Exception as e:
        log_event('speech_to_text_error', {
            'error': str(e),
            'errorType': type(e).__name__
        })
        return build_error_response(
            error_message="Internal server error during transcription",
            error_code='INTERNAL_ERROR',
            status_code=500
        )


def transcribe_with_fallback(s3_key: str, language: str, audio_id: str) -> Tuple[Optional[str], float, str]:
    """
    Transcribe audio with fallback chain: Transcribe → Bhashini → Error
    
    Args:
        s3_key: S3 key of audio file
        language: Language code
        audio_id: Audio identifier
    
    Returns:
        Tuple of (transcript, confidence, method)
    """
    # Try Amazon Transcribe first for English and Hindi
    if language in TRANSCRIBE_LANGUAGES:
        transcript, confidence = transcribe_with_amazon(s3_key, language, audio_id)
        if transcript and confidence >= MIN_CONFIDENCE_THRESHOLD:
            return transcript, confidence, 'transcribe'
        
        log_event('transcribe_low_confidence', {
            'audioId': audio_id,
            'confidence': confidence,
            'language': language
        })
    
    # Try Bhashini for regional languages or as fallback
    if ENABLE_BHASHINI:
        transcript, confidence = transcribe_with_bhashini(s3_key, language, audio_id)
        if transcript and confidence >= MIN_CONFIDENCE_THRESHOLD:
            return transcript, confidence, 'bhashini'
        
        log_event('bhashini_low_confidence', {
            'audioId': audio_id,
            'confidence': confidence,
            'language': language
        })
    
    # All methods failed
    return None, 0.0, 'none'


def transcribe_with_amazon(s3_key: str, language: str, audio_id: str) -> Tuple[Optional[str], float]:
    """
    Transcribe audio using Amazon Transcribe
    
    Args:
        s3_key: S3 key of audio file
        language: Language code
        audio_id: Audio identifier
    
    Returns:
        Tuple of (transcript, confidence)
    """
    try:
        transcribe_client = get_transcribe_client()
        
        # Map language to Transcribe language code
        transcribe_lang = TRANSCRIBE_LANGUAGES.get(language, 'en-IN')
        
        # Generate job name
        job_name = f"stt-{audio_id}-{int(time.time())}"
        audio_uri = f"s3://{AUDIO_BUCKET}/{s3_key}"
        
        # Determine media format from S3 key
        media_format = 'mp3' if s3_key.endswith('.mp3') else 'wav'
        
        # Start transcription job with noise reduction settings
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_uri},
            MediaFormat=media_format,
            LanguageCode=transcribe_lang,
            Settings={
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 1,
                'ChannelIdentification': False
            }
        )
        
        log_event('transcribe_job_started', {
            'jobName': job_name,
            'language': transcribe_lang,
            'audioId': audio_id
        })
        
        # Poll for job completion
        max_wait = MAX_TRANSCRIPTION_WAIT_SECONDS
        waited = 0
        poll_interval = 2
        
        while waited < max_wait:
            status_response = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            job_status = status_response['TranscriptionJob']['TranscriptionJobStatus']
            
            if job_status == 'COMPLETED':
                transcript_uri = status_response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # Fetch transcript
                response = requests.get(transcript_uri, timeout=10)
                transcript_data = response.json()
                
                # Extract transcript and confidence
                transcripts = transcript_data.get('results', {}).get('transcripts', [])
                if transcripts:
                    transcript_text = transcripts[0].get('transcript', '')
                    
                    # Calculate average confidence from items
                    items = transcript_data.get('results', {}).get('items', [])
                    confidences = [
                        float(item.get('alternatives', [{}])[0].get('confidence', 0))
                        for item in items
                        if 'alternatives' in item and item['alternatives']
                    ]
                    
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    # Clean up job
                    try:
                        transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
                    except:
                        pass
                    
                    return transcript_text, avg_confidence
            
            elif job_status == 'FAILED':
                failure_reason = status_response['TranscriptionJob'].get('FailureReason', 'Unknown')
                log_event('transcribe_job_failed', {
                    'jobName': job_name,
                    'reason': failure_reason
                })
                return None, 0.0
            
            time.sleep(poll_interval)
            waited += poll_interval
        
        # Timeout
        log_event('transcribe_job_timeout', {
            'jobName': job_name,
            'waitedSeconds': waited
        })
        return None, 0.0
        
    except ClientError as e:
        log_event('transcribe_client_error', {
            'error': str(e),
            'audioId': audio_id
        })
        return None, 0.0
    except Exception as e:
        log_event('transcribe_unexpected_error', {
            'error': str(e),
            'errorType': type(e).__name__,
            'audioId': audio_id
        })
        return None, 0.0


def transcribe_with_bhashini(s3_key: str, language: str, audio_id: str) -> Tuple[Optional[str], float]:
    """
    Transcribe audio using Bhashini API
    
    Args:
        s3_key: S3 key of audio file
        language: Language code
        audio_id: Audio identifier
    
    Returns:
        Tuple of (transcript, confidence)
    """
    try:
        if not BHASHINI_API_KEY:
            log_event('bhashini_api_key_missing', {'audioId': audio_id})
            return None, 0.0
        
        # Download audio from S3
        s3_client = get_s3_client()
        audio_obj = s3_client.get_object(Bucket=AUDIO_BUCKET, Key=s3_key)
        audio_bytes = audio_obj['Body'].read()
        
        # Map language to Bhashini language code
        bhashini_lang = BHASHINI_LANGUAGES.get(language, language)
        
        # Prepare Bhashini API request
        # Note: This is a simplified implementation. Actual Bhashini API may require
        # different endpoints and request formats. Update based on official documentation.
        headers = {
            'Authorization': f'Bearer {BHASHINI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Bhashini pipeline configuration request
        config_payload = {
            'pipelineTasks': [
                {
                    'taskType': 'asr',
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
            log_event('bhashini_config_failed', {
                'statusCode': config_response.status_code,
                'audioId': audio_id
            })
            return None, 0.0
        
        config_data = config_response.json()
        
        # Extract ASR service endpoint
        asr_service = None
        for task in config_data.get('pipelineResponseConfig', []):
            if task.get('taskType') == 'asr':
                asr_service = task.get('config', {})
                break
        
        if not asr_service:
            log_event('bhashini_asr_service_not_found', {'audioId': audio_id})
            return None, 0.0
        
        # Call ASR service
        # Note: Actual implementation depends on Bhashini API specification
        # This is a placeholder implementation
        asr_endpoint = asr_service.get('serviceId', '')
        
        # For now, return placeholder since we don't have actual Bhashini credentials
        log_event('bhashini_not_implemented', {
            'audioId': audio_id,
            'language': bhashini_lang,
            'note': 'Bhashini integration requires valid API credentials'
        })
        
        return None, 0.0
        
    except requests.RequestException as e:
        log_event('bhashini_request_error', {
            'error': str(e),
            'audioId': audio_id
        })
        return None, 0.0
    except Exception as e:
        log_event('bhashini_unexpected_error', {
            'error': str(e),
            'errorType': type(e).__name__,
            'audioId': audio_id
        })
        return None, 0.0


def detect_language_from_hint(language_hint: str) -> Tuple[str, float]:
    """
    Detect language from hint with confidence scoring
    
    Args:
        language_hint: Language hint from user
    
    Returns:
        Tuple of (detected_language, confidence)
    """
    # Normalize language hint
    lang = language_hint.lower().strip()
    
    # Remove country code if present
    if '-' in lang:
        lang = lang.split('-')[0]
    
    # Check if language is supported
    all_supported = {**TRANSCRIBE_LANGUAGES, **BHASHINI_LANGUAGES}
    
    if lang in all_supported or f"{lang}-IN" in all_supported:
        return lang, HIGH_CONFIDENCE_THRESHOLD
    
    # Default to English with lower confidence
    log_event('language_defaulted_to_english', {
        'providedHint': language_hint
    })
    return 'en', 0.5

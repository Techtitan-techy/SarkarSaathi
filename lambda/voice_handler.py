"""
Voice Processing Lambda Handler
Handles voice input, transcription, and text-to-speech
"""
import json
import boto3
import base64
import os
from datetime import datetime
from shared.utils import (
    create_response,
    get_s3_client,
    get_transcribe_client,
    generate_id,
    log_info,
    log_error
)

# Initialize AWS clients
s3_client = get_s3_client()
transcribe_client = get_transcribe_client()
polly_client = boto3.client('polly')

# Environment variables
AUDIO_BUCKET = os.environ.get('AUDIO_BUCKET', 'sarkari-saathi-audio')
REGION = os.environ.get('AWS_REGION', 'ap-south-1')


def lambda_handler(event, context):
    """
    Main handler for voice processing
    
    Endpoints:
    - POST /voice/upload - Upload audio file
    - POST /voice/transcribe - Transcribe audio to text
    - POST /voice/synthesize - Convert text to speech
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        log_info(f"Voice handler called: {http_method} {path}")
        
        if http_method == 'POST':
            if path.endswith('/upload'):
                return handle_audio_upload(event)
            elif path.endswith('/transcribe'):
                return handle_transcription(event)
            elif path.endswith('/synthesize'):
                return handle_synthesis(event)
        
        return create_response(400, {'error': 'Invalid endpoint'})
        
    except Exception as e:
        log_error(f"Voice handler error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def handle_audio_upload(event):
    """Upload audio file to S3"""
    try:
        body = json.loads(event.get('body', '{}'))
        audio_data = body.get('audio')
        language = body.get('language', 'en-IN')
        
        if not audio_data:
            return create_response(400, {'error': 'No audio data provided'})
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        
        # Generate unique filename
        audio_id = generate_id('audio')
        filename = f"uploads/{audio_id}.wav"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=AUDIO_BUCKET,
            Key=filename,
            Body=audio_bytes,
            ContentType='audio/wav'
        )
        
        log_info(f"Audio uploaded: {filename}")
        
        return create_response(200, {
            'audioId': audio_id,
            'filename': filename,
            'language': language
        })
        
    except Exception as e:
        log_error(f"Audio upload error: {str(e)}")
        return create_response(500, {'error': 'Failed to upload audio'})


def handle_transcription(event):
    """Transcribe audio to text using Amazon Transcribe"""
    try:
        body = json.loads(event.get('body', '{}'))
        audio_id = body.get('audioId')
        language = body.get('language', 'en-IN')
        
        if not audio_id:
            return create_response(400, {'error': 'No audio ID provided'})
        
        filename = f"uploads/{audio_id}.wav"
        audio_uri = f"s3://{AUDIO_BUCKET}/{filename}"
        
        # Start transcription job
        job_name = f"transcribe-{audio_id}"
        
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': audio_uri},
            MediaFormat='wav',
            LanguageCode=language
        )
        
        # Wait for job to complete (simplified for demo)
        # In production, use Step Functions or polling
        import time
        max_wait = 30
        waited = 0
        
        while waited < max_wait:
            status = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            
            if job_status == 'COMPLETED':
                transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # Get transcript text
                import requests
                response = requests.get(transcript_uri)
                transcript_data = response.json()
                
                transcript_text = transcript_data['results']['transcripts'][0]['transcript']
                
                log_info(f"Transcription completed: {transcript_text}")
                
                return create_response(200, {
                    'transcript': transcript_text,
                    'language': language,
                    'confidence': 0.95  # Simplified
                })
            
            elif job_status == 'FAILED':
                return create_response(500, {'error': 'Transcription failed'})
            
            time.sleep(2)
            waited += 2
        
        return create_response(202, {
            'status': 'processing',
            'jobName': job_name
        })
        
    except Exception as e:
        log_error(f"Transcription error: {str(e)}")
        return create_response(500, {'error': 'Failed to transcribe audio'})


def handle_synthesis(event):
    """Convert text to speech using Amazon Polly"""
    try:
        body = json.loads(event.get('body', '{}'))
        text = body.get('text')
        language = body.get('language', 'en-IN')
        
        if not text:
            return create_response(400, {'error': 'No text provided'})
        
        # Map language to Polly voice
        voice_map = {
            'en-IN': 'Aditi',
            'hi-IN': 'Aditi',
            'en-US': 'Joanna',
        }
        
        voice_id = voice_map.get(language, 'Aditi')
        
        # Synthesize speech
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural'
        )
        
        # Save audio to S3
        audio_id = generate_id('tts')
        filename = f"tts/{audio_id}.mp3"
        
        audio_stream = response['AudioStream'].read()
        
        s3_client.put_object(
            Bucket=AUDIO_BUCKET,
            Key=filename,
            Body=audio_stream,
            ContentType='audio/mpeg'
        )
        
        # Generate presigned URL
        audio_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AUDIO_BUCKET, 'Key': filename},
            ExpiresIn=3600
        )
        
        log_info(f"TTS generated: {filename}")
        
        return create_response(200, {
            'audioUrl': audio_url,
            'audioId': audio_id,
            'language': language
        })
        
    except Exception as e:
        log_error(f"TTS error: {str(e)}")
        return create_response(500, {'error': 'Failed to synthesize speech'})

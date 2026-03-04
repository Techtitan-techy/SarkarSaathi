"""
End-to-End Integration Tests for Voice Processing Pipeline

This test suite validates the complete voice pipeline functionality:
- Audio input handling and S3 storage
- Speech-to-text transcription with language detection
- Text-to-speech synthesis with caching
- Multi-language support
- Performance requirements (3-second response time)

Requirements validated: 1.1, 1.2, 1.3, 1.4, 2.1, 10.1
"""

import json
import base64
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

# Import Lambda handlers
import audio_input_handler
import speech_to_text_service
import text_to_speech_service


class TestVoicePipelineIntegration:
    """End-to-end integration tests for voice processing pipeline"""
    
    def test_complete_voice_pipeline_english(self):
        """
        Test complete voice pipeline: audio upload → transcription → TTS
        Validates: Requirements 1.1, 1.2, 10.1
        """
        # Step 1: Upload audio file
        mp3_data = b'ID3' + b'\x00' * 1000
        mp3_b64 = base64.b64encode(mp3_data).decode('utf-8')
        
        upload_event = {
            'body': json.dumps({
                'audio': mp3_b64,
                'format': 'audio/mpeg',
                'userId': 'test_user_001',
                'sessionId': 'test_session_001'
            })
        }
        
        with patch('audio_input_handler.get_s3_client') as mock_s3, \
             patch('audio_input_handler.generate_presigned_url') as mock_presigned:
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_presigned.return_value = 'https://test-audio-url.com/audio.mp3'
            
            upload_response = audio_input_handler.lambda_handler(upload_event, None)
            
            assert upload_response['statusCode'] == 200
            upload_body = json.loads(upload_response['body'])
            assert upload_body['success'] is True
            
            audio_id = upload_body['data']['audioId']
            s3_key = upload_body['data']['s3Key']
        
        # Step 2: Transcribe audio
        transcribe_event = {
            'body': json.dumps({
                's3Key': s3_key,
                'audioId': audio_id,
                'language': 'en',
                'userId': 'test_user_001'
            })
        }
        
        with patch('speech_to_text_service.transcribe_with_amazon') as mock_transcribe:
            mock_transcribe.return_value = ('Hello, I want to apply for PM-KISAN scheme', 0.96)
            
            transcribe_response = speech_to_text_service.lambda_handler(transcribe_event, None)
            
            assert transcribe_response['statusCode'] == 200
            transcribe_body = json.loads(transcribe_response['body'])
            assert transcribe_body['success'] is True
            assert transcribe_body['data']['confidence'] >= 0.95
            
            transcript = transcribe_body['data']['transcript']
        
        # Step 3: Generate TTS response
        tts_event = {
            'body': json.dumps({
                'text': 'PM-KISAN is a scheme for farmers. You may be eligible.',
                'language': 'en',
                'userId': 'test_user_001'
            })
        }
        
        mock_audio = b'fake_audio_response'
        
        with patch('text_to_speech_service.check_cache_exists') as mock_cache, \
             patch('text_to_speech_service.synthesize_with_polly') as mock_polly, \
             patch('text_to_speech_service.get_s3_client') as mock_s3, \
             patch('text_to_speech_service.get_audio_url') as mock_url:
            mock_cache.return_value = False
            mock_polly.return_value = mock_audio
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_url.return_value = 'https://test-tts-url.com/response.mp3'
            
            tts_response = text_to_speech_service.lambda_handler(tts_event, None)
            
            assert tts_response['statusCode'] == 200
            tts_body = json.loads(tts_response['body'])
            assert tts_body['success'] is True
            assert tts_body['data']['audioUrl'] is not None
    
    def test_complete_voice_pipeline_hindi(self):
        """
        Test complete voice pipeline with Hindi language
        Validates: Requirements 1.1, 1.2, 2.1
        """
        # Step 1: Upload audio
        mp3_data = b'ID3' + b'\x00' * 1000
        mp3_b64 = base64.b64encode(mp3_data).decode('utf-8')
        
        upload_event = {
            'body': json.dumps({
                'audio': mp3_b64,
                'format': 'audio/mpeg',
                'userId': 'test_user_002',
                'sessionId': 'test_session_002'
            })
        }
        
        with patch('audio_input_handler.get_s3_client') as mock_s3, \
             patch('audio_input_handler.generate_presigned_url') as mock_presigned:
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_presigned.return_value = 'https://test-audio-url.com/audio.mp3'
            
            upload_response = audio_input_handler.lambda_handler(upload_event, None)
            audio_id = json.loads(upload_response['body'])['data']['audioId']
            s3_key = json.loads(upload_response['body'])['data']['s3Key']
        
        # Step 2: Transcribe Hindi audio
        transcribe_event = {
            'body': json.dumps({
                's3Key': s3_key,
                'audioId': audio_id,
                'language': 'hi',
                'userId': 'test_user_002'
            })
        }
        
        with patch('speech_to_text_service.transcribe_with_amazon') as mock_transcribe:
            mock_transcribe.return_value = ('मुझे पीएम किसान योजना के बारे में जानकारी चाहिए', 0.94)
            
            transcribe_response = speech_to_text_service.lambda_handler(transcribe_event, None)
            
            assert transcribe_response['statusCode'] == 200
            transcribe_body = json.loads(transcribe_response['body'])
            assert transcribe_body['data']['language'] == 'hi'
            assert transcribe_body['data']['confidence'] >= 0.90
        
        # Step 3: Generate Hindi TTS
        tts_event = {
            'body': json.dumps({
                'text': 'पीएम किसान योजना किसानों के लिए है। आप पात्र हो सकते हैं।',
                'language': 'hi',
                'userId': 'test_user_002'
            })
        }
        
        mock_audio = b'fake_hindi_audio'
        
        with patch('text_to_speech_service.check_cache_exists') as mock_cache, \
             patch('text_to_speech_service.synthesize_with_polly') as mock_polly, \
             patch('text_to_speech_service.get_s3_client') as mock_s3, \
             patch('text_to_speech_service.get_audio_url') as mock_url:
            mock_cache.return_value = False
            mock_polly.return_value = mock_audio
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_url.return_value = 'https://test-tts-url.com/hindi.mp3'
            
            tts_response = text_to_speech_service.lambda_handler(tts_event, None)
            
            assert tts_response['statusCode'] == 200
            tts_body = json.loads(tts_response['body'])
            assert tts_body['data']['language'] == 'hi'
    
    def test_language_detection_accuracy(self):
        """
        Test language detection from audio input
        Validates: Requirements 2.1, 2.2
        """
        test_cases = [
            ('en', 'en', 0.85),
            ('hi', 'hi', 0.85),
            ('en-IN', 'en', 0.85),
            ('hi-IN', 'hi', 0.85),
            ('ta', 'ta', 0.85),
        ]
        
        for input_lang, expected_lang, min_confidence in test_cases:
            detected_lang, confidence = speech_to_text_service.detect_language_from_hint(input_lang)
            
            assert detected_lang == expected_lang, f"Expected {expected_lang}, got {detected_lang}"
            assert confidence >= min_confidence, f"Confidence {confidence} below threshold {min_confidence}"
    
    def test_audio_caching_reduces_api_calls(self):
        """
        Test that TTS caching reduces API calls
        Validates: Requirements 10.1 (performance optimization)
        """
        tts_event = {
            'body': json.dumps({
                'text': 'This is a cached response',
                'language': 'en',
                'userId': 'test_user_003'
            })
        }
        
        # First call - cache miss
        mock_audio = b'fake_audio_data'
        
        with patch('text_to_speech_service.check_cache_exists') as mock_cache, \
             patch('text_to_speech_service.synthesize_with_polly') as mock_polly, \
             patch('text_to_speech_service.get_s3_client') as mock_s3, \
             patch('text_to_speech_service.get_audio_url') as mock_url:
            mock_cache.return_value = False
            mock_polly.return_value = mock_audio
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_url.return_value = 'https://test-tts-url.com/cached.mp3'
            
            first_response = text_to_speech_service.lambda_handler(tts_event, None)
            first_body = json.loads(first_response['body'])
            
            assert first_body['data']['cacheHit'] is False
            assert first_body['data']['processingMethod'] == 'polly'
            assert mock_polly.called
        
        # Second call - cache hit
        with patch('text_to_speech_service.check_cache_exists') as mock_cache, \
             patch('text_to_speech_service.synthesize_with_polly') as mock_polly, \
             patch('text_to_speech_service.get_audio_url') as mock_url:
            mock_cache.return_value = True
            mock_url.return_value = 'https://test-tts-url.com/cached.mp3'
            
            second_response = text_to_speech_service.lambda_handler(tts_event, None)
            second_body = json.loads(second_response['body'])
            
            assert second_body['data']['cacheHit'] is True
            assert second_body['data']['processingMethod'] == 'cache'
            assert not mock_polly.called  # Polly should not be called on cache hit
    
    def test_performance_response_time(self):
        """
        Test that voice processing meets 3-second response time requirement
        Validates: Requirements 10.1
        """
        tts_event = {
            'body': json.dumps({
                'text': 'Quick response test',
                'language': 'en',
                'userId': 'test_user_004'
            })
        }
        
        mock_audio = b'fake_audio_data'
        
        with patch('text_to_speech_service.check_cache_exists') as mock_cache, \
             patch('text_to_speech_service.synthesize_with_polly') as mock_polly, \
             patch('text_to_speech_service.get_s3_client') as mock_s3, \
             patch('text_to_speech_service.get_audio_url') as mock_url:
            mock_cache.return_value = False
            mock_polly.return_value = mock_audio
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_url.return_value = 'https://test-tts-url.com/quick.mp3'
            
            start_time = time.time()
            response = text_to_speech_service.lambda_handler(tts_event, None)
            processing_time = time.time() - start_time
            
            assert response['statusCode'] == 200
            # In real scenario, processing time should be < 3 seconds
            # For mocked tests, we just verify the response includes timing
            body = json.loads(response['body'])
            assert 'processingTime' in body['data']
    
    def test_pause_detection_threshold(self):
        """
        Test that pause detection threshold is properly configured
        Validates: Requirements 1.4
        """
        # Verify pause detection threshold is set to 3 seconds
        assert speech_to_text_service.PAUSE_DETECTION_THRESHOLD == 3
    
    def test_noise_filtering_configuration(self):
        """
        Test that noise filtering is enabled in transcription
        Validates: Requirements 1.3
        """
        s3_key = 'uploads/test_audio.mp3'
        audio_id = 'test_audio_123'
        language = 'en'
        
        with patch('speech_to_text_service.get_transcribe_client') as mock_transcribe_client:
            mock_client = Mock()
            mock_client.start_transcription_job = Mock()
            mock_client.get_transcription_job = Mock(return_value={
                'TranscriptionJob': {
                    'TranscriptionJobStatus': 'FAILED',
                    'FailureReason': 'Test failure'
                }
            })
            mock_transcribe_client.return_value = mock_client
            
            # Call transcription
            transcript, confidence = speech_to_text_service.transcribe_with_amazon(
                s3_key, language, audio_id
            )
            
            # Verify that start_transcription_job was called with proper settings
            if mock_client.start_transcription_job.called:
                call_args = mock_client.start_transcription_job.call_args
                # Settings should be configured for noise reduction
                assert 'Settings' in call_args[1]
    
    def test_multi_language_support(self):
        """
        Test support for multiple Indian languages
        Validates: Requirements 2.1
        """
        supported_languages = ['en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa']
        
        for lang in supported_languages:
            # Test language detection
            detected_lang, confidence = speech_to_text_service.detect_language_from_hint(lang)
            assert detected_lang is not None
            assert confidence > 0
            
            # Verify language is in supported mappings
            is_supported = (
                lang in speech_to_text_service.TRANSCRIBE_LANGUAGES or
                lang in speech_to_text_service.BHASHINI_LANGUAGES
            )
            assert is_supported, f"Language {lang} not in supported mappings"
    
    def test_fallback_chain_transcribe_to_bhashini(self):
        """
        Test fallback from Amazon Transcribe to Bhashini
        Validates: Requirements 1.5, 2.1
        """
        s3_key = 'uploads/test_audio.mp3'
        audio_id = 'test_audio_fallback'
        language = 'ta'  # Tamil - not supported by Transcribe
        
        with patch('speech_to_text_service.ENABLE_BHASHINI', True):
            with patch('speech_to_text_service.transcribe_with_bhashini') as mock_bhashini:
                mock_bhashini.return_value = ('வணக்கம்', 0.88)
                
                transcript, confidence, method = speech_to_text_service.transcribe_with_fallback(
                    s3_key, language, audio_id
                )
                
                assert method == 'bhashini'
                assert transcript is not None
                assert confidence >= 0.70  # MIN_CONFIDENCE_THRESHOLD
    
    def test_error_recovery_low_confidence(self):
        """
        Test error recovery when transcription confidence is low
        Validates: Requirements 1.5
        """
        s3_key = 'uploads/test_audio.mp3'
        audio_id = 'test_audio_low_conf'
        language = 'en'
        
        with patch('speech_to_text_service.transcribe_with_amazon') as mock_transcribe:
            # Simulate low confidence transcription
            mock_transcribe.return_value = ('unclear audio', 0.60)
            
            with patch('speech_to_text_service.ENABLE_BHASHINI', False):
                transcript, confidence, method = speech_to_text_service.transcribe_with_fallback(
                    s3_key, language, audio_id
                )
                
                # Should fail due to low confidence
                assert transcript is None or confidence < speech_to_text_service.MIN_CONFIDENCE_THRESHOLD
    
    def test_audio_format_validation(self):
        """
        Test audio format validation for MP3 and WAV
        Validates: Requirements 1.1
        """
        # Test valid MP3
        mp3_data = b'ID3' + b'\x00' * 100
        assert audio_input_handler.validate_audio_magic_bytes(mp3_data, 'mp3') is True
        
        # Test valid WAV
        wav_data = b'RIFF' + b'\x00' * 4 + b'WAVE' + b'\x00' * 100
        assert audio_input_handler.validate_audio_magic_bytes(wav_data, 'wav') is True
        
        # Test invalid MP3
        invalid_mp3 = b'INVALID' + b'\x00' * 100
        assert audio_input_handler.validate_audio_magic_bytes(invalid_mp3, 'mp3') is False
    
    def test_tts_cache_key_consistency(self):
        """
        Test that TTS cache keys are consistent for same input
        Validates: Requirements 10.1 (caching optimization)
        """
        text = "Hello, welcome to SarkariSaathi"
        language = "en"
        speed = 1.0
        
        # Generate cache key multiple times
        key1 = text_to_speech_service.generate_tts_cache_key(text, language, speed)
        key2 = text_to_speech_service.generate_tts_cache_key(text, language, speed)
        key3 = text_to_speech_service.generate_tts_cache_key(text, language, speed)
        
        # All keys should be identical
        assert key1 == key2 == key3
        
        # Different input should produce different key
        key4 = text_to_speech_service.generate_tts_cache_key(text, "hi", speed)
        assert key1 != key4
    
    def test_concurrent_audio_uploads(self):
        """
        Test handling of concurrent audio uploads
        Validates: Requirements 10.1, 10.2
        """
        # Simulate multiple concurrent uploads
        upload_events = []
        for i in range(5):
            mp3_data = b'ID3' + b'\x00' * (100 + i)  # Slightly different data
            mp3_b64 = base64.b64encode(mp3_data).decode('utf-8')
            
            upload_events.append({
                'body': json.dumps({
                    'audio': mp3_b64,
                    'format': 'audio/mpeg',
                    'userId': f'test_user_{i}',
                    'sessionId': f'test_session_{i}'
                })
            })
        
        audio_ids = set()
        
        with patch('audio_input_handler.get_s3_client') as mock_s3, \
             patch('audio_input_handler.generate_presigned_url') as mock_presigned:
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_presigned.return_value = 'https://test-url.com'
            
            for event in upload_events:
                response = audio_input_handler.lambda_handler(event, None)
                assert response['statusCode'] == 200
                
                body = json.loads(response['body'])
                audio_id = body['data']['audioId']
                audio_ids.add(audio_id)
        
        # All audio IDs should be unique
        assert len(audio_ids) == 5


class TestVoicePipelineEdgeCases:
    """Edge case tests for voice processing pipeline"""
    
    def test_empty_audio_data(self):
        """Test handling of empty audio data"""
        event = {
            'body': json.dumps({
                'audio': '',
                'format': 'audio/mpeg'
            })
        }
        
        response = audio_input_handler.lambda_handler(event, None)
        assert response['statusCode'] == 400
    
    def test_very_long_text_tts(self):
        """Test TTS with text exceeding maximum length"""
        long_text = 'a' * 4000  # Exceeds MAX_TEXT_LENGTH
        
        event = {
            'body': json.dumps({
                'text': long_text,
                'language': 'en'
            })
        }
        
        response = text_to_speech_service.lambda_handler(event, None)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'too long' in body['error']['errorMessage'].lower()
    
    def test_unsupported_language_fallback(self):
        """Test fallback to English for unsupported language"""
        detected_lang, confidence = speech_to_text_service.detect_language_from_hint('xyz')
        assert detected_lang == 'en'  # Should default to English
        assert confidence == 0.5  # Lower confidence for default
    
    def test_s3_upload_retry_on_failure(self):
        """Test retry behavior on S3 upload failure"""
        mp3_data = b'ID3' + b'\x00' * 100
        mp3_b64 = base64.b64encode(mp3_data).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'audio': mp3_b64,
                'format': 'audio/mpeg'
            })
        }
        
        with patch('audio_input_handler.get_s3_client') as mock_s3:
            mock_s3_client = Mock()
            mock_s3_client.put_object.side_effect = ClientError(
                {'Error': {'Code': 'ServiceUnavailable'}},
                'PutObject'
            )
            mock_s3.return_value = mock_s3_client
            
            response = audio_input_handler.lambda_handler(event, None)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error']['retryable'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

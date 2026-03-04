"""
Unit Tests for Voice Processing Pipeline

Tests for audio input handler, speech-to-text, and text-to-speech services.
"""

import json
import base64
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

# Import Lambda handlers
import audio_input_handler
import speech_to_text_service
import text_to_speech_service


class TestAudioInputHandler:
    """Tests for audio input handler Lambda function"""
    
    def test_valid_mp3_upload(self):
        """Test successful MP3 audio upload"""
        # Create mock MP3 data (ID3 tag)
        mp3_data = b'ID3' + b'\x00' * 100
        mp3_b64 = base64.b64encode(mp3_data).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'audio': mp3_b64,
                'format': 'audio/mpeg',
                'userId': 'test_user',
                'sessionId': 'test_session'
            })
        }
        
        context = None  # Use None instead of Mock to avoid JSON serialization issues
        
        with patch('audio_input_handler.get_s3_client') as mock_s3, \
             patch('audio_input_handler.generate_presigned_url') as mock_presigned:
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_presigned.return_value = 'https://test-url.com'
            
            response = audio_input_handler.lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert 'audioId' in body['data']
            assert 'presignedUrl' in body['data']
            assert body['data']['format'] == 'mp3'
    
    def test_valid_wav_upload(self):
        """Test successful WAV audio upload"""
        # Create mock WAV data (RIFF header)
        wav_data = b'RIFF' + b'\x00' * 4 + b'WAVE' + b'\x00' * 100
        wav_b64 = base64.b64encode(wav_data).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'audio': wav_b64,
                'format': 'audio/wav',
                'userId': 'test_user',
                'sessionId': 'test_session'
            })
        }
        
        context = None
        
        with patch('audio_input_handler.get_s3_client') as mock_s3, \
             patch('audio_input_handler.generate_presigned_url') as mock_presigned:
            mock_s3_client = Mock()
            mock_s3_client.put_object = Mock()
            mock_s3.return_value = mock_s3_client
            mock_presigned.return_value = 'https://test-url.com'
            
            response = audio_input_handler.lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert body['data']['format'] == 'wav'
    
    def test_missing_audio_field(self):
        """Test error when audio field is missing"""
        event = {
            'body': json.dumps({
                'format': 'audio/mpeg'
            })
        }
        
        context = None
        
        response = audio_input_handler.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'audio' in body['error']['errorMessage']
    
    def test_unsupported_format(self):
        """Test error for unsupported audio format"""
        mp3_data = b'ID3' + b'\x00' * 100
        mp3_b64 = base64.b64encode(mp3_data).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'audio': mp3_b64,
                'format': 'audio/ogg'  # Unsupported
            })
        }
        
        context = None
        
        response = audio_input_handler.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'Unsupported' in body['error']['errorMessage']
    
    def test_invalid_base64(self):
        """Test error for invalid base64 encoding"""
        event = {
            'body': json.dumps({
                'audio': 'not-valid-base64!!!',
                'format': 'audio/mpeg'
            })
        }
        
        context = None
        
        response = audio_input_handler.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'base64' in body['error']['errorMessage'].lower()
    
    def test_file_too_large(self):
        """Test error when audio file exceeds size limit"""
        # Create large audio data (11MB)
        large_data = b'ID3' + b'\x00' * (11 * 1024 * 1024)
        large_b64 = base64.b64encode(large_data).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'audio': large_b64,
                'format': 'audio/mpeg'
            })
        }
        
        context = None
        
        response = audio_input_handler.lambda_handler(event, context)
        
        assert response['statusCode'] == 413
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'too large' in body['error']['errorMessage'].lower()
    
    def test_invalid_mp3_magic_bytes(self):
        """Test error for invalid MP3 file format"""
        # Invalid MP3 data (wrong magic bytes)
        invalid_data = b'INVALID' + b'\x00' * 100
        invalid_b64 = base64.b64encode(invalid_data).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'audio': invalid_b64,
                'format': 'audio/mpeg'
            })
        }
        
        context = None
        
        response = audio_input_handler.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'Invalid' in body['error']['errorMessage']
    
    def test_s3_upload_failure(self):
        """Test handling of S3 upload failure"""
        mp3_data = b'ID3' + b'\x00' * 100
        mp3_b64 = base64.b64encode(mp3_data).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'audio': mp3_b64,
                'format': 'audio/mpeg'
            })
        }
        
        context = None
        
        with patch('audio_input_handler.get_s3_client') as mock_s3:
            mock_s3_client = Mock()
            mock_s3_client.put_object.side_effect = ClientError(
                {'Error': {'Code': 'ServiceUnavailable'}},
                'PutObject'
            )
            mock_s3.return_value = mock_s3_client
            
            response = audio_input_handler.lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error']['retryable'] is True


class TestSpeechToTextService:
    """Tests for speech-to-text service Lambda function"""
    
    def test_successful_transcription_english(self):
        """Test successful transcription for English"""
        event = {
            'body': json.dumps({
                's3Key': 'uploads/test_audio.mp3',
                'audioId': 'test_audio_123',
                'language': 'en',
                'userId': 'test_user'
            })
        }
        
        context = None
        
        
        with patch('speech_to_text_service.transcribe_with_amazon') as mock_transcribe:
            mock_transcribe.return_value = ('Hello, how are you?', 0.95)
            
            response = speech_to_text_service.lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert body['data']['transcript'] == 'Hello, how are you?'
            assert body['data']['confidence'] == 0.95
            assert body['data']['processingMethod'] == 'transcribe'
    
    def test_successful_transcription_hindi(self):
        """Test successful transcription for Hindi"""
        event = {
            'body': json.dumps({
                's3Key': 'uploads/test_audio.mp3',
                'audioId': 'test_audio_123',
                'language': 'hi',
                'userId': 'test_user'
            })
        }
        
        context = None
        
        with patch('speech_to_text_service.transcribe_with_amazon') as mock_transcribe:
            mock_transcribe.return_value = ('नमस्ते', 0.92)
            
            response = speech_to_text_service.lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert body['data']['transcript'] == 'नमस्ते'
            assert body['data']['language'] == 'hi'
    
    def test_missing_s3_key(self):
        """Test error when s3Key is missing"""
        event = {
            'body': json.dumps({
                'language': 'en'
            })
        }
        
        context = None
        
        response = speech_to_text_service.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 's3Key' in body['error']['errorMessage']
    
    def test_fallback_to_bhashini(self):
        """Test fallback to Bhashini when Transcribe fails"""
        event = {
            'body': json.dumps({
                's3Key': 'uploads/test_audio.mp3',
                'language': 'ta',  # Tamil - not supported by Transcribe
                'userId': 'test_user'
            })
        }
        
        context = None
        
        with patch('speech_to_text_service.ENABLE_BHASHINI', True):
            with patch('speech_to_text_service.transcribe_with_bhashini') as mock_bhashini:
                mock_bhashini.return_value = ('வணக்கம்', 0.88)
                
                response = speech_to_text_service.lambda_handler(event, context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['data']['processingMethod'] == 'bhashini'
    
    def test_transcription_failure(self):
        """Test error when all transcription methods fail"""
        event = {
            'body': json.dumps({
                's3Key': 'uploads/test_audio.mp3',
                'language': 'en'
            })
        }
        
        context = None
        
        with patch('speech_to_text_service.transcribe_with_amazon') as mock_transcribe:
            mock_transcribe.return_value = (None, 0.0)
            
            response = speech_to_text_service.lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['success'] is False
            assert 'Failed to transcribe' in body['error']['errorMessage']
    
    def test_language_detection(self):
        """Test language detection from hint"""
        lang, confidence = speech_to_text_service.detect_language_from_hint('hi-IN')
        assert lang == 'hi'
        assert confidence >= 0.85
        
        lang, confidence = speech_to_text_service.detect_language_from_hint('unknown')
        assert lang == 'en'  # Default to English


class TestTextToSpeechService:
    """Tests for text-to-speech service Lambda function"""
    
    def test_successful_synthesis_english(self):
        """Test successful TTS synthesis for English"""
        event = {
            'body': json.dumps({
                'text': 'Hello, welcome to SarkariSaathi',
                'language': 'en',
                'userId': 'test_user'
            })
        }
        
        context = None
        
        
        mock_audio = b'fake_audio_data'
        
        with patch('text_to_speech_service.check_cache_exists') as mock_cache:
            mock_cache.return_value = False
            
            with patch('text_to_speech_service.synthesize_with_polly') as mock_polly:
                mock_polly.return_value = mock_audio
                
                with patch('text_to_speech_service.get_s3_client') as mock_s3:
                    mock_s3_client = Mock()
                    mock_s3_client.put_object = Mock()
                    mock_s3.return_value = mock_s3_client
                    
                    with patch('text_to_speech_service.get_audio_url') as mock_url:
                        mock_url.return_value = 'https://test-audio-url.com'
                        
                        response = text_to_speech_service.lambda_handler(event, context)
                        
                        assert response['statusCode'] == 200
                        body = json.loads(response['body'])
                        assert body['success'] is True
                        assert body['data']['audioUrl'] == 'https://test-audio-url.com'
                        assert body['data']['cacheHit'] is False
                        assert body['data']['processingMethod'] == 'polly'
    
    def test_cache_hit(self):
        """Test TTS cache hit"""
        event = {
            'body': json.dumps({
                'text': 'Cached text',
                'language': 'en'
            })
        }
        
        context = None
        
        with patch('text_to_speech_service.check_cache_exists') as mock_cache:
            mock_cache.return_value = True
            
            with patch('text_to_speech_service.get_audio_url') as mock_url:
                mock_url.return_value = 'https://cached-audio-url.com'
                
                response = text_to_speech_service.lambda_handler(event, context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['data']['cacheHit'] is True
                assert body['data']['processingMethod'] == 'cache'
    
    def test_missing_text_field(self):
        """Test error when text field is missing"""
        event = {
            'body': json.dumps({
                'language': 'en'
            })
        }
        
        context = None
        
        response = text_to_speech_service.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'text' in body['error']['errorMessage']
    
    def test_text_too_long(self):
        """Test error when text exceeds maximum length"""
        long_text = 'a' * 4000  # Exceeds MAX_TEXT_LENGTH
        
        event = {
            'body': json.dumps({
                'text': long_text,
                'language': 'en'
            })
        }
        
        context = None
        
        response = text_to_speech_service.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'too long' in body['error']['errorMessage'].lower()
    
    def test_invalid_speed(self):
        """Test error for invalid speed parameter"""
        event = {
            'body': json.dumps({
                'text': 'Test text',
                'language': 'en',
                'speed': 3.0  # Invalid (must be 0.5-2.0)
            })
        }
        
        context = None
        
        response = text_to_speech_service.lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'speed' in body['error']['errorMessage'].lower()
    
    def test_synthesis_failure(self):
        """Test error when synthesis fails"""
        event = {
            'body': json.dumps({
                'text': 'Test text',
                'language': 'en'
            })
        }
        
        context = None
        
        with patch('text_to_speech_service.check_cache_exists') as mock_cache:
            mock_cache.return_value = False
            
            with patch('text_to_speech_service.synthesize_with_polly') as mock_polly:
                mock_polly.return_value = None
                
                response = text_to_speech_service.lambda_handler(event, context)
                
                assert response['statusCode'] == 500
                body = json.loads(response['body'])
                assert body['success'] is False
                assert 'Failed to synthesize' in body['error']['errorMessage']
    
    def test_cache_key_generation(self):
        """Test cache key generation consistency"""
        key1 = text_to_speech_service.generate_tts_cache_key('Hello', 'en', 1.0)
        key2 = text_to_speech_service.generate_tts_cache_key('Hello', 'en', 1.0)
        key3 = text_to_speech_service.generate_tts_cache_key('Hello', 'hi', 1.0)
        
        # Same input should generate same key
        assert key1 == key2
        
        # Different language should generate different key
        assert key1 != key3
    
    def test_language_normalization(self):
        """Test language code normalization"""
        assert text_to_speech_service.normalize_language('en-IN') == 'en-IN'
        assert text_to_speech_service.normalize_language('EN') == 'en'
        assert text_to_speech_service.normalize_language('hi-IN') == 'hi-IN'
        assert text_to_speech_service.normalize_language('ta-IN') == 'ta'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

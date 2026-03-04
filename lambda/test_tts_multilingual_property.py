"""
Property-Based Tests for TTS Quality and Multilingual Support

Feature: sarkari-saathi
Property 2: Multilingual Processing
Property 3: Text-to-Speech Quality

**Validates: Requirements 1.2, 2.1, 2.2, 2.5**

These tests verify that:
1. TTS service generates audio for all supported languages
2. Language detection works correctly for various inputs
3. Code-mixing is handled appropriately
4. Audio output quality is consistent
"""

import json
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, Tuple, Optional
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import hashlib

# Mock AWS services before importing
with patch('boto3.client') as mock_client:
    mock_client.return_value = Mock()
    
    # Set environment variables
    os.environ['TTS_CACHE_BUCKET'] = 'test-tts-cache-bucket'
    os.environ['BHASHINI_API_URL'] = 'https://test-bhashini.example.com'
    os.environ['BHASHINI_API_KEY'] = 'test-key'
    os.environ['ENABLE_BHASHINI'] = 'false'
    os.environ['CACHE_TTL_DAYS'] = '7'
    os.environ['MAX_TEXT_LENGTH'] = '3000'
    
    # Import the text-to-speech service
    from text_to_speech_service import (
        synthesize_with_fallback,
        synthesize_with_polly,
        normalize_language,
        generate_tts_cache_key,
        POLLY_VOICES,
        BHASHINI_TTS_LANGUAGES
    )


# ============================================================================
# Test Data Strategies
# ============================================================================

# Supported languages
SUPPORTED_LANGUAGES = list(POLLY_VOICES.keys()) + list(BHASHINI_TTS_LANGUAGES.keys())

# Speech speeds
SPEECH_SPEEDS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]


@st.composite
def text_input_strategy(draw):
    """Generate valid text inputs for TTS."""
    # Generate text of varying lengths
    word_count = draw(st.integers(min_value=1, max_value=100))
    words = [f"word{i}" for i in range(word_count)]
    text = " ".join(words)
    
    return text


@st.composite
def language_strategy(draw):
    """Generate language codes including edge cases."""
    return draw(st.one_of(
        st.sampled_from(SUPPORTED_LANGUAGES),
        st.sampled_from(['en-IN', 'hi-IN', 'en-US']),  # With country codes
        st.sampled_from(['EN', 'HI', 'Ta', 'Te']),  # Case variations
        st.text(min_size=2, max_size=5, alphabet='abcdefghijklmnopqrstuvwxyz')  # Random strings
    ))


@st.composite
def tts_request_strategy(draw):
    """Generate valid TTS request configurations."""
    language = draw(st.sampled_from(SUPPORTED_LANGUAGES))
    
    return {
        "text": draw(text_input_strategy()),
        "language": language,
        "speed": draw(st.sampled_from(SPEECH_SPEEDS)),
        "userId": f"user-{draw(st.integers(min_value=1, max_value=10000))}",
        "sessionId": f"session-{draw(st.integers(min_value=1, max_value=10000))}"
    }


@st.composite
def code_mixed_text_strategy(draw):
    """Generate code-mixed text (English + regional language)."""
    # Simulate code-mixing by combining English and transliterated words
    english_words = ["hello", "please", "thank", "you", "government", "scheme"]
    hindi_words = ["namaste", "dhanyavaad", "sarkar", "yojana", "kripa"]
    
    word_count = draw(st.integers(min_value=3, max_value=15))
    words = []
    for _ in range(word_count):
        if draw(st.booleans()):
            words.append(draw(st.sampled_from(english_words)))
        else:
            words.append(draw(st.sampled_from(hindi_words)))
    
    return " ".join(words)


# ============================================================================
# Property 2: Multilingual Processing
# ============================================================================

class TestMultilingualProcessing:
    """
    **Validates: Requirements 2.1, 2.2, 2.5**
    
    Property 2: For any text or audio input in supported Indian languages
    (including code-mixed content), the Language_Processor should correctly
    detect the language, process the content, and respond in the appropriate language.
    """
    
    @given(language=st.sampled_from(SUPPORTED_LANGUAGES))
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_supported_languages_are_normalized(self, language: str):
        """
        Property: All supported languages should be normalized to valid codes.
        
        **Validates: Requirement 2.1** - Support for specified Indian languages
        
        This ensures the system can handle all 10 supported languages.
        """
        normalized = normalize_language(language)
        
        # Normalized language should be in supported languages
        all_supported = list(POLLY_VOICES.keys()) + list(BHASHINI_TTS_LANGUAGES.keys())
        assert normalized in all_supported, \
            f"Normalized language '{normalized}' must be in supported languages"

    
    @given(language=language_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_language_normalization_is_consistent(self, language: str):
        """
        Property: Language normalization should be idempotent - normalizing
        twice should give the same result.
        
        **Validates: Requirement 2.1** - Language processing consistency
        """
        normalized_once = normalize_language(language)
        normalized_twice = normalize_language(normalized_once)
        
        assert normalized_once == normalized_twice, \
            f"Normalization should be idempotent: {normalized_once} != {normalized_twice}"
    
    
    @given(language_with_code=st.sampled_from(['en-IN', 'hi-IN', 'en-US', 'ta-IN', 'te-IN']))
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_language_with_country_code_is_normalized(self, language_with_code: str):
        """
        Property: Language codes with country suffixes should be normalized
        to base language codes or kept as-is for Polly voices.
        
        **Validates: Requirement 2.1** - Language handling
        """
        normalized = normalize_language(language_with_code)
        
        # Should be a valid language code
        all_supported = list(POLLY_VOICES.keys()) + list(BHASHINI_TTS_LANGUAGES.keys())
        assert normalized in all_supported, \
            f"Normalized language '{normalized}' must be supported"
    
    
    @given(tts_request=tts_request_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_polly_languages_use_polly_service(
        self,
        mock_polly_client,
        tts_request: Dict[str, Any]
    ):
        """
        Property: Languages supported by Polly should use Polly service.
        
        **Validates: Requirement 2.1** - Appropriate service selection
        """
        # Only test Polly-supported languages
        assume(tts_request['language'] in POLLY_VOICES)
        
        # Mock Polly client
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        
        # Mock successful synthesis
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake_audio_data'
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        audio_bytes, method = synthesize_with_fallback(
            text=tts_request['text'],
            language=tts_request['language'],
            speed=tts_request['speed']
        )
        
        # Should use Polly
        assert method == 'polly', \
            f"Polly-supported language '{tts_request['language']}' should use Polly"
        assert audio_bytes is not None, "Should return audio bytes"
    
    
    @given(code_mixed_text=code_mixed_text_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_code_mixed_text_is_processed(
        self,
        mock_polly_client,
        code_mixed_text: str
    ):
        """
        Property: Code-mixed text (English + regional language) should be
        processed successfully.
        
        **Validates: Requirement 2.5** - Handle code-mixing
        """
        # Mock Polly client
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake_audio_data'
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        # Try with Hindi (common code-mixing scenario)
        audio_bytes, method = synthesize_with_fallback(
            text=code_mixed_text,
            language='hi',
            speed=1.0
        )
        
        # Should successfully process code-mixed text
        assert audio_bytes is not None, "Code-mixed text should be processed"
        assert method in ['polly', 'bhashini', 'none'], "Should use valid method"

    
    @given(
        original_lang=st.sampled_from(['en', 'hi']),
        new_lang=st.sampled_from(['ta', 'te', 'en'])
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_language_switching_mid_conversation(
        self,
        mock_polly_client,
        original_lang: str,
        new_lang: str
    ):
        """
        Property: System should handle language switches mid-conversation.
        
        **Validates: Requirement 2.2** - Detect language changes and respond
        in new language
        """
        # Mock Polly client
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake_audio_data'
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        # First request in original language
        audio1, method1 = synthesize_with_fallback(
            text="First message",
            language=original_lang,
            speed=1.0
        )
        
        # Second request in new language
        audio2, method2 = synthesize_with_fallback(
            text="Second message",
            language=new_lang,
            speed=1.0
        )
        
        # Both should succeed
        if original_lang in POLLY_VOICES:
            assert audio1 is not None, f"Original language '{original_lang}' should work"
        
        if new_lang in POLLY_VOICES:
            assert audio2 is not None, f"New language '{new_lang}' should work"


# ============================================================================
# Property 3: Text-to-Speech Quality
# ============================================================================

class TestTextToSpeechQuality:
    """
    **Validates: Requirements 1.2**
    
    Property 3: For any text response in supported languages, the Audio_Interface
    should generate natural-sounding speech in the user's preferred language
    with consistent quality.
    """
    
    @given(tts_request=tts_request_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_tts_returns_non_empty_audio(
        self,
        mock_polly_client,
        tts_request: Dict[str, Any]
    ):
        """
        Property: Successful TTS synthesis must return non-empty audio data.
        
        **Validates: Requirement 1.2** - Convert text to speech
        """
        # Only test Polly-supported languages
        assume(tts_request['language'] in POLLY_VOICES)
        
        # Mock Polly client
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake_audio_data_with_content'
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        audio_bytes, method = synthesize_with_fallback(
            text=tts_request['text'],
            language=tts_request['language'],
            speed=tts_request['speed']
        )
        
        # If synthesis succeeded, audio must be non-empty
        if audio_bytes:
            assert len(audio_bytes) > 0, "Audio data must be non-empty"
            assert isinstance(audio_bytes, bytes), "Audio must be bytes"

    
    @given(
        text=text_input_strategy(),
        language=st.sampled_from(['en', 'hi']),
        speed=st.sampled_from(SPEECH_SPEEDS)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_speech_speed_is_applied_correctly(
        self,
        mock_polly_client,
        text: str,
        language: str,
        speed: float
    ):
        """
        Property: Speech speed parameter should be applied to synthesis.
        
        **Validates: Requirement 1.2** - Natural-sounding speech with quality
        """
        # Mock Polly client
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake_audio_data'
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        audio_bytes = synthesize_with_polly(
            text=text,
            language=language,
            speed=speed
        )
        
        # Verify Polly was called
        if mock_client.synthesize_speech.called:
            call_args = mock_client.synthesize_speech.call_args
            
            # Check that SSML includes prosody rate
            ssml_text = call_args[1]['Text']
            expected_rate = int(speed * 100)
            
            assert 'prosody' in ssml_text, "SSML should include prosody tag"
            assert f'rate="{expected_rate}%"' in ssml_text, \
                f"SSML should include rate={expected_rate}%"
    
    
    @given(tts_request=tts_request_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_fallback_chain_returns_consistent_format(
        self,
        mock_polly_client,
        tts_request: Dict[str, Any]
    ):
        """
        Property: The fallback chain must always return a consistent tuple format:
        (audio_bytes, method).
        
        **Validates: Requirement 1.2** - Reliable speech synthesis
        """
        # Mock Polly client
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake_audio_data'
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        result = synthesize_with_fallback(
            text=tts_request['text'],
            language=tts_request['language'],
            speed=tts_request['speed']
        )
        
        # Must return a tuple of 2 elements
        assert isinstance(result, tuple), "Result must be a tuple"
        assert len(result) == 2, "Result must have 2 elements"
        
        audio_bytes, method = result
        
        # Validate types
        assert audio_bytes is None or isinstance(audio_bytes, bytes), \
            "Audio must be None or bytes"
        assert isinstance(method, str), "Method must be string"
        assert method in ['polly', 'bhashini', 'none'], \
            f"Method must be valid, got '{method}'"
    
    
    @given(
        text=text_input_strategy(),
        language=st.sampled_from(['en', 'hi'])
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_same_text_generates_same_cache_key(
        self,
        mock_polly_client,
        text: str,
        language: str
    ):
        """
        Property: Same text, language, and speed should generate the same cache key.
        
        **Validates: Requirement 1.2** - Consistent quality and caching
        """
        speed = 1.0
        
        # Generate cache key twice
        key1 = generate_tts_cache_key(text, language, speed)
        key2 = generate_tts_cache_key(text, language, speed)
        
        assert key1 == key2, "Same inputs should generate same cache key"
        
        # Cache key should be a valid hash
        assert len(key1) == 64, "Cache key should be SHA-256 hash (64 chars)"
        assert all(c in '0123456789abcdef' for c in key1), \
            "Cache key should be hexadecimal"

    
    @given(
        text=text_input_strategy(),
        language=st.sampled_from(['en', 'hi']),
        speed1=st.sampled_from(SPEECH_SPEEDS),
        speed2=st.sampled_from(SPEECH_SPEEDS)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_different_speeds_generate_different_cache_keys(
        self,
        text: str,
        language: str,
        speed1: float,
        speed2: float
    ):
        """
        Property: Different speeds should generate different cache keys.
        
        **Validates: Requirement 1.2** - Quality consistency per configuration
        """
        assume(speed1 != speed2)
        
        key1 = generate_tts_cache_key(text, language, speed1)
        key2 = generate_tts_cache_key(text, language, speed2)
        
        assert key1 != key2, \
            f"Different speeds should generate different cache keys"
    
    
    @given(tts_request=tts_request_strategy())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('text_to_speech_service.get_polly_client')
    def test_polly_uses_neural_engine_for_quality(
        self,
        mock_polly_client,
        tts_request: Dict[str, Any]
    ):
        """
        Property: Polly synthesis should use neural engine for better quality.
        
        **Validates: Requirement 1.2** - Natural-sounding speech
        """
        # Only test Polly-supported languages
        assume(tts_request['language'] in POLLY_VOICES)
        
        # Mock Polly client
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        
        mock_audio_stream = Mock()
        mock_audio_stream.read.return_value = b'fake_audio_data'
        mock_client.synthesize_speech.return_value = {
            'AudioStream': mock_audio_stream
        }
        
        audio_bytes = synthesize_with_polly(
            text=tts_request['text'],
            language=tts_request['language'],
            speed=tts_request['speed']
        )
        
        # Verify Polly was called with neural engine
        if mock_client.synthesize_speech.called:
            call_args = mock_client.synthesize_speech.call_args
            
            assert call_args[1]['Engine'] == 'neural', \
                "Should use neural engine for better quality"


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

class TestEdgeCases:
    """
    Tests for edge cases and boundary conditions in TTS.
    """
    
    def test_empty_text_generates_valid_cache_key(self):
        """Edge case: Empty text should generate a valid cache key."""
        key = generate_tts_cache_key("", "en", 1.0)
        
        assert len(key) == 64, "Should generate valid hash for empty text"
    
    
    def test_very_long_text_generates_valid_cache_key(self):
        """Edge case: Very long text should generate a valid cache key."""
        long_text = "word " * 1000  # 5000 characters
        key = generate_tts_cache_key(long_text, "en", 1.0)
        
        assert len(key) == 64, "Should generate valid hash for long text"
    
    
    def test_special_characters_in_text(self):
        """Edge case: Special characters should be handled in cache key."""
        special_text = "Hello! How are you? I'm fine. #test @user"
        key = generate_tts_cache_key(special_text, "en", 1.0)
        
        assert len(key) == 64, "Should handle special characters"
    
    
    def test_unicode_text_in_cache_key(self):
        """Edge case: Unicode text (Hindi, Tamil) should work in cache key."""
        hindi_text = "नमस्ते सरकारी साथी"
        tamil_text = "வணக்கம் அரசு திட்டம்"
        
        key_hindi = generate_tts_cache_key(hindi_text, "hi", 1.0)
        key_tamil = generate_tts_cache_key(tamil_text, "ta", 1.0)
        
        assert len(key_hindi) == 64, "Should handle Hindi text"
        assert len(key_tamil) == 64, "Should handle Tamil text"
        assert key_hindi != key_tamil, "Different texts should have different keys"

    
    @given(st.sampled_from(['EN', 'Hi', 'TA', 'te', 'En-In', 'HI-IN']))
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_case_insensitive_language_normalization(self, language: str):
        """Edge case: Language normalization should be case-insensitive."""
        normalized = normalize_language(language)
        
        # Should normalize to lowercase or keep Polly format
        assert normalized.islower() or normalized in POLLY_VOICES, \
            f"Language should be normalized: {normalized}"
    
    
    def test_minimum_speed_boundary(self):
        """Edge case: Minimum speed (0.5) should be valid."""
        key = generate_tts_cache_key("test", "en", 0.5)
        assert len(key) == 64, "Minimum speed should work"
    
    
    def test_maximum_speed_boundary(self):
        """Edge case: Maximum speed (2.0) should be valid."""
        key = generate_tts_cache_key("test", "en", 2.0)
        assert len(key) == 64, "Maximum speed should work"
    
    
    def test_normal_speed_default(self):
        """Edge case: Normal speed (1.0) should be the default."""
        key = generate_tts_cache_key("test", "en", 1.0)
        assert len(key) == 64, "Normal speed should work"
    
    
    @given(st.sampled_from(list(POLLY_VOICES.keys())))
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_polly_voices_are_configured(self, language: str):
        """Edge case: All Polly languages should have voice configuration."""
        voice_config = POLLY_VOICES.get(language)
        
        assert voice_config is not None, f"Language '{language}' should have voice config"
        assert 'voiceId' in voice_config, "Should have voiceId"
        assert 'engine' in voice_config, "Should have engine"
        assert 'languageCode' in voice_config, "Should have languageCode"
        assert voice_config['engine'] == 'neural', "Should use neural engine"
    
    
    @given(st.sampled_from(list(BHASHINI_TTS_LANGUAGES.keys())))
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_bhashini_languages_are_mapped(self, language: str):
        """Edge case: All Bhashini languages should be mapped."""
        bhashini_code = BHASHINI_TTS_LANGUAGES.get(language)
        
        assert bhashini_code is not None, \
            f"Language '{language}' should have Bhashini mapping"
        assert isinstance(bhashini_code, str), "Bhashini code should be string"
    
    
    def test_unsupported_language_normalization(self):
        """Edge case: Unsupported language should default gracefully."""
        # Test with a completely unsupported language
        normalized = normalize_language('xyz')
        
        # Should return lowercase version
        assert normalized == 'xyz', "Should return lowercase for unknown language"
    
    
    @patch('text_to_speech_service.get_polly_client')
    def test_polly_failure_returns_none(self, mock_polly_client):
        """Edge case: Polly failure should return None gracefully."""
        # Mock Polly client to raise exception
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        mock_client.synthesize_speech.side_effect = Exception("Polly error")
        
        audio_bytes = synthesize_with_polly("test", "en", 1.0)
        
        assert audio_bytes is None, "Should return None on Polly failure"
    
    
    @patch('text_to_speech_service.get_polly_client')
    def test_fallback_chain_handles_all_failures(self, mock_polly_client):
        """Edge case: When all services fail, should return (None, 'none')."""
        # Mock Polly to fail
        mock_client = Mock()
        mock_polly_client.return_value = mock_client
        mock_client.synthesize_speech.side_effect = Exception("All services failed")
        
        audio_bytes, method = synthesize_with_fallback("test", "en", 1.0)
        
        # When all fail, should return None and 'none'
        assert audio_bytes is None, "Should return None when all services fail"
        assert method == 'none', "Method should be 'none' when all fail"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

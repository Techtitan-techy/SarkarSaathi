"""
Test Error Handling and Fallback Mechanisms

This test verifies that the error handler and API fallback strategies
work correctly.
"""

import pytest
import json
from datetime import datetime
from shared.error_handler import (
    ErrorHandler,
    TranscriptionError,
    EligibilityError,
    APIError,
    GovernmentAPIError,
    ErrorSeverity,
    get_user_friendly_message,
    get_recovery_suggestion
)
from shared.api_fallback import (
    CircuitBreaker,
    ExponentialBackoff,
    FallbackChain,
    CircuitState
)


# ========================================
# Error Handler Tests
# ========================================

def test_transcription_error():
    """Test TranscriptionError creation and properties"""
    error = TranscriptionError("Low audio quality")
    
    assert error.error_code == "TRANSCRIPTION_ERROR"
    assert error.severity == ErrorSeverity.WARNING
    assert error.retryable == True
    assert 'en' in error.user_message
    assert 'hi' in error.user_message


def test_eligibility_error():
    """Test EligibilityError creation"""
    error = EligibilityError("Age criteria not met")
    
    assert error.error_code == "ELIGIBILITY_ERROR"
    assert error.severity == ErrorSeverity.INFO
    assert error.retryable == False
    assert 'en' in error.user_message
    assert 'hi' in error.user_message


def test_api_error():
    """Test APIError creation"""
    error = APIError("Connection timeout", "Bhashini")
    
    assert "BHASHINI" in error.error_code
    assert error.severity == ErrorSeverity.ERROR
    assert error.retryable == True


def test_government_api_error():
    """Test GovernmentAPIError creation"""
    error = GovernmentAPIError("Service unavailable")
    
    assert error.error_code == "GOVERNMENT_API_ERROR"
    assert error.severity == ErrorSeverity.WARNING
    assert 'manual submission' in error.user_message['en'].lower()


def test_error_handler_custom_error():
    """Test ErrorHandler with custom SarkariSaathi errors"""
    handler = ErrorHandler()
    error = TranscriptionError("Test error")
    context = {'function': 'test_function', 'user_id': 'test_user'}
    
    response = handler.handle_error(error, context, language='en')
    
    assert response['statusCode'] in [200, 500]
    assert 'body' in response
    
    body = json.loads(response['body'])
    assert body['success'] == False
    assert 'error' in body
    assert body['error']['errorCode'] == 'TRANSCRIPTION_ERROR'


def test_error_handler_generic_error():
    """Test ErrorHandler with generic Python errors"""
    handler = ErrorHandler()
    error = ValueError("Invalid input")
    context = {'function': 'test_function'}
    
    response = handler.handle_error(error, context, language='en')
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['success'] == False


def test_get_user_friendly_message():
    """Test user-friendly message retrieval"""
    message_en = get_user_friendly_message('TRANSCRIPTION_ERROR', 'en')
    message_hi = get_user_friendly_message('TRANSCRIPTION_ERROR', 'hi')
    
    assert len(message_en) > 0
    assert len(message_hi) > 0
    assert message_en != message_hi


def test_get_recovery_suggestion():
    """Test recovery suggestion retrieval"""
    suggestion_en = get_recovery_suggestion('ELIGIBILITY_ERROR', 'en')
    suggestion_hi = get_recovery_suggestion('ELIGIBILITY_ERROR', 'hi')
    
    assert len(suggestion_en) > 0
    assert len(suggestion_hi) > 0


# ========================================
# Circuit Breaker Tests
# ========================================

def test_circuit_breaker_closed_state():
    """Test circuit breaker in closed state"""
    cb = CircuitBreaker("test_service", failure_threshold=3)
    
    # Should allow calls in closed state
    result = cb.call(lambda: "success")
    assert result == "success"
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures"""
    cb = CircuitBreaker("test_service", failure_threshold=3)
    
    # Cause failures
    for i in range(3):
        try:
            cb.call(lambda: 1/0)  # Will raise ZeroDivisionError
        except:
            pass
    
    # Circuit should be open now
    assert cb.state == CircuitState.OPEN
    
    # Should reject calls
    with pytest.raises(Exception, match="Circuit breaker.*is OPEN"):
        cb.call(lambda: "success")


def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker recovery through half-open state"""
    cb = CircuitBreaker(
        "test_service",
        failure_threshold=2,
        recovery_timeout=0,  # Immediate recovery attempt
        success_threshold=2
    )
    
    # Open the circuit
    for i in range(2):
        try:
            cb.call(lambda: 1/0)
        except:
            pass
    
    assert cb.state == CircuitState.OPEN
    
    # Should transition to half-open
    result = cb.call(lambda: "success")
    assert result == "success"
    assert cb.state == CircuitState.HALF_OPEN
    
    # Another success should close it
    result = cb.call(lambda: "success")
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_get_state():
    """Test circuit breaker state retrieval"""
    cb = CircuitBreaker("test_service")
    state = cb.get_state()
    
    assert state['name'] == "test_service"
    assert state['state'] == CircuitState.CLOSED.value
    assert 'failureCount' in state
    assert 'successCount' in state


# ========================================
# Exponential Backoff Tests
# ========================================

def test_exponential_backoff_success():
    """Test exponential backoff with successful call"""
    backoff = ExponentialBackoff(base_delay=0.1, max_retries=3)
    
    call_count = [0]
    def test_func():
        call_count[0] += 1
        return "success"
    
    result = backoff.execute(test_func)
    assert result == "success"
    assert call_count[0] == 1  # Should succeed on first try


def test_exponential_backoff_retry():
    """Test exponential backoff retries on failure"""
    backoff = ExponentialBackoff(base_delay=0.01, max_retries=3)
    
    call_count = [0]
    def test_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    result = backoff.execute(test_func, retryable_exceptions=(ValueError,))
    assert result == "success"
    assert call_count[0] == 3  # Should succeed on third try


def test_exponential_backoff_exhausted():
    """Test exponential backoff when retries exhausted"""
    backoff = ExponentialBackoff(base_delay=0.01, max_retries=2)
    
    def test_func():
        raise ValueError("Persistent failure")
    
    with pytest.raises(ValueError, match="Persistent failure"):
        backoff.execute(test_func, retryable_exceptions=(ValueError,))


# ========================================
# Fallback Chain Tests
# ========================================

def test_fallback_chain_primary_success():
    """Test fallback chain with primary success"""
    chain = FallbackChain("test_operation")
    
    chain.add_fallback(lambda: "primary", "primary", priority=0)
    chain.add_fallback(lambda: "secondary", "secondary", priority=1)
    
    result = chain.execute()
    assert result['success'] == True
    assert result['data'] == "primary"
    assert result['fallbackUsed'] == "primary"


def test_fallback_chain_secondary_fallback():
    """Test fallback chain falls back to secondary"""
    chain = FallbackChain("test_operation")
    
    def primary():
        raise Exception("Primary failed")
    
    chain.add_fallback(primary, "primary", priority=0)
    chain.add_fallback(lambda: "secondary", "secondary", priority=1)
    
    result = chain.execute()
    assert result['success'] == True
    assert result['data'] == "secondary"
    assert result['fallbackUsed'] == "secondary"


def test_fallback_chain_all_fail():
    """Test fallback chain when all fallbacks fail"""
    chain = FallbackChain("test_operation")
    
    def failing_func():
        raise Exception("Failed")
    
    chain.add_fallback(failing_func, "primary", priority=0)
    chain.add_fallback(failing_func, "secondary", priority=1)
    
    result = chain.execute()
    assert result['success'] == False
    assert result['fallbackUsed'] == 'none'


def test_fallback_chain_priority_order():
    """Test fallback chain respects priority order"""
    chain = FallbackChain("test_operation")
    
    # Add in reverse priority order
    chain.add_fallback(lambda: "low", "low", priority=2)
    chain.add_fallback(lambda: "high", "high", priority=0)
    chain.add_fallback(lambda: "medium", "medium", priority=1)
    
    result = chain.execute()
    assert result['data'] == "high"  # Should use highest priority


# ========================================
# Integration Tests
# ========================================

def test_error_handler_with_circuit_breaker():
    """Test integration of error handler with circuit breaker"""
    handler = ErrorHandler()
    cb = CircuitBreaker("test_api", failure_threshold=2)
    
    # Simulate API failures
    for i in range(2):
        try:
            cb.call(lambda: 1/0)
        except:
            pass
    
    # Circuit should be open
    assert cb.state == CircuitState.OPEN
    
    # Try to call through circuit breaker
    try:
        cb.call(lambda: "success")
    except Exception as e:
        response = handler.handle_error(e, {'function': 'test'}, 'en')
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] == False


def test_multilingual_error_messages():
    """Test error messages in multiple languages"""
    handler = ErrorHandler()
    error = TranscriptionError("Test error")
    
    # Test English
    response_en = handler.handle_error(error, {}, 'en')
    body_en = json.loads(response_en['body'])
    message_en = body_en['error']['errorMessage']
    
    # Test Hindi
    response_hi = handler.handle_error(error, {}, 'hi')
    body_hi = json.loads(response_hi['body'])
    message_hi = body_hi['error']['errorMessage']
    
    # Messages should be different
    assert message_en != message_hi
    assert len(message_en) > 0
    assert len(message_hi) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

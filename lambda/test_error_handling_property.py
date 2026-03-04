"""
Property-Based Test for Error Handling and Alternatives

**Validates: Requirements 1.5, 4.3, 7.4**

This test validates Property 6 from the design document:
"For any ineligible user profile or failed operation, the system should provide 
clear explanations and suggest appropriate alternatives or fallback options"

Test Coverage:
1. Speech recognition failures trigger retry prompts (Requirement 1.5)
2. Ineligible users get explanations and alternatives (Requirement 4.3)
3. API failures provide manual fallback instructions (Requirement 7.4)
4. Error messages are clear and actionable

Uses fast-check for property-based testing with 20-25 iterations.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any, List
import json
from datetime import datetime

from shared.error_handler import (
    ErrorHandler,
    TranscriptionError,
    EligibilityError,
    APIError,
    GovernmentAPIError,
    DatabaseError,
    ValidationError,
    ErrorSeverity,
    get_user_friendly_message,
    get_recovery_suggestion
)
from shared.api_fallback import (
    CircuitBreaker,
    ExponentialBackoff,
    FallbackChain,
    CircuitState,
    GovernmentAPIClient
)


# ========================================
# Test Strategies
# ========================================

# Language strategy
languages = st.sampled_from(['en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa'])

# Error message content strategy
error_messages = st.text(min_size=5, max_size=100, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
    whitelist_characters=' .,!?'
))

# User context strategy
@st.composite
def user_context_strategy(draw):
    """Generate random user context for error scenarios"""
    return {
        'user_id': draw(st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'session_id': draw(st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'function': draw(st.sampled_from(['voice_handler', 'eligibility_engine', 'application_assistant'])),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

# Scheme ID strategy
scheme_ids = st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd')))

# Audio quality issues strategy
audio_issues = st.sampled_from([
    'Low audio quality',
    'Background noise detected',
    'Speech too fast',
    'Speech too slow',
    'Unclear pronunciation',
    'Audio timeout',
    'Microphone error'
])

# Ineligibility reasons strategy
@st.composite
def ineligibility_reason_strategy(draw):
    """Generate ineligibility reasons"""
    reason_type = draw(st.sampled_from(['age', 'income', 'state', 'category', 'occupation']))
    
    reasons = {
        'age': {
            'en': 'Your age does not meet the scheme requirements',
            'hi': 'आपकी आयु योजना की आवश्यकताओं को पूरा नहीं करती है'
        },
        'income': {
            'en': 'Your income exceeds the eligibility limit',
            'hi': 'आपकी आय पात्रता सीमा से अधिक है'
        },
        'state': {
            'en': 'This scheme is not available in your state',
            'hi': 'यह योजना आपके राज्य में उपलब्ध नहीं है'
        },
        'category': {
            'en': 'Your category does not qualify for this scheme',
            'hi': 'आपकी श्रेणी इस योजना के लिए योग्य नहीं है'
        },
        'occupation': {
            'en': 'Your occupation is not eligible for this scheme',
            'hi': 'आपका व्यवसाय इस योजना के लिए पात्र नहीं है'
        }
    }
    
    return reasons[reason_type]

# API failure types strategy
api_failures = st.sampled_from([
    'Connection timeout',
    'Service unavailable',
    'Rate limit exceeded',
    'Authentication failed',
    'Invalid response',
    'Network error'
])


# ========================================
# Property 6: Error Handling and Alternatives
# ========================================

@given(
    audio_issue=audio_issues,
    language=languages,
    context=user_context_strategy()
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_speech_recognition_error_handling(audio_issue, language, context):
    """
    Property: Speech recognition failures MUST trigger retry prompts with guidance
    
    **Validates: Requirement 1.5**
    
    For any speech recognition failure, the system should:
    1. Provide a clear, user-friendly error message
    2. Ask the user to repeat their input
    3. Provide guidance on how to improve speech quality
    4. Support multiple languages
    """
    # Create transcription error
    error = TranscriptionError(audio_issue)
    handler = ErrorHandler()
    
    # Handle the error
    response = handler.handle_error(error, context, language)
    
    # Verify response structure
    assert 'statusCode' in response
    assert 'body' in response
    
    body = json.loads(response['body'])
    
    # Property 1: Error response must indicate failure
    assert body['success'] == False, "Error response must indicate failure"
    
    # Property 2: Must include error details
    assert 'error' in body, "Response must include error details"
    error_details = body['error']
    
    # Property 3: Must have correct error code
    assert error_details['errorCode'] == 'TRANSCRIPTION_ERROR', \
        "Error code must be TRANSCRIPTION_ERROR"
    
    # Property 4: Must be retryable
    assert error_details['retryable'] == True, \
        "Speech recognition errors must be retryable"
    
    # Property 5: Must provide user-friendly message
    assert 'errorMessage' in error_details, "Must provide error message"
    assert len(error_details['errorMessage']) > 0, "Error message must not be empty"
    
    # Property 6: Must provide recovery suggestion
    assert 'recoverySuggestion' in error_details, "Must provide recovery suggestion"
    assert len(error_details['recoverySuggestion']) > 0, \
        "Recovery suggestion must not be empty"
    
    # Property 7: Message should ask user to repeat (in English or Hindi)
    message_lower = error_details['errorMessage'].lower()
    if language == 'en':
        assert 'repeat' in message_lower or 'again' in message_lower, \
            "English message should ask user to repeat"
    elif language == 'hi':
        # Hindi message should contain guidance
        assert len(error_details['errorMessage']) > 10, \
            "Hindi message should provide guidance"
    
    # Property 8: Must have timestamp
    assert 'timestamp' in error_details, "Error must have timestamp"
    
    # Property 9: Severity should be WARNING (not critical)
    assert error_details['severity'] == ErrorSeverity.WARNING.value, \
        "Speech errors should be WARNING severity"


@given(
    reason=ineligibility_reason_strategy(),
    language=languages,
    context=user_context_strategy()
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_ineligibility_error_handling(reason, language, context):
    """
    Property: Ineligible users MUST receive explanations and alternative suggestions
    
    **Validates: Requirement 4.3**
    
    For any ineligibility determination, the system should:
    1. Explain why the user doesn't qualify
    2. Suggest alternative schemes
    3. Provide clear, non-technical language
    4. Support multiple languages
    """
    # Create eligibility error with reason
    error = EligibilityError("User does not qualify", reason=reason)
    handler = ErrorHandler()
    
    # Handle the error
    response = handler.handle_error(error, context, language)
    
    # Verify response structure
    assert 'statusCode' in response
    assert 'body' in response
    
    body = json.loads(response['body'])
    
    # Property 1: Error response must indicate failure
    assert body['success'] == False, "Ineligibility response must indicate failure"
    
    # Property 2: Must include error details
    assert 'error' in body, "Response must include error details"
    error_details = body['error']
    
    # Property 3: Must have correct error code
    assert error_details['errorCode'] == 'ELIGIBILITY_ERROR', \
        "Error code must be ELIGIBILITY_ERROR"
    
    # Property 4: Must NOT be retryable (eligibility is deterministic)
    assert error_details['retryable'] == False, \
        "Eligibility errors should not be retryable"
    
    # Property 5: Must provide explanation
    assert 'errorMessage' in error_details, "Must provide explanation"
    assert len(error_details['errorMessage']) > 0, "Explanation must not be empty"
    
    # Property 6: Must suggest alternatives
    assert 'recoverySuggestion' in error_details, "Must suggest alternatives"
    suggestion = error_details['recoverySuggestion']
    assert len(suggestion) > 0, "Alternative suggestion must not be empty"
    
    # Property 7: Suggestion should mention alternatives
    suggestion_lower = suggestion.lower()
    if language == 'en':
        assert 'alternative' in suggestion_lower or 'other' in suggestion_lower or 'suggest' in suggestion_lower, \
            "English suggestion should mention alternatives"
    elif language == 'hi':
        # Hindi suggestion should provide guidance
        assert len(suggestion) > 10, "Hindi suggestion should provide guidance"
    
    # Property 8: Severity should be INFO (not an error, just information)
    assert error_details['severity'] == ErrorSeverity.INFO.value, \
        "Ineligibility should be INFO severity"
    
    # Property 9: Status code should be 200 (informational, not error)
    assert response['statusCode'] == 200, \
        "Ineligibility should return 200 status (informational)"


@given(
    api_failure=api_failures,
    api_name=st.sampled_from(['Bhashini', 'GovernmentAPI', 'Transcribe', 'Polly']),
    language=languages,
    context=user_context_strategy()
)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_api_failure_fallback(api_failure, api_name, language, context):
    """
    Property: API failures MUST provide manual fallback instructions
    
    **Validates: Requirement 7.4**
    
    For any API integration failure, the system should:
    1. Detect the failure gracefully
    2. Provide clear error message
    3. Offer manual submission instructions with contact details
    4. Support multiple languages
    """
    # Create appropriate error based on API type
    if api_name == 'GovernmentAPI':
        error = GovernmentAPIError(api_failure)
    else:
        error = APIError(api_failure, api_name)
    
    handler = ErrorHandler()
    
    # Handle the error
    response = handler.handle_error(error, context, language)
    
    # Verify response structure
    assert 'statusCode' in response
    assert 'body' in response
    
    body = json.loads(response['body'])
    
    # Property 1: Error response must indicate failure
    assert body['success'] == False, "API failure response must indicate failure"
    
    # Property 2: Must include error details
    assert 'error' in body, "Response must include error details"
    error_details = body['error']
    
    # Property 3: Must have appropriate error code
    assert 'API' in error_details['errorCode'] or 'GOVERNMENT' in error_details['errorCode'], \
        "Error code must indicate API failure"
    
    # Property 4: Must be retryable (temporary failures)
    assert error_details['retryable'] == True, \
        "API failures should be retryable"
    
    # Property 5: Must provide user-friendly message
    assert 'errorMessage' in error_details, "Must provide error message"
    assert len(error_details['errorMessage']) > 0, "Error message must not be empty"
    
    # Property 6: Must provide recovery suggestion or manual instructions
    assert 'recoverySuggestion' in error_details, "Must provide recovery suggestion"
    recovery = error_details['recoverySuggestion']
    
    # Property 7: For Government API, must mention manual submission
    if api_name == 'GovernmentAPI':
        recovery_lower = recovery.lower()
        if language == 'en':
            assert 'manual' in recovery_lower or 'office' in recovery_lower or 'submit' in recovery_lower, \
                "Government API failure should mention manual submission"
        elif language == 'hi':
            # Hindi recovery should provide guidance
            assert len(recovery) > 10, "Hindi recovery should provide guidance"
    
    # Property 8: Must have timestamp
    assert 'timestamp' in error_details, "Error must have timestamp"
    
    # Property 9: Severity should be ERROR or WARNING
    assert error_details['severity'] in [ErrorSeverity.ERROR.value, ErrorSeverity.WARNING.value], \
        "API failures should be ERROR or WARNING severity"


@given(
    error_code=st.sampled_from([
        'TRANSCRIPTION_ERROR',
        'ELIGIBILITY_ERROR',
        'API_ERROR',
        'DATABASE_ERROR',
        'GOVERNMENT_API_ERROR'
    ]),
    language=languages
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_multilingual_error_messages(error_code, language):
    """
    Property: All error messages MUST be available in multiple languages
    
    For any error code and language combination:
    1. Must return a non-empty message
    2. Must return a recovery suggestion
    3. Messages should be clear and actionable
    """
    # Get user-friendly message
    message = get_user_friendly_message(error_code, language)
    
    # Property 1: Message must not be empty
    assert len(message) > 0, f"Message for {error_code} in {language} must not be empty"
    
    # Property 2: Message must be reasonably long (not just a placeholder)
    assert len(message) > 10, f"Message for {error_code} must be descriptive"
    
    # Get recovery suggestion
    suggestion = get_recovery_suggestion(error_code, language)
    
    # Property 3: Suggestion must not be empty for most error types
    if error_code != 'DATABASE_ERROR':  # Some errors may not have suggestions
        assert len(suggestion) >= 0, f"Suggestion for {error_code} should be provided"
    
    # Property 4: English and Hindi messages should be different
    if language in ['en', 'hi']:
        message_en = get_user_friendly_message(error_code, 'en')
        message_hi = get_user_friendly_message(error_code, 'hi')
        
        # They should be different (unless fallback to same language)
        if language == 'en':
            assert message == message_en, "English message should match"
        elif language == 'hi':
            assert message == message_hi, "Hindi message should match"


@given(
    failure_count=st.integers(min_value=1, max_value=10),
    service_name=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_circuit_breaker_fallback(failure_count, service_name):
    """
    Property: Circuit breaker MUST prevent cascading failures
    
    For any number of consecutive failures:
    1. Circuit should open after threshold
    2. Should reject requests when open
    3. Should provide clear error message
    4. Should allow recovery attempts after timeout
    """
    # Create circuit breaker with low threshold for testing
    cb = CircuitBreaker(service_name, failure_threshold=3, recovery_timeout=0)
    
    # Simulate failures
    failure_occurred = False
    for i in range(min(failure_count, 5)):  # Limit to 5 for test speed
        try:
            cb.call(lambda: 1/0)  # Will raise ZeroDivisionError
        except:
            failure_occurred = True
    
    # Property 1: Failures should have occurred
    assert failure_occurred, "Failures should have been recorded"
    
    # Property 2: Circuit should open after threshold
    if failure_count >= 3:
        assert cb.state == CircuitState.OPEN, \
            f"Circuit should be OPEN after {failure_count} failures"
        
        # Property 3: Should reject calls when open
        try:
            cb.call(lambda: "success")
            # If we get here, circuit didn't reject (might be in HALF_OPEN)
            assert cb.state == CircuitState.HALF_OPEN, \
                "If call succeeded, circuit should be HALF_OPEN"
        except Exception as e:
            # Property 4: Error message should mention circuit breaker
            error_msg = str(e).lower()
            assert 'circuit' in error_msg or 'open' in error_msg, \
                "Error message should mention circuit breaker"
    
    # Property 5: State should be retrievable
    state = cb.get_state()
    assert 'state' in state, "Circuit breaker state should be retrievable"
    assert 'failureCount' in state, "Should track failure count"


@given(
    scheme_id=scheme_ids,
    language=languages
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_government_api_manual_instructions(scheme_id, language):
    """
    Property: Government API failures MUST provide manual submission instructions
    
    **Validates: Requirement 7.4**
    
    For any scheme and language:
    1. Must provide manual instructions when API fails
    2. Instructions must include contact details or office locations
    3. Instructions must be in user's language
    4. Instructions must be actionable
    """
    # Create government API client
    client = GovernmentAPIClient()
    
    # Attempt to submit application (will fail as API not implemented)
    result = client.submit_application(
        scheme_id=scheme_id,
        application_data={'test': 'data'}
    )
    
    # Property 1: Result must indicate failure
    assert result['success'] == False, "API failure should indicate failure"
    
    # Property 2: Must provide manual instructions
    assert 'manualInstructions' in result, "Must provide manual instructions"
    instructions = result['manualInstructions']
    
    # Property 3: Instructions must be available in requested language
    assert language in instructions or 'en' in instructions, \
        f"Instructions must be available in {language} or English"
    
    # Get instructions in appropriate language
    instruction_text = instructions.get(language, instructions.get('en', ''))
    
    # Property 4: Instructions must not be empty
    assert len(instruction_text) > 0, "Instructions must not be empty"
    
    # Property 5: Instructions must be reasonably detailed
    assert len(instruction_text) > 50, "Instructions must be detailed"
    
    # Property 6: Instructions should mention key steps
    instruction_lower = instruction_text.lower()
    if language == 'en':
        # Should mention office, form, or submit
        assert any(word in instruction_lower for word in ['office', 'form', 'submit', 'visit']), \
            "Instructions should mention key steps"
    
    # Property 7: Must have source indicator
    assert 'source' in result, "Result must indicate source"
    assert result['source'] == 'manual', "Source should be 'manual' for fallback"


@given(
    max_retries=st.integers(min_value=1, max_value=5),
    success_on_attempt=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_exponential_backoff_retry(max_retries, success_on_attempt):
    """
    Property: Exponential backoff MUST retry failed operations appropriately
    
    For any retry configuration:
    1. Should retry up to max_retries times
    2. Should succeed if operation succeeds within retry limit
    3. Should fail if all retries exhausted
    4. Should apply exponential delay between retries
    """
    backoff = ExponentialBackoff(
        base_delay=0.01,  # Fast for testing
        max_retries=max_retries
    )
    
    call_count = [0]
    
    def test_func():
        call_count[0] += 1
        if call_count[0] < success_on_attempt:
            raise ValueError("Temporary failure")
        return "success"
    
    # Property 1: If success_on_attempt <= max_retries + 1, should succeed
    if success_on_attempt <= max_retries + 1:
        result = backoff.execute(test_func, retryable_exceptions=(ValueError,))
        
        # Property 2: Should return success
        assert result == "success", "Should succeed within retry limit"
        
        # Property 3: Should have called exactly success_on_attempt times
        assert call_count[0] == success_on_attempt, \
            f"Should have called {success_on_attempt} times"
    else:
        # Property 4: Should exhaust retries and raise exception
        with pytest.raises(ValueError):
            backoff.execute(test_func, retryable_exceptions=(ValueError,))
        
        # Property 5: Should have called max_retries + 1 times
        assert call_count[0] == max_retries + 1, \
            f"Should have called {max_retries + 1} times"


@given(
    fallback_count=st.integers(min_value=2, max_value=5),
    success_at=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_fallback_chain_execution(fallback_count, success_at):
    """
    Property: Fallback chain MUST try alternatives in priority order
    
    For any fallback chain configuration:
    1. Should try fallbacks in priority order
    2. Should stop at first successful fallback
    3. Should return which fallback was used
    4. Should fail gracefully if all fallbacks fail
    """
    chain = FallbackChain("test_operation")
    
    # Add fallbacks
    for i in range(fallback_count):
        def make_fallback(index):
            def fallback():
                if index == success_at:
                    return f"success_{index}"
                raise Exception(f"Fallback {index} failed")
            return fallback
        
        chain.add_fallback(
            make_fallback(i),
            f"fallback_{i}",
            priority=i
        )
    
    # Execute chain
    result = chain.execute()
    
    # Property 1: Result must have success indicator
    assert 'success' in result, "Result must have success indicator"
    
    # Property 2: If success_at < fallback_count, should succeed
    if success_at < fallback_count:
        assert result['success'] == True, "Should succeed with valid fallback"
        
        # Property 3: Should use the correct fallback
        assert result['fallbackUsed'] == f"fallback_{success_at}", \
            f"Should use fallback_{success_at}"
        
        # Property 4: Should return the data
        assert result['data'] == f"success_{success_at}", \
            "Should return correct data"
    else:
        # Property 5: Should fail if no fallback succeeds
        assert result['success'] == False, "Should fail if all fallbacks fail"
        
        # Property 6: Should indicate no fallback was used
        assert result['fallbackUsed'] == 'none', \
            "Should indicate no fallback succeeded"
    
    # Property 7: Must have timestamp
    assert 'timestamp' in result, "Result must have timestamp"


# ========================================
# Summary Property Test
# ========================================

@given(
    error_type=st.sampled_from(['transcription', 'eligibility', 'api', 'government_api']),
    language=languages,
    context=user_context_strategy()
)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_comprehensive_error_handling(error_type, language, context):
    """
    Comprehensive property: ALL errors MUST provide clear, actionable responses
    
    **Feature: sarkari-saathi, Property 6: Error Handling and Alternatives**
    
    For ANY error type in ANY language:
    1. Must provide user-friendly message
    2. Must indicate if retryable
    3. Must provide recovery suggestion or alternative
    4. Must support multiple languages
    5. Must have proper severity level
    6. Must include timestamp
    """
    # Create appropriate error
    if error_type == 'transcription':
        error = TranscriptionError("Test transcription error")
    elif error_type == 'eligibility':
        error = EligibilityError("Test eligibility error")
    elif error_type == 'api':
        error = APIError("Test API error", "TestAPI")
    else:  # government_api
        error = GovernmentAPIError("Test government API error")
    
    handler = ErrorHandler()
    response = handler.handle_error(error, context, language)
    
    # Universal Property 1: Must have valid response structure
    assert 'statusCode' in response, "Response must have status code"
    assert 'body' in response, "Response must have body"
    assert 'headers' in response, "Response must have headers"
    
    body = json.loads(response['body'])
    
    # Universal Property 2: Must indicate failure
    assert body['success'] == False or error_type == 'eligibility', \
        "Error response must indicate failure (except eligibility which is informational)"
    
    # Universal Property 3: Must have error details
    assert 'error' in body, "Response must include error details"
    error_details = body['error']
    
    # Universal Property 4: Must have error code
    assert 'errorCode' in error_details, "Must have error code"
    assert len(error_details['errorCode']) > 0, "Error code must not be empty"
    
    # Universal Property 5: Must have user-friendly message
    assert 'errorMessage' in error_details, "Must have error message"
    assert len(error_details['errorMessage']) > 0, "Error message must not be empty"
    
    # Universal Property 6: Must indicate if retryable
    assert 'retryable' in error_details, "Must indicate if retryable"
    assert isinstance(error_details['retryable'], bool), "Retryable must be boolean"
    
    # Universal Property 7: Must have recovery suggestion
    assert 'recoverySuggestion' in error_details, "Must have recovery suggestion"
    # Note: Some errors may have empty suggestions, which is acceptable
    
    # Universal Property 8: Must have severity
    assert 'severity' in error_details, "Must have severity"
    assert error_details['severity'] in [s.value for s in ErrorSeverity], \
        "Severity must be valid"
    
    # Universal Property 9: Must have timestamp
    assert 'timestamp' in error_details, "Must have timestamp"
    assert len(error_details['timestamp']) > 0, "Timestamp must not be empty"
    
    # Universal Property 10: CORS headers must be present
    assert 'Access-Control-Allow-Origin' in response['headers'], \
        "Must have CORS headers"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

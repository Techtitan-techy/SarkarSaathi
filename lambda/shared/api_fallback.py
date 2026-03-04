"""
SarkariSaathi - API Fallback Strategies

This module implements circuit breaker pattern, exponential backoff,
and fallback chains for external API calls.

Requirements: 7.2, 7.4, 10.4
"""

import time
import json
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import requests


# ========================================
# Circuit Breaker States
# ========================================

class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


# ========================================
# Circuit Breaker
# ========================================

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external API calls
    
    Prevents cascading failures by stopping requests to failing services
    and allowing them time to recover.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Name of the service/API
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Successful calls needed to close circuit from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.utcnow()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                print(f"Circuit breaker {self.name}: Transitioning to HALF_OPEN")
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN. Service unavailable.")
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Record success
            self._on_success()
            
            return result
            
        except Exception as e:
            # Record failure
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                print(f"Circuit breaker {self.name}: Transitioning to CLOSED")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            # Immediately open circuit if failure in half-open state
            self.state = CircuitState.OPEN
            print(f"Circuit breaker {self.name}: Transitioning to OPEN (failure in HALF_OPEN)")
        elif self.failure_count >= self.failure_threshold:
            # Open circuit if threshold exceeded
            self.state = CircuitState.OPEN
            print(f"Circuit breaker {self.name}: Transitioning to OPEN (threshold exceeded)")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failureCount': self.failure_count,
            'successCount': self.success_count,
            'lastFailureTime': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'lastStateChange': self.last_state_change.isoformat()
        }


# ========================================
# Exponential Backoff
# ========================================

class ExponentialBackoff:
    """
    Exponential backoff strategy for retrying failed requests
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5,
        exponential_base: float = 2.0
    ):
        """
        Initialize exponential backoff
        
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            max_retries: Maximum number of retry attempts
            exponential_base: Base for exponential calculation
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.exponential_base = exponential_base
    
    def execute(
        self,
        func: Callable,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            retryable_exceptions: Tuple of exceptions that should trigger retry
        
        Returns:
            Function result
        
        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt >= self.max_retries:
                    print(f"Max retries ({self.max_retries}) exhausted")
                    raise e
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                print(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay}s delay")
                time.sleep(delay)
        
        # Should not reach here, but raise last exception if it does
        if last_exception:
            raise last_exception


# ========================================
# Fallback Chain
# ========================================

class FallbackChain:
    """
    Implements fallback chain: Primary → Secondary → Cached → Manual
    """
    
    def __init__(self, name: str):
        """
        Initialize fallback chain
        
        Args:
            name: Name of the service/operation
        """
        self.name = name
        self.fallback_functions: List[Dict[str, Any]] = []
    
    def add_fallback(
        self,
        func: Callable,
        name: str,
        priority: int = 0
    ):
        """
        Add a fallback function to the chain
        
        Args:
            func: Fallback function
            name: Name of the fallback (e.g., "primary", "secondary", "cached")
            priority: Priority (lower = higher priority)
        """
        self.fallback_functions.append({
            'func': func,
            'name': name,
            'priority': priority
        })
        
        # Sort by priority
        self.fallback_functions.sort(key=lambda x: x['priority'])
    
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute fallback chain
        
        Args:
            *args, **kwargs: Arguments to pass to fallback functions
        
        Returns:
            Dict with result and metadata about which fallback was used
        """
        last_exception = None
        
        for fallback in self.fallback_functions:
            try:
                print(f"Attempting {fallback['name']} for {self.name}")
                result = fallback['func'](*args, **kwargs)
                
                return {
                    'success': True,
                    'data': result,
                    'fallbackUsed': fallback['name'],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                
            except Exception as e:
                last_exception = e
                print(f"{fallback['name']} failed: {str(e)}")
                continue
        
        # All fallbacks failed
        return {
            'success': False,
            'error': str(last_exception) if last_exception else "All fallbacks failed",
            'fallbackUsed': 'none',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


# ========================================
# API Client with Fallback
# ========================================

class ResilientAPIClient:
    """
    API client with circuit breaker, exponential backoff, and fallback support
    """
    
    def __init__(self, service_name: str):
        """
        Initialize resilient API client
        
        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.circuit_breaker = CircuitBreaker(
            name=service_name,
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=2
        )
        self.backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            max_retries=3
        )
        self.s3_client = boto3.client('s3', region_name='ap-south-1')
        self.cache_bucket = 'sarkari-saathi-cache'
    
    def call_with_fallback(
        self,
        primary_func: Callable,
        cache_key: Optional[str] = None,
        manual_instructions: Optional[Dict[str, str]] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call API with full fallback chain
        
        Args:
            primary_func: Primary API function
            cache_key: S3 cache key for fallback
            manual_instructions: Manual instructions if all else fails
            *args, **kwargs: Arguments for primary function
        
        Returns:
            Dict with result and metadata
        """
        # Try primary with circuit breaker and exponential backoff
        try:
            result = self.circuit_breaker.call(
                lambda: self.backoff.execute(primary_func, *args, **kwargs)
            )
            return {
                'success': True,
                'data': result,
                'source': 'primary',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as primary_error:
            print(f"Primary API failed: {str(primary_error)}")
        
        # Try cached data
        if cache_key:
            try:
                cached_data = self._get_cached_data(cache_key)
                if cached_data:
                    return {
                        'success': True,
                        'data': cached_data,
                        'source': 'cache',
                        'warning': 'Using cached data. Information may be outdated.',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
            except Exception as cache_error:
                print(f"Cache retrieval failed: {str(cache_error)}")
        
        # Return manual instructions as last resort
        if manual_instructions:
            return {
                'success': False,
                'source': 'manual',
                'manualInstructions': manual_instructions,
                'message': 'Service unavailable. Please follow manual instructions.',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        
        # Complete failure
        return {
            'success': False,
            'source': 'none',
            'error': 'Service unavailable and no fallback available',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Retrieve cached data from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.cache_bucket,
                Key=cache_key
            )
            data = response['Body'].read().decode('utf-8')
            return json.loads(data)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise e
    
    def cache_data(self, cache_key: str, data: Any, ttl_hours: int = 24):
        """Cache data to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.cache_bucket,
                Key=cache_key,
                Body=json.dumps(data),
                ContentType='application/json',
                Metadata={
                    'cached_at': datetime.utcnow().isoformat(),
                    'ttl_hours': str(ttl_hours)
                }
            )
            print(f"Cached data with key: {cache_key}")
        except Exception as e:
            print(f"Failed to cache data: {str(e)}")


# ========================================
# Service-Specific Clients
# ========================================

class BhashiniClient(ResilientAPIClient):
    """Resilient client for Bhashini API"""
    
    def __init__(self):
        super().__init__("Bhashini")
        self.api_url = "https://dhruva-api.bhashini.gov.in/services"
        self.api_key = None  # Load from environment or secrets manager
    
    def transcribe(
        self,
        audio_data: bytes,
        language: str
    ) -> Dict[str, Any]:
        """
        Transcribe audio with fallback to cached results
        
        Args:
            audio_data: Audio data bytes
            language: Language code
        
        Returns:
            Transcription result
        """
        import hashlib
        cache_key = f"transcription/{hashlib.md5(audio_data).hexdigest()}_{language}.json"
        
        def primary_call():
            # Implement actual Bhashini API call
            # This is a placeholder
            response = requests.post(
                f"{self.api_url}/asr",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"audio": audio_data.hex(), "language": language},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        manual_instructions = {
            'en': "Speech recognition is temporarily unavailable. Please type your message or try again later.",
            'hi': "वाक् पहचान अस्थायी रूप से अनुपलब्ध है। कृपया अपना संदेश टाइप करें या बाद में पुनः प्रयास करें।"
        }
        
        return self.call_with_fallback(
            primary_call,
            cache_key=cache_key,
            manual_instructions=manual_instructions
        )


class GovernmentAPIClient(ResilientAPIClient):
    """Resilient client for Government APIs"""
    
    def __init__(self):
        super().__init__("GovernmentAPI")
    
    def submit_application(
        self,
        scheme_id: str,
        application_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit application with fallback to manual instructions
        
        Args:
            scheme_id: Scheme identifier
            application_data: Application form data
        
        Returns:
            Submission result with tracking number or manual instructions
        """
        def primary_call():
            # Implement actual government API call
            # This is a placeholder
            raise Exception("Government API not implemented yet")
        
        # Get manual submission instructions for the scheme
        manual_instructions = self._get_manual_instructions(scheme_id)
        
        return self.call_with_fallback(
            primary_call,
            manual_instructions=manual_instructions
        )
    
    def _get_manual_instructions(self, scheme_id: str) -> Dict[str, str]:
        """Get manual submission instructions for a scheme"""
        # This would typically fetch from database
        return {
            'en': f"To submit your application manually:\n"
                  f"1. Visit your nearest government office\n"
                  f"2. Ask for application form for scheme {scheme_id}\n"
                  f"3. Fill the form and submit with required documents\n"
                  f"4. Collect acknowledgment receipt",
            'hi': f"अपना आवेदन मैन्युअल रूप से जमा करने के लिए:\n"
                  f"1. अपने निकटतम सरकारी कार्यालय में जाएं\n"
                  f"2. योजना {scheme_id} के लिए आवेदन पत्र मांगें\n"
                  f"3. फॉर्म भरें और आवश्यक दस्तावेजों के साथ जमा करें\n"
                  f"4. पावती रसीद एकत्र करें"
        }
    
    def get_scheme_data(
        self,
        scheme_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get scheme data with fallback to cached version
        
        Args:
            scheme_id: Scheme identifier
            use_cache: Whether to use cached data as fallback
        
        Returns:
            Scheme data
        """
        cache_key = f"schemes/{scheme_id}.json" if use_cache else None
        
        def primary_call():
            # Implement actual government API call
            # This is a placeholder
            raise Exception("Government API not implemented yet")
        
        manual_instructions = {
            'en': f"Scheme information is temporarily unavailable. Please visit the official government website or contact the helpline.",
            'hi': f"योजना की जानकारी अस्थायी रूप से अनुपलब्ध है। कृपया आधिकारिक सरकारी वेबसाइट पर जाएं या हेल्पलाइन से संपर्क करें।"
        }
        
        result = self.call_with_fallback(
            primary_call,
            cache_key=cache_key,
            manual_instructions=manual_instructions
        )
        
        # Add staleness warning if using cached data
        if result.get('source') == 'cache':
            result['warning'] = {
                'en': "This information may be outdated. Please verify with official sources.",
                'hi': "यह जानकारी पुरानी हो सकती है। कृपया आधिकारिक स्रोतों से सत्यापित करें।"
            }
        
        return result


# ========================================
# Global Instances
# ========================================

# Create global instances for easy import
bhashini_client = BhashiniClient()
government_api_client = GovernmentAPIClient()

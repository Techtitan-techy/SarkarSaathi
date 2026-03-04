"""
SarkariSaathi - Centralized Error Handler

This module provides centralized error handling, logging, and recovery mechanisms
for all Lambda functions in the SarkariSaathi application.

Requirements: 1.5, 4.3, 7.4
"""

import json
import traceback
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, BotoCoreError


# ========================================
# Error Severity Levels
# ========================================

class ErrorSeverity(str, Enum):
    """Error severity levels for logging and alerting"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ========================================
# Error Types
# ========================================

class SarkariSaathiError(Exception):
    """Base exception for SarkariSaathi application"""
    def __init__(
        self,
        message: str,
        error_code: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        retryable: bool = False,
        user_message: Optional[Dict[str, str]] = None,
        recovery_suggestion: Optional[Dict[str, str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.retryable = retryable
        self.user_message = user_message or {}
        self.recovery_suggestion = recovery_suggestion or {}
        self.timestamp = datetime.utcnow().isoformat() + 'Z'


class TranscriptionError(SarkariSaathiError):
    """Error during speech-to-text processing"""
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(
            message=message,
            error_code="TRANSCRIPTION_ERROR",
            severity=ErrorSeverity.WARNING,
            retryable=retryable,
            user_message={
                'en': "I couldn't understand your speech clearly. Could you please repeat that?",
                'hi': "मैं आपकी बात स्पष्ट रूप से नहीं समझ सका। क्या आप कृपया दोहरा सकते हैं?"
            },
            recovery_suggestion={
                'en': "Please speak clearly and reduce background noise",
                'hi': "कृपया स्पष्ट रूप से बोलें और पृष्ठभूमि शोर कम करें"
            }
        )


class EligibilityError(SarkariSaathiError):
    """Error during eligibility assessment"""
    def __init__(self, message: str, reason: Optional[Dict[str, str]] = None):
        super().__init__(
            message=message,
            error_code="ELIGIBILITY_ERROR",
            severity=ErrorSeverity.INFO,
            retryable=False,
            user_message=reason or {
                'en': "Based on the information provided, you don't qualify for this scheme.",
                'hi': "प्रदान की गई जानकारी के आधार पर, आप इस योजना के लिए योग्य नहीं हैं।"
            },
            recovery_suggestion={
                'en': "Let me suggest alternative schemes that you may qualify for",
                'hi': "मैं वैकल्पिक योजनाओं का सुझाव देता हूं जिनके लिए आप योग्य हो सकते हैं"
            }
        )


class APIError(SarkariSaathiError):
    """Error during external API calls"""
    def __init__(self, message: str, api_name: str, retryable: bool = True):
        super().__init__(
            message=message,
            error_code=f"API_ERROR_{api_name.upper()}",
            severity=ErrorSeverity.ERROR,
            retryable=retryable,
            user_message={
                'en': f"We're experiencing technical difficulties with {api_name}. Please try again in a moment.",
                'hi': f"{api_name} के साथ तकनीकी कठिनाइयों का सामना कर रहे हैं। कृपया कुछ देर में पुनः प्रयास करें।"
            },
            recovery_suggestion={
                'en': "Using cached data or alternative service",
                'hi': "कैश्ड डेटा या वैकल्पिक सेवा का उपयोग कर रहे हैं"
            }
        )


class DatabaseError(SarkariSaathiError):
    """Error during database operations"""
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            severity=ErrorSeverity.ERROR,
            retryable=retryable,
            user_message={
                'en': "We're having trouble accessing your information. Please try again.",
                'hi': "हमें आपकी जानकारी तक पहुंचने में परेशानी हो रही है। कृपया पुनः प्रयास करें।"
            }
        )


class ValidationError(SarkariSaathiError):
    """Error during input validation"""
    def __init__(self, message: str, field: str):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.WARNING,
            retryable=False,
            user_message={
                'en': f"The {field} you provided is invalid. Please provide correct information.",
                'hi': f"आपके द्वारा प्रदान की गई {field} अमान्य है। कृपया सही जानकारी प्रदान करें।"
            }
        )


class GovernmentAPIError(SarkariSaathiError):
    """Error when government API is unavailable"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="GOVERNMENT_API_ERROR",
            severity=ErrorSeverity.WARNING,
            retryable=True,
            user_message={
                'en': "Government services are temporarily unavailable. I'll provide you with manual submission instructions.",
                'hi': "सरकारी सेवाएं अस्थायी रूप से अनुपलब्ध हैं। मैं आपको मैनुअल सबमिशन निर्देश प्रदान करूंगा।"
            },
            recovery_suggestion={
                'en': "You can submit your application manually at the nearest government office",
                'hi': "आप अपना आवेदन निकटतम सरकारी कार्यालय में मैन्युअल रूप से जमा कर सकते हैं"
            }
        )


# ========================================
# CloudWatch Logger
# ========================================

class CloudWatchLogger:
    """Centralized logging to CloudWatch"""
    
    def __init__(self):
        self.logs_client = boto3.client('logs', region_name='ap-south-1')
        self.log_group = '/aws/lambda/sarkari-saathi'
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ):
        """Log error to CloudWatch with context"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': severity.value,
            'errorType': type(error).__name__,
            'errorMessage': str(error),
            'context': context
        }
        
        # Add custom error details if available
        if isinstance(error, SarkariSaathiError):
            log_entry.update({
                'errorCode': error.error_code,
                'retryable': error.retryable,
                'userMessage': error.user_message,
                'recoverySuggestion': error.recovery_suggestion
            })
        
        # Add stack trace for ERROR and CRITICAL
        if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            log_entry['stackTrace'] = traceback.format_exc()
        
        # Print to CloudWatch Logs (Lambda automatically captures stdout)
        print(json.dumps(log_entry))
        
        return log_entry
    
    def log_info(self, message: str, context: Dict[str, Any] = None):
        """Log informational message"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': ErrorSeverity.INFO.value,
            'message': message,
            'context': context or {}
        }
        print(json.dumps(log_entry))
    
    def log_warning(self, message: str, context: Dict[str, Any] = None):
        """Log warning message"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': ErrorSeverity.WARNING.value,
            'message': message,
            'context': context or {}
        }
        print(json.dumps(log_entry))


# ========================================
# Error Handler
# ========================================

class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self):
        self.logger = CloudWatchLogger()
    
    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Handle error and return appropriate response
        
        Args:
            error: The exception that occurred
            context: Context information (user_id, session_id, function_name, etc.)
            language: User's preferred language for error messages
        
        Returns:
            Dict containing error response with user-friendly message
        """
        # Determine severity
        severity = ErrorSeverity.ERROR
        if isinstance(error, SarkariSaathiError):
            severity = error.severity
        elif isinstance(error, (ClientError, BotoCoreError)):
            severity = ErrorSeverity.ERROR
        elif isinstance(error, ValueError):
            severity = ErrorSeverity.WARNING
        
        # Log the error
        self.logger.log_error(error, context, severity)
        
        # Build response
        if isinstance(error, SarkariSaathiError):
            return self._build_custom_error_response(error, language)
        elif isinstance(error, ClientError):
            return self._handle_aws_error(error, language)
        else:
            return self._build_generic_error_response(error, language)
    
    def _build_custom_error_response(
        self,
        error: SarkariSaathiError,
        language: str
    ) -> Dict[str, Any]:
        """Build response for custom SarkariSaathi errors"""
        user_message = error.user_message.get(language, error.user_message.get('en', str(error)))
        recovery = error.recovery_suggestion.get(language, error.recovery_suggestion.get('en', ''))
        
        return {
            'statusCode': 200 if error.severity == ErrorSeverity.INFO else 500,
            'headers': self._get_cors_headers(),
            'body': json.dumps({
                'success': False,
                'error': {
                    'errorCode': error.error_code,
                    'errorMessage': user_message,
                    'severity': error.severity.value,
                    'retryable': error.retryable,
                    'recoverySuggestion': recovery,
                    'timestamp': error.timestamp
                }
            })
        }
    
    def _handle_aws_error(self, error: ClientError, language: str) -> Dict[str, Any]:
        """Handle AWS service errors"""
        error_code = error.response['Error']['Code']
        
        # Map AWS errors to user-friendly messages
        error_messages = {
            'ResourceNotFoundException': {
                'en': "The requested information was not found.",
                'hi': "अनुरोधित जानकारी नहीं मिली।"
            },
            'ThrottlingException': {
                'en': "Too many requests. Please try again in a moment.",
                'hi': "बहुत सारे अनुरोध। कृपया कुछ देर में पुनः प्रयास करें।"
            },
            'ProvisionedThroughputExceededException': {
                'en': "Service is busy. Please try again shortly.",
                'hi': "सेवा व्यस्त है। कृपया शीघ्र ही पुनः प्रयास करें।"
            },
            'AccessDeniedException': {
                'en': "Access denied. Please contact support.",
                'hi': "पहुंच अस्वीकृत। कृपया सहायता से संपर्क करें।"
            }
        }
        
        message = error_messages.get(error_code, {
            'en': "A technical error occurred. Please try again.",
            'hi': "एक तकनीकी त्रुटि हुई। कृपया पुनः प्रयास करें।"
        })
        
        retryable = error_code in ['ThrottlingException', 'ProvisionedThroughputExceededException']
        status_code = 429 if error_code == 'ThrottlingException' else 500
        
        return {
            'statusCode': status_code,
            'headers': self._get_cors_headers(),
            'body': json.dumps({
                'success': False,
                'error': {
                    'errorCode': error_code,
                    'errorMessage': message.get(language, message['en']),
                    'severity': ErrorSeverity.ERROR.value,
                    'retryable': retryable,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            })
        }
    
    def _build_generic_error_response(
        self,
        error: Exception,
        language: str
    ) -> Dict[str, Any]:
        """Build response for generic errors"""
        messages = {
            'en': "An unexpected error occurred. Our team has been notified.",
            'hi': "एक अप्रत्याशित त्रुटि हुई। हमारी टीम को सूचित कर दिया गया है।"
        }
        
        return {
            'statusCode': 500,
            'headers': self._get_cors_headers(),
            'body': json.dumps({
                'success': False,
                'error': {
                    'errorCode': 'INTERNAL_ERROR',
                    'errorMessage': messages.get(language, messages['en']),
                    'severity': ErrorSeverity.ERROR.value,
                    'retryable': False,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            })
        }
    
    def _get_cors_headers(self) -> Dict[str, str]:
        """Get CORS headers for API responses"""
        return {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }


# ========================================
# Decorator for Error Handling
# ========================================

def with_error_handling(language_field: str = 'language'):
    """
    Decorator to wrap Lambda handlers with error handling
    
    Args:
        language_field: Field name in event to extract user's language
    
    Usage:
        @with_error_handling(language_field='preferredLanguage')
        def lambda_handler(event, context):
            # Your handler code
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(event, context):
            error_handler = ErrorHandler()
            
            try:
                # Extract language from event
                language = 'en'
                if isinstance(event, dict):
                    body = event.get('body', {})
                    if isinstance(body, str):
                        try:
                            body = json.loads(body)
                        except:
                            pass
                    if isinstance(body, dict):
                        language = body.get(language_field, 'en')
                
                # Execute the function
                return func(event, context)
                
            except Exception as e:
                # Build context for logging
                error_context = {
                    'functionName': context.function_name if context else 'unknown',
                    'requestId': context.request_id if context else 'unknown',
                    'event': event
                }
                
                # Handle and return error response
                return error_handler.handle_error(e, error_context, language)
        
        return wrapper
    return decorator


# ========================================
# Utility Functions
# ========================================

def get_user_friendly_message(
    error_code: str,
    language: str = 'en',
    **kwargs
) -> str:
    """
    Get user-friendly error message for a given error code
    
    Args:
        error_code: Error code
        language: User's preferred language
        **kwargs: Additional parameters for message formatting
    
    Returns:
        User-friendly error message
    """
    messages = {
        'TRANSCRIPTION_ERROR': {
            'en': "I couldn't understand your speech clearly. Could you please repeat that?",
            'hi': "मैं आपकी बात स्पष्ट रूप से नहीं समझ सका। क्या आप कृपया दोहरा सकते हैं?"
        },
        'ELIGIBILITY_ERROR': {
            'en': "Based on the information provided, you don't qualify for this scheme.",
            'hi': "प्रदान की गई जानकारी के आधार पर, आप इस योजना के लिए योग्य नहीं हैं।"
        },
        'API_ERROR': {
            'en': "We're experiencing technical difficulties. Please try again in a moment.",
            'hi': "हम तकनीकी कठिनाइयों का सामना कर रहे हैं। कृपया कुछ देर में पुनः प्रयास करें।"
        },
        'DATABASE_ERROR': {
            'en': "We're having trouble accessing your information. Please try again.",
            'hi': "हमें आपकी जानकारी तक पहुंचने में परेशानी हो रही है। कृपया पुनः प्रयास करें।"
        },
        'GOVERNMENT_API_ERROR': {
            'en': "Government services are temporarily unavailable. I'll provide you with manual submission instructions.",
            'hi': "सरकारी सेवाएं अस्थायी रूप से अनुपलब्ध हैं। मैं आपको मैनुअल सबमिशन निर्देश प्रदान करूंगा।"
        }
    }
    
    message_dict = messages.get(error_code, {
        'en': "An error occurred. Please try again.",
        'hi': "एक त्रुटि हुई। कृपया पुनः प्रयास करें।"
    })
    
    return message_dict.get(language, message_dict.get('en', 'An error occurred'))


def get_recovery_suggestion(error_code: str, language: str = 'en') -> str:
    """Get recovery suggestion for an error"""
    suggestions = {
        'TRANSCRIPTION_ERROR': {
            'en': "Please speak clearly and reduce background noise",
            'hi': "कृपया स्पष्ट रूप से बोलें और पृष्ठभूमि शोर कम करें"
        },
        'ELIGIBILITY_ERROR': {
            'en': "Let me suggest alternative schemes that you may qualify for",
            'hi': "मैं वैकल्पिक योजनाओं का सुझाव देता हूं जिनके लिए आप योग्य हो सकते हैं"
        },
        'API_ERROR': {
            'en': "Using cached data or alternative service",
            'hi': "कैश्ड डेटा या वैकल्पिक सेवा का उपयोग कर रहे हैं"
        },
        'GOVERNMENT_API_ERROR': {
            'en': "You can submit your application manually at the nearest government office",
            'hi': "आप अपना आवेदन निकटतम सरकारी कार्यालय में मैन्युअल रूप से जमा कर सकते हैं"
        }
    }
    
    suggestion_dict = suggestions.get(error_code, {
        'en': "Please try again or contact support",
        'hi': "कृपया पुनः प्रयास करें या सहायता से संपर्क करें"
    })
    
    return suggestion_dict.get(language, suggestion_dict.get('en', ''))


# ========================================
# Global Error Handler Instance
# ========================================

# Create a global instance for easy import
error_handler = ErrorHandler()
logger = CloudWatchLogger()

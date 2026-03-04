"""
Integration Tests for SMS/IVR Flows

Tests SMS message parsing, response generation, IVR DTMF navigation,
and callback scheduling functionality.

**Validates: Requirement 8.3** - Accessibility and feature phone support
"""

import json
import pytest
import boto3
from moto import mock_aws
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import time
from unittest.mock import Mock, patch, MagicMock

# Import handlers
import sms_handler
import ivr_handler
import conversation_manager


@pytest.fixture
def mock_aws_environment(monkeypatch):
    """Set up mock AWS environment variables."""
    monkeypatch.setenv('AWS_REGION', 'ap-south-1')
    monkeypatch.setenv('SMS_CONVERSATIONS_TABLE', 'test-sms-conversations')
    monkeypatch.setenv('SESSIONS_TABLE', 'test-sessions')
    monkeypatch.setenv('USERS_TABLE', 'test-users')
    monkeypatch.setenv('IVR_CALLBACKS_TABLE', 'test-ivr-callbacks')
    monkeypatch.setenv('PINPOINT_APP_ID', 'test-app-id')
    monkeypatch.setenv('CONVERSATION_MANAGER_FUNCTION', 'test-conversation-manager')
    monkeypatch.setenv('CONNECT_INSTANCE_ID', 'test-connect-instance')
    monkeypatch.setenv('TTS_CACHE_BUCKET', 'test-tts-cache')


@pytest.fixture
@mock_aws
def dynamodb_tables(mock_aws_environment):
    """Create mock DynamoDB tables for testing."""
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    
    # Create SMS Conversations table
    sms_table = dynamodb.create_table(
        TableName='test-sms-conversations',
        KeySchema=[
            {'AttributeName': 'phoneNumber', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'phoneNumber', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create Sessions table
    sessions_table = dynamodb.create_table(
        TableName='test-sessions',
        KeySchema=[
            {'AttributeName': 'sessionId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'sessionId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create Users table
    users_table = dynamodb.create_table(
        TableName='test-users',
        KeySchema=[
            {'AttributeName': 'userId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'phoneNumber', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'phoneNumber-index',
                'KeySchema': [
                    {'AttributeName': 'phoneNumber', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create IVR Callbacks table
    callbacks_table = dynamodb.create_table(
        TableName='test-ivr-callbacks',
        KeySchema=[
            {'AttributeName': 'callbackId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'callbackId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    return {
        'sms_conversations': sms_table,
        'sessions': sessions_table,
        'users': users_table,
        'callbacks': callbacks_table
    }


# ============================================================================
# SMS MESSAGE PARSING AND RESPONSE GENERATION TESTS
# ============================================================================

class TestSMSMessageParsing:
    """Test SMS message parsing and response generation."""
    
    def test_parse_incoming_sms_english(self, dynamodb_tables, mock_aws_environment):
        """Test parsing English SMS message."""
        with patch.object(sms_handler, 'lambda_client') as mock_lambda, \
             patch.object(sms_handler, 'pinpoint') as mock_pinpoint:
            
            # Mock conversation manager response
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'Welcome to SarkariSaathi! I can help you discover government schemes.',
                        'nextState': 'ProfileCollection'
                    })
                }).encode())
            }
            
            # Mock Pinpoint SMS send
            mock_pinpoint.send_messages.return_value = {
                'MessageResponse': {
                    'Result': {
                        '+919876543210': {
                            'DeliveryStatus': 'SUCCESSFUL',
                            'MessageId': 'test-msg-id',
                            'StatusCode': 200
                        }
                    }
                }
            }
            
            # Test incoming SMS
            event = {
                'body': json.dumps({
                    'action': 'receiveSms',
                    'phoneNumber': '+919876543210',
                    'message': 'Hello, I need help with government schemes',
                    'language': 'en'
                })
            }
            
            response = sms_handler.lambda_handler(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'sessionId' in body
            assert body['messagesSent'] >= 1
            
            # Verify conversation manager was called
            mock_lambda.invoke.assert_called_once()
            call_args = json.loads(mock_lambda.invoke.call_args[1]['Payload'])
            assert call_args['userMessage'] == 'Hello, I need help with government schemes'
            assert call_args['language'] == 'en'
            assert call_args['channel'] == 'sms'
    
    def test_parse_incoming_sms_hindi(self, dynamodb_tables, mock_aws_environment):
        """Test parsing Hindi SMS message."""
        with patch.object(sms_handler, 'lambda_client') as mock_lambda, \
             patch.object(sms_handler, 'pinpoint') as mock_pinpoint:
            
            # Mock conversation manager response in Hindi
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'नमस्ते! SarkariSaathi में आपका स्वागत है।',
                        'nextState': 'ProfileCollection'
                    })
                }).encode())
            }
            
            mock_pinpoint.send_messages.return_value = {
                'MessageResponse': {
                    'Result': {
                        '+919876543210': {
                            'DeliveryStatus': 'SUCCESSFUL',
                            'MessageId': 'test-msg-id',
                            'StatusCode': 200
                        }
                    }
                }
            }
            
            event = {
                'body': json.dumps({
                    'action': 'receiveSms',
                    'phoneNumber': '+919876543210',
                    'message': 'नमस्ते, मुझे सरकारी योजनाओं की जानकारी चाहिए',
                    'language': 'hi'
                })
            }
            
            response = sms_handler.lambda_handler(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'sessionId' in body
    
    def test_sms_message_chunking(self, dynamodb_tables, mock_aws_environment):
        """Test that long SMS messages are properly chunked."""
        long_message = "This is a very long message that exceeds the standard SMS length of 160 characters. " * 5
        
        chunks = sms_handler.chunk_message(long_message, chunk_size=160)
        
        # Verify chunks are created
        assert len(chunks) > 1
        
        # Verify each chunk is within size limit (accounting for part indicators)
        for chunk in chunks:
            assert len(chunk) <= 170  # Allow some extra for part indicators like "(1/3)"
        
        # Verify part indicators are present
        assert "(1/" in chunks[0]
        assert f"({len(chunks)}/{len(chunks)})" in chunks[-1]
    
    def test_sms_rate_limiting(self, dynamodb_tables, mock_aws_environment):
        """Test SMS rate limiting prevents spam."""
        phone_number = '+919876543210'
        
        # Simulate multiple messages within rate limit window
        table = dynamodb_tables['sms_conversations']
        current_time = datetime.utcnow()
        
        # Add 10 messages (at the limit)
        for i in range(10):
            timestamp = (current_time - timedelta(seconds=i)).isoformat()
            table.put_item(Item={
                'phoneNumber': phone_number,
                'timestamp': timestamp,
                'messageId': f'msg-{i}',
                'message': f'Test message {i}',
                'direction': 'inbound',
                'sessionId': 'test-session',
                'language': 'en'
            })
        
        # Check rate limit
        is_allowed, remaining = sms_handler.check_rate_limit(phone_number)
        
        assert not is_allowed
        assert remaining == 0
    
    def test_sms_conversation_history_storage(self, dynamodb_tables, mock_aws_environment):
        """Test that SMS messages are stored in conversation history."""
        phone_number = '+919876543210'
        message = 'Test message'
        session_id = 'test-session-123'
        
        # Store message
        sms_handler.store_sms_message(phone_number, message, 'inbound', session_id, 'en')
        
        # Retrieve conversation history
        event = {
            'body': json.dumps({
                'action': 'getConversationHistory',
                'phoneNumber': phone_number,
                'limit': 10
            })
        }
        
        response = sms_handler.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['messageCount'] >= 1
        assert any(msg['message'] == message for msg in body['messages'])


# ============================================================================
# IVR DTMF NAVIGATION TESTS
# ============================================================================

class TestIVRDTMFNavigation:
    """Test IVR DTMF (touch-tone) navigation."""
    
    def test_ivr_main_menu_presentation(self, dynamodb_tables, mock_aws_environment):
        """Test IVR presents main menu on incoming call."""
        # Create a session in DynamoDB first
        sessions_table = dynamodb_tables['sessions']
        contact_id = 'test-contact-123'
        phone_number = '+919876543210'
        
        sessions_table.put_item(Item={
            'sessionId': f'ivr-{contact_id}',
            'userId': f'phone-{phone_number}',
            'phoneNumber': phone_number,
            'contactId': contact_id,
            'channel': 'ivr',
            'currentState': 'Welcome',
            'context': json.dumps({}),
            'language': 'en',
            'messages': [],
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        })
        
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': phone_number},
                    'ContactId': contact_id
                },
                'Parameters': {
                    'action': 'handleIncomingCall'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert 'shouldEnd' in response
        assert response['shouldEnd'] is False
        assert 'nextAction' in response
        assert response['nextAction'] == 'waitForDtmf'
        
        # Verify menu options are present
        message = response['message']
        assert '1' in message  # Scheme discovery
        assert '2' in message  # Eligibility check
        assert '3' in message  # Application help
        assert '4' in message  # Speak to agent
    
    def test_ivr_dtmf_scheme_discovery(self, dynamodb_tables, mock_aws_environment):
        """Test DTMF input '1' for scheme discovery."""
        with patch.object(ivr_handler, 'lambda_client') as mock_lambda:
            
            # Mock conversation manager response
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'Let me help you discover schemes.',
                        'nextState': 'SchemeDiscovery'
                    })
                }).encode())
            }
            
            event = {
                'Details': {
                    'ContactData': {
                        'CustomerEndpoint': {'Address': '+919876543210'},
                        'ContactId': 'test-contact-123'
                    },
                    'Parameters': {
                        'action': 'processDtmfInput',
                        'dtmfInput': '1'
                    }
                }
            }
            
            response = ivr_handler.lambda_handler(event, None)
            
            assert 'message' in response
            assert response['shouldEnd'] is False
            
            # Verify conversation manager was called with correct action
            mock_lambda.invoke.assert_called_once()
            call_args = json.loads(mock_lambda.invoke.call_args[1]['Payload'])
            assert call_args['dtmfAction'] == 'scheme_discovery'
    
    def test_ivr_dtmf_eligibility_check(self, dynamodb_tables, mock_aws_environment):
        """Test DTMF input '2' for eligibility check."""
        with patch.object(ivr_handler, 'lambda_client') as mock_lambda:
            
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'Let me check your eligibility.',
                        'nextState': 'EligibilityCheck'
                    })
                }).encode())
            }
            
            event = {
                'Details': {
                    'ContactData': {
                        'CustomerEndpoint': {'Address': '+919876543210'},
                        'ContactId': 'test-contact-123'
                    },
                    'Parameters': {
                        'action': 'processDtmfInput',
                        'dtmfInput': '2'
                    }
                }
            }
            
            response = ivr_handler.lambda_handler(event, None)
            
            assert 'message' in response
            call_args = json.loads(mock_lambda.invoke.call_args[1]['Payload'])
            assert call_args['dtmfAction'] == 'eligibility_check'
    
    def test_ivr_dtmf_application_help(self, dynamodb_tables, mock_aws_environment):
        """Test DTMF input '3' for application guidance."""
        with patch.object(ivr_handler, 'lambda_client') as mock_lambda:
            
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'I can help you with the application.',
                        'nextState': 'ApplicationGuidance'
                    })
                }).encode())
            }
            
            event = {
                'Details': {
                    'ContactData': {
                        'CustomerEndpoint': {'Address': '+919876543210'},
                        'ContactId': 'test-contact-123'
                    },
                    'Parameters': {
                        'action': 'processDtmfInput',
                        'dtmfInput': '3'
                    }
                }
            }
            
            response = ivr_handler.lambda_handler(event, None)
            
            assert 'message' in response
            call_args = json.loads(mock_lambda.invoke.call_args[1]['Payload'])
            assert call_args['dtmfAction'] == 'application_guidance'
    
    def test_ivr_dtmf_speak_to_agent(self, dynamodb_tables, mock_aws_environment):
        """Test DTMF input '4' transfers to agent."""
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': '+919876543210'},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'processDtmfInput',
                    'dtmfInput': '4'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert 'nextAction' in response
        assert response['nextAction'] == 'transferToAgent'
        assert 'connect' in response['message'].lower() or 'agent' in response['message'].lower()
    
    def test_ivr_dtmf_repeat_menu(self, dynamodb_tables, mock_aws_environment):
        """Test DTMF input '9' repeats the menu."""
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': '+919876543210'},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'processDtmfInput',
                    'dtmfInput': '9'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert response['shouldEnd'] is False
        # Should return to main menu
        assert '1' in response['message']
        assert '2' in response['message']
    
    def test_ivr_dtmf_end_call(self, dynamodb_tables, mock_aws_environment):
        """Test DTMF input '0' ends the call."""
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': '+919876543210'},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'processDtmfInput',
                    'dtmfInput': '0'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert response['shouldEnd'] is True
        assert 'thank' in response['message'].lower() or 'goodbye' in response['message'].lower()
    
    def test_ivr_dtmf_invalid_input(self, dynamodb_tables, mock_aws_environment):
        """Test invalid DTMF input handling."""
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': '+919876543210'},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'processDtmfInput',
                    'dtmfInput': '7'  # Invalid option
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert response['shouldEnd'] is False
        assert 'invalid' in response['message'].lower()
        assert response['nextAction'] == 'waitForDtmf'
    
    def test_ivr_multilingual_menu(self, dynamodb_tables, mock_aws_environment):
        """Test IVR menu in Hindi language."""
        # Create session with Hindi language preference
        sessions_table = dynamodb_tables['sessions']
        sessions_table.put_item(Item={
            'sessionId': 'ivr-test-contact-123',
            'userId': 'test-user',
            'phoneNumber': '+919876543210',
            'contactId': 'test-contact-123',
            'channel': 'ivr',
            'currentState': 'Welcome',
            'context': json.dumps({}),
            'language': 'hi',
            'messages': [],
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        })
        
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': '+919876543210'},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'handleIncomingCall'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert response['language'] == 'hi'
        # Check for Hindi text (Devanagari script)
        assert any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in response['message'])


# ============================================================================
# CALLBACK SCHEDULING TESTS
# ============================================================================

class TestCallbackScheduling:
    """Test IVR callback scheduling functionality."""
    
    def test_schedule_callback_next_available(self, dynamodb_tables, mock_aws_environment):
        """Test scheduling callback for next available time."""
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': '+919876543210'},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'scheduleCallback',
                    'callbackTime': 'next_available',
                    'language': 'en',
                    'reason': 'scheme_inquiry'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert response['shouldEnd'] is True
        assert 'scheduled' in response['message'].lower()
        
        # Verify callback was stored in DynamoDB
        callbacks_table = dynamodb_tables['callbacks']
        scan_response = callbacks_table.scan()
        callbacks = scan_response['Items']
        
        assert len(callbacks) >= 1
        callback = callbacks[0]
        assert callback['phoneNumber'] == '+919876543210'
        assert callback['status'] == 'pending'
        assert callback['reason'] == 'scheme_inquiry'
    
    def test_schedule_callback_specific_time(self, dynamodb_tables, mock_aws_environment):
        """Test scheduling callback for specific time."""
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': '+919876543210'},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'scheduleCallback',
                    'callbackTime': '14:30',  # 2:30 PM
                    'language': 'en',
                    'reason': 'application_help'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert response['shouldEnd'] is True
        
        # Verify callback time is parsed correctly
        callbacks_table = dynamodb_tables['callbacks']
        scan_response = callbacks_table.scan()
        callbacks = scan_response['Items']
        
        assert len(callbacks) >= 1
        callback = callbacks[0]
        scheduled_time = datetime.fromisoformat(callback['scheduledTime'])
        assert scheduled_time.hour == 14
        assert scheduled_time.minute == 30
    
    def test_get_callback_status_pending(self, dynamodb_tables, mock_aws_environment):
        """Test retrieving pending callback status."""
        phone_number = '+919876543210'
        
        # Create a pending callback
        callbacks_table = dynamodb_tables['callbacks']
        callback_id = hashlib.md5(f"{phone_number}{time.time()}".encode()).hexdigest()
        scheduled_time = datetime.utcnow() + timedelta(hours=2)
        
        callbacks_table.put_item(Item={
            'callbackId': callback_id,
            'phoneNumber': phone_number,
            'contactId': 'test-contact-123',
            'scheduledTime': scheduled_time.isoformat(),
            'status': 'pending',
            'reason': 'general_inquiry',
            'language': 'en',
            'createdAt': datetime.utcnow().isoformat()
        })
        
        # Query callback status
        event = {
            'Details': {
                'Parameters': {
                    'action': 'getCallbackStatus',
                    'phoneNumber': phone_number,
                    'language': 'en'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert 'scheduled' in response['message'].lower()
    
    def test_get_callback_status_none(self, dynamodb_tables, mock_aws_environment):
        """Test retrieving callback status when none exists."""
        event = {
            'Details': {
                'Parameters': {
                    'action': 'getCallbackStatus',
                    'phoneNumber': '+919999999999',  # No callbacks for this number
                    'language': 'en'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        assert 'message' in response
        assert 'no pending' in response['message'].lower() or 'not' in response['message'].lower()
    
    def test_callback_ttl_expiration(self, dynamodb_tables, mock_aws_environment):
        """Test that callbacks have TTL set for automatic cleanup."""
        phone_number = '+919876543210'
        
        # Schedule callback
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': phone_number},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'scheduleCallback',
                    'callbackTime': 'next_available',
                    'language': 'en',
                    'reason': 'test'
                }
            }
        }
        
        ivr_handler.lambda_handler(event, None)
        
        # Verify TTL is set
        callbacks_table = dynamodb_tables['callbacks']
        scan_response = callbacks_table.scan()
        callbacks = scan_response['Items']
        
        assert len(callbacks) >= 1
        callback = callbacks[0]
        assert 'ttl' in callback
        
        # TTL should be approximately 7 days from now
        expected_ttl = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        assert abs(callback['ttl'] - expected_ttl) < 3600  # Within 1 hour tolerance


# ============================================================================
# END-TO-END INTEGRATION TESTS
# ============================================================================

class TestSMSIVRIntegration:
    """End-to-end integration tests for SMS and IVR flows."""
    
    def test_sms_to_ivr_session_continuity(self, dynamodb_tables, mock_aws_environment):
        """Test that user can switch from SMS to IVR and maintain context."""
        phone_number = '+919876543210'
        user_id = 'test-user-123'
        
        # Create user profile
        users_table = dynamodb_tables['users']
        users_table.put_item(Item={
            'userId': user_id,
            'phoneNumber': phone_number,
            'preferredLanguage': 'en',
            'demographics': {
                'age': 30,
                'state': 'Maharashtra',
                'income': 300000
            },
            'createdAt': datetime.utcnow().isoformat()
        })
        
        # Create SMS session with context
        sessions_table = dynamodb_tables['sessions']
        sms_session_id = f"sms-{hashlib.md5(f'{phone_number}{time.time()}'.encode()).hexdigest()}"
        
        sessions_table.put_item(Item={
            'sessionId': sms_session_id,
            'userId': user_id,
            'phoneNumber': phone_number,
            'channel': 'sms',
            'currentState': 'SchemeDiscovery',
            'context': json.dumps({
                'userId': user_id,
                'userProfile': {
                    'age': 30,
                    'state': 'Maharashtra',
                    'income': 300000
                }
            }),
            'language': 'en',
            'messages': [],
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        })
        
        # Now user calls IVR - should recognize returning user
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': phone_number},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'handleIncomingCall'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        # Should greet as returning user
        assert 'message' in response
        assert 'welcome back' in response['message'].lower() or 'स्वागत' in response['message']
    
    def test_complete_sms_conversation_flow(self, dynamodb_tables, mock_aws_environment):
        """Test complete SMS conversation from greeting to scheme discovery."""
        with patch.object(sms_handler, 'lambda_client') as mock_lambda, \
             patch.object(sms_handler, 'pinpoint') as mock_pinpoint:
            
            phone_number = '+919876543210'
            
            # Mock Pinpoint responses
            mock_pinpoint.send_messages.return_value = {
                'MessageResponse': {
                    'Result': {
                        phone_number: {
                            'DeliveryStatus': 'SUCCESSFUL',
                            'MessageId': 'test-msg-id',
                            'StatusCode': 200
                        }
                    }
                }
            }
            
            # Step 1: Initial greeting
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'Welcome! Please tell me your age, state, and income.',
                        'nextState': 'ProfileCollection'
                    })
                }).encode())
            }
            
            event1 = {
                'body': json.dumps({
                    'action': 'receiveSms',
                    'phoneNumber': phone_number,
                    'message': 'Hello',
                    'language': 'en'
                })
            }
            
            response1 = sms_handler.lambda_handler(event1, None)
            assert response1['statusCode'] == 200
            session_id = json.loads(response1['body'])['sessionId']
            
            # Step 2: Provide profile information
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'Great! I found 5 schemes for you. Would you like to see them?',
                        'nextState': 'SchemeDiscovery'
                    })
                }).encode())
            }
            
            event2 = {
                'body': json.dumps({
                    'action': 'receiveSms',
                    'phoneNumber': phone_number,
                    'message': 'I am 30 years old from Maharashtra with income 300000',
                    'language': 'en'
                })
            }
            
            response2 = sms_handler.lambda_handler(event2, None)
            assert response2['statusCode'] == 200
            
            # Verify conversation manager was called twice
            assert mock_lambda.invoke.call_count == 2
    
    def test_complete_ivr_conversation_flow(self, dynamodb_tables, mock_aws_environment):
        """Test complete IVR conversation with DTMF navigation."""
        with patch.object(ivr_handler, 'lambda_client') as mock_lambda:
            
            phone_number = '+919876543210'
            contact_id = 'test-contact-123'
            
            # Step 1: Incoming call - present menu
            event1 = {
                'Details': {
                    'ContactData': {
                        'CustomerEndpoint': {'Address': phone_number},
                        'ContactId': contact_id
                    },
                    'Parameters': {
                        'action': 'handleIncomingCall'
                    }
                }
            }
            
            response1 = ivr_handler.lambda_handler(event1, None)
            assert response1['shouldEnd'] is False
            assert response1['nextAction'] == 'waitForDtmf'
            
            # Step 2: User presses 1 for scheme discovery
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 200,
                    'body': json.dumps({
                        'response': 'Let me help you discover schemes.',
                        'nextState': 'SchemeDiscovery'
                    })
                }).encode())
            }
            
            event2 = {
                'Details': {
                    'ContactData': {
                        'CustomerEndpoint': {'Address': phone_number},
                        'ContactId': contact_id
                    },
                    'Parameters': {
                        'action': 'processDtmfInput',
                        'dtmfInput': '1'
                    }
                }
            }
            
            response2 = ivr_handler.lambda_handler(event2, None)
            assert 'message' in response2
            
            # Step 3: User presses 0 to end call
            event3 = {
                'Details': {
                    'ContactData': {
                        'CustomerEndpoint': {'Address': phone_number},
                        'ContactId': contact_id
                    },
                    'Parameters': {
                        'action': 'processDtmfInput',
                        'dtmfInput': '0'
                    }
                }
            }
            
            response3 = ivr_handler.lambda_handler(event3, None)
            assert response3['shouldEnd'] is True
    
    def test_error_handling_in_sms_flow(self, dynamodb_tables, mock_aws_environment):
        """Test error handling when conversation manager fails."""
        with patch.object(sms_handler, 'lambda_client') as mock_lambda, \
             patch.object(sms_handler, 'pinpoint') as mock_pinpoint:
            
            # Mock conversation manager error
            mock_lambda.invoke.return_value = {
                'Payload': Mock(read=lambda: json.dumps({
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Internal error'
                    })
                }).encode())
            }
            
            # Mock Pinpoint success
            mock_pinpoint.send_messages.return_value = {
                'MessageResponse': {
                    'Result': {
                        '+919876543210': {
                            'DeliveryStatus': 'SUCCESSFUL',
                            'MessageId': 'test-msg-id',
                            'StatusCode': 200
                        }
                    }
                }
            }
            
            event = {
                'body': json.dumps({
                    'action': 'receiveSms',
                    'phoneNumber': '+919876543210',
                    'message': 'Hello',
                    'language': 'en'
                })
            }
            
            response = sms_handler.lambda_handler(event, None)
            
            # Should still return 200 but with error message sent to user
            assert response['statusCode'] == 200
            
            # Verify error message was sent via SMS
            mock_pinpoint.send_messages.assert_called()
    
    def test_multilingual_sms_ivr_consistency(self, dynamodb_tables, mock_aws_environment):
        """Test that language preference is maintained across SMS and IVR."""
        phone_number = '+919876543210'
        
        # Create user with Hindi preference
        users_table = dynamodb_tables['users']
        users_table.put_item(Item={
            'userId': 'test-user-hindi',
            'phoneNumber': phone_number,
            'preferredLanguage': 'hi',
            'demographics': {},
            'createdAt': datetime.utcnow().isoformat()
        })
        
        # Test IVR call - should use Hindi
        event = {
            'Details': {
                'ContactData': {
                    'CustomerEndpoint': {'Address': phone_number},
                    'ContactId': 'test-contact-123'
                },
                'Parameters': {
                    'action': 'handleIncomingCall'
                }
            }
        }
        
        response = ivr_handler.lambda_handler(event, None)
        
        # Should contain Hindi text
        assert any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in response['message'])


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

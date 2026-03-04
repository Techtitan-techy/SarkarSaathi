"""
SMS Handler Lambda Function

Handles bidirectional SMS communication for feature phone support.
Integrates with conversation_manager.py for response generation.
Implements rate limiting, multi-part SMS handling, and conversation history tracking.
"""

import json
import os
import boto3
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
pinpoint = boto3.client('pinpoint', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
ssm = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

# Environment variables
SMS_CONVERSATIONS_TABLE = os.environ.get('SMS_CONVERSATIONS_TABLE', 'SarkariSaathi-SmsConversations')
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'SarkariSaathi-Sessions')
USERS_TABLE = os.environ.get('USERS_TABLE', 'SarkariSaathi-Users')
PINPOINT_APP_ID = os.environ.get('PINPOINT_APP_ID')
CONVERSATION_MANAGER_FUNCTION = os.environ.get('CONVERSATION_MANAGER_FUNCTION', 'SarkariSaathi-ConversationManager')

# SMS configuration
SMS_CHUNK_SIZE = 160  # Standard SMS length
SMS_RATE_LIMIT = 10  # Messages per minute per user
RATE_LIMIT_WINDOW = 60  # seconds


def lambda_handler(event, context):
    """Main Lambda handler for SMS processing."""
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        action = body.get('action', 'sendSms')
        
        handlers = {
            'sendSms': handle_send_sms,
            'receiveSms': handle_receive_sms,
            'getConversationHistory': get_conversation_history
        }
        
        handler = handlers.get(action)
        if not handler:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
        
        result = handler(body, context)
        return result
        
    except Exception as e:
        print(f"Error in SMS handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for API responses."""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }


def check_rate_limit(phone_number: str) -> Tuple[bool, int]:
    """
    Check if user has exceeded SMS rate limit.
    Returns (is_allowed, remaining_quota)
    """
    try:
        table = dynamodb.Table(SMS_CONVERSATIONS_TABLE)
        
        # Get messages from last minute
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=RATE_LIMIT_WINDOW)
        
        response = table.query(
            KeyConditionExpression='phoneNumber = :phone AND #ts >= :window_start',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':phone': phone_number,
                ':window_start': window_start.isoformat()
            }
        )
        
        message_count = len(response.get('Items', []))
        remaining = max(0, SMS_RATE_LIMIT - message_count)
        is_allowed = message_count < SMS_RATE_LIMIT
        
        return is_allowed, remaining
        
    except Exception as e:
        print(f"Error checking rate limit: {str(e)}")
        # Allow on error to not block users
        return True, SMS_RATE_LIMIT


def store_sms_message(phone_number: str, message: str, direction: str, 
                      session_id: str, language: str = 'en') -> None:
    """Store SMS message in conversation history."""
    try:
        table = dynamodb.Table(SMS_CONVERSATIONS_TABLE)
        
        timestamp = datetime.utcnow().isoformat()
        message_id = hashlib.md5(f"{phone_number}{timestamp}".encode()).hexdigest()
        
        # TTL: 30 days from now
        ttl = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        
        item = {
            'phoneNumber': phone_number,
            'timestamp': timestamp,
            'messageId': message_id,
            'message': message,
            'direction': direction,  # 'inbound' or 'outbound'
            'sessionId': session_id,
            'language': language,
            'ttl': ttl
        }
        
        table.put_item(Item=item)
        print(f"Stored SMS message: {message_id}")
        
    except Exception as e:
        print(f"Error storing SMS message: {str(e)}")


def chunk_message(message: str, chunk_size: int = SMS_CHUNK_SIZE) -> List[str]:
    """
    Split long message into SMS-sized chunks.
    Tries to break at word boundaries when possible.
    """
    if len(message) <= chunk_size:
        return [message]
    
    chunks = []
    remaining = message
    
    while remaining:
        if len(remaining) <= chunk_size:
            chunks.append(remaining)
            break
        
        # Try to break at last space within chunk_size
        chunk = remaining[:chunk_size]
        last_space = chunk.rfind(' ')
        
        if last_space > chunk_size * 0.7:  # Only break at space if it's not too early
            chunks.append(remaining[:last_space])
            remaining = remaining[last_space + 1:]
        else:
            chunks.append(remaining[:chunk_size])
            remaining = remaining[chunk_size:]
    
    # Add part indicators for multi-part messages
    if len(chunks) > 1:
        chunks = [f"({i+1}/{len(chunks)}) {chunk}" for i, chunk in enumerate(chunks)]
    
    return chunks


def send_sms_via_pinpoint(phone_number: str, message: str) -> Dict[str, Any]:
    """Send SMS using Amazon Pinpoint."""
    try:
        # Ensure phone number is in E.164 format
        if not phone_number.startswith('+'):
            # Assume India (+91) if no country code
            phone_number = f"+91{phone_number}"
        
        response = pinpoint.send_messages(
            ApplicationId=PINPOINT_APP_ID,
            MessageRequest={
                'Addresses': {
                    phone_number: {
                        'ChannelType': 'SMS'
                    }
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'MessageType': 'TRANSACTIONAL',
                        'OriginationNumber': None  # Use default origination number
                    }
                }
            }
        )
        
        result = response['MessageResponse']['Result'][phone_number]
        
        return {
            'success': result['DeliveryStatus'] == 'SUCCESSFUL',
            'messageId': result.get('MessageId'),
            'statusCode': result.get('StatusCode'),
            'statusMessage': result.get('StatusMessage')
        }
        
    except Exception as e:
        print(f"Error sending SMS via Pinpoint: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def get_or_create_session(phone_number: str, user_id: Optional[str] = None) -> str:
    """Get existing session or create new one for phone number."""
    try:
        # Try to find existing active session
        users_table = dynamodb.Table(USERS_TABLE)
        
        # Look up user by phone number
        if not user_id:
            response = users_table.query(
                IndexName='phoneNumber-index',
                KeyConditionExpression='phoneNumber = :phone',
                ExpressionAttributeValues={':phone': phone_number},
                Limit=1
            )
            
            if response.get('Items'):
                user_id = response['Items'][0]['userId']
        
        # Check for active session
        sessions_table = dynamodb.Table(SESSIONS_TABLE)
        
        if user_id:
            # Look for recent session (within last hour)
            current_time = datetime.utcnow()
            one_hour_ago = current_time - timedelta(hours=1)
            
            response = sessions_table.scan(
                FilterExpression='userId = :user_id AND updatedAt >= :time_threshold',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':time_threshold': one_hour_ago.isoformat()
                },
                Limit=1
            )
            
            if response.get('Items'):
                return response['Items'][0]['sessionId']
        
        # Create new session
        session_id = f"sms-{hashlib.md5(f'{phone_number}{time.time()}'.encode()).hexdigest()}"
        
        timestamp = datetime.utcnow().isoformat()
        ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        
        session_item = {
            'sessionId': session_id,
            'userId': user_id or f"phone-{phone_number}",
            'phoneNumber': phone_number,
            'channel': 'sms',
            'currentState': 'Welcome',
            'context': json.dumps({}),
            'language': 'en',
            'messages': [],
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'ttl': ttl
        }
        
        sessions_table.put_item(Item=session_item)
        print(f"Created new SMS session: {session_id}")
        
        return session_id
        
    except Exception as e:
        print(f"Error getting/creating session: {str(e)}")
        # Fallback to generating session ID
        return f"sms-{hashlib.md5(f'{phone_number}{time.time()}'.encode()).hexdigest()}"


def handle_receive_sms(body: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle incoming SMS from user."""
    try:
        phone_number = body.get('phoneNumber')
        message = body.get('message', '').strip()
        language = body.get('language', 'en')
        
        if not phone_number or not message:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'phoneNumber and message are required'})
            }
        
        # Check rate limit
        is_allowed, remaining = check_rate_limit(phone_number)
        if not is_allowed:
            error_msg = "Rate limit exceeded. Please wait a minute before sending more messages."
            if language == 'hi':
                error_msg = "दर सीमा पार हो गई। कृपया अधिक संदेश भेजने से पहले एक मिनट प्रतीक्षा करें।"
            
            return {
                'statusCode': 429,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': error_msg,
                    'remaining': remaining
                })
            }
        
        # Get or create session
        session_id = get_or_create_session(phone_number)
        
        # Store incoming message
        store_sms_message(phone_number, message, 'inbound', session_id, language)
        
        # Invoke conversation manager to generate response
        conversation_event = {
            'action': 'determineState',
            'sessionId': session_id,
            'userMessage': message,
            'language': language,
            'channel': 'sms'
        }
        
        # Call conversation manager
        response = lambda_client.invoke(
            FunctionName=CONVERSATION_MANAGER_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(conversation_event)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        # Extract response text
        if response_payload.get('statusCode') == 200:
            response_body = json.loads(response_payload.get('body', '{}'))
            response_text = response_body.get('response', 'I apologize, I could not process your request.')
        else:
            response_text = 'Sorry, something went wrong. Please try again.'
            if language == 'hi':
                response_text = 'क्षमा करें, कुछ गलत हो गया। कृपया पुनः प्रयास करें।'
        
        # Chunk response for SMS
        message_chunks = chunk_message(response_text, SMS_CHUNK_SIZE)
        
        # Send SMS chunks
        sent_messages = []
        for chunk in message_chunks:
            send_result = send_sms_via_pinpoint(phone_number, chunk)
            sent_messages.append(send_result)
            
            # Store outbound message
            if send_result.get('success'):
                store_sms_message(phone_number, chunk, 'outbound', session_id, language)
            
            # Small delay between chunks to ensure order
            if len(message_chunks) > 1:
                time.sleep(0.5)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'sessionId': session_id,
                'messagesSent': len(sent_messages),
                'results': sent_messages,
                'remaining': remaining - 1
            })
        }
        
    except Exception as e:
        print(f"Error handling received SMS: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def handle_send_sms(body: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle outbound SMS (for system-initiated messages)."""
    try:
        phone_number = body.get('phoneNumber')
        message = body.get('message', '').strip()
        language = body.get('language', 'en')
        session_id = body.get('sessionId')
        
        if not phone_number or not message:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'phoneNumber and message are required'})
            }
        
        # Get or create session if not provided
        if not session_id:
            session_id = get_or_create_session(phone_number)
        
        # Chunk message
        message_chunks = chunk_message(message, SMS_CHUNK_SIZE)
        
        # Send SMS chunks
        sent_messages = []
        for chunk in message_chunks:
            send_result = send_sms_via_pinpoint(phone_number, chunk)
            sent_messages.append(send_result)
            
            # Store outbound message
            if send_result.get('success'):
                store_sms_message(phone_number, chunk, 'outbound', session_id, language)
            
            # Small delay between chunks
            if len(message_chunks) > 1:
                time.sleep(0.5)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'sessionId': session_id,
                'messagesSent': len(sent_messages),
                'results': sent_messages
            })
        }
        
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def get_conversation_history(body: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Retrieve SMS conversation history for a phone number."""
    try:
        phone_number = body.get('phoneNumber')
        limit = body.get('limit', 50)
        
        if not phone_number:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'phoneNumber is required'})
            }
        
        table = dynamodb.Table(SMS_CONVERSATIONS_TABLE)
        
        response = table.query(
            KeyConditionExpression='phoneNumber = :phone',
            ExpressionAttributeValues={':phone': phone_number},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        
        messages = response.get('Items', [])
        
        # Convert Decimal to float for JSON serialization
        for msg in messages:
            for key, value in msg.items():
                if isinstance(value, Decimal):
                    msg[key] = float(value)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'phoneNumber': phone_number,
                'messageCount': len(messages),
                'messages': messages
            })
        }
        
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

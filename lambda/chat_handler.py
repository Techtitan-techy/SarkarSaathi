"""
Chat/Conversation Lambda Handler
Handles chat messages and integrates with Amazon Bedrock
"""
import json
import boto3
import os
from datetime import datetime
from shared.utils import (
    create_response,
    get_bedrock_client,
    get_dynamodb_client,
    generate_id,
    log_info,
    log_error
)
from shared.models import Session, Message

# Initialize AWS clients
bedrock_client = get_bedrock_client()
dynamodb = get_dynamodb_client()

# Environment variables
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'sarkari-saathi-sessions')
MODEL_ID = 'anthropic.claude-3-5-sonnet-20241022-v2:0'


def lambda_handler(event, context):
    """
    Main handler for chat/conversation
    
    Endpoints:
    - POST /chat/message - Send a message and get response
    - GET /chat/session/{sessionId} - Get session history
    - POST /chat/session - Create new session
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        log_info(f"Chat handler called: {http_method} {path}")
        
        if http_method == 'POST':
            if path.endswith('/message'):
                return handle_message(event)
            elif path.endswith('/session'):
                return create_session(event)
        elif http_method == 'GET' and '/session/' in path:
            return get_session(event)
        
        return create_response(400, {'error': 'Invalid endpoint'})
        
    except Exception as e:
        log_error(f"Chat handler error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def create_session(event):
    """Create a new chat session"""
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('userId', 'anonymous')
        language = body.get('language', 'en')
        
        session_id = generate_id('session')
        
        session = {
            'sessionId': session_id,
            'userId': user_id,
            'language': language,
            'messages': [],
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Save to DynamoDB
        table = dynamodb.Table(SESSIONS_TABLE)
        table.put_item(Item=session)
        
        log_info(f"Session created: {session_id}")
        
        return create_response(200, {
            'sessionId': session_id,
            'userId': user_id,
            'language': language
        })
        
    except Exception as e:
        log_error(f"Create session error: {str(e)}")
        return create_response(500, {'error': 'Failed to create session'})


def get_session(event):
    """Get session history"""
    try:
        path_params = event.get('pathParameters', {})
        session_id = path_params.get('sessionId')
        
        if not session_id:
            return create_response(400, {'error': 'No session ID provided'})
        
        # Get from DynamoDB
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={'sessionId': session_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Session not found'})
        
        return create_response(200, response['Item'])
        
    except Exception as e:
        log_error(f"Get session error: {str(e)}")
        return create_response(500, {'error': 'Failed to get session'})


def handle_message(event):
    """Handle incoming chat message and generate response"""
    try:
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('sessionId')
        message = body.get('message')
        user_info = body.get('userInfo', {})
        language = body.get('language', 'en')
        
        if not message:
            return create_response(400, {'error': 'No message provided'})
        
        # Get session history
        session_history = []
        if session_id:
            table = dynamodb.Table(SESSIONS_TABLE)
            response = table.get_item(Key={'sessionId': session_id})
            if 'Item' in response:
                session_history = response['Item'].get('messages', [])
        
        # Build conversation context
        conversation_context = build_context(session_history, user_info, language)
        
        # Generate response using Bedrock
        ai_response = generate_bedrock_response(
            message,
            conversation_context,
            language
        )
        
        # Update session
        if session_id:
            update_session(session_id, message, ai_response)
        
        log_info(f"Message processed for session: {session_id}")
        
        return create_response(200, {
            'response': ai_response,
            'sessionId': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        log_error(f"Handle message error: {str(e)}")
        return create_response(500, {'error': 'Failed to process message'})


def build_context(session_history, user_info, language):
    """Build conversation context for Bedrock"""
    context = {
        'role': 'system',
        'content': get_system_prompt(language)
    }
    
    # Add user info if available
    if user_info:
        user_context = f"\nUser Information:\n"
        if user_info.get('age'):
            user_context += f"- Age: {user_info['age']}\n"
        if user_info.get('state'):
            user_context += f"- State: {user_info['state']}\n"
        if user_info.get('income'):
            user_context += f"- Income: ₹{user_info['income']}\n"
        if user_info.get('occupation'):
            user_context += f"- Occupation: {user_info['occupation']}\n"
        
        context['content'] += user_context
    
    return context


def get_system_prompt(language):
    """Get system prompt based on language"""
    if language == 'hi':
        return """आप SarkariSaathi हैं, एक सहायक AI जो भारतीय नागरिकों को सरकारी योजनाओं के बारे में जानकारी देता है।

आपका काम:
1. उपयोगकर्ता की जानकारी (उम्र, राज्य, आय, व्यवसाय) एकत्र करना
2. उपयुक्त सरकारी योजनाओं की सिफारिश करना
3. योजना के लाभ और पात्रता मानदंड समझाना
4. आवेदन प्रक्रिया में मदद करना

हमेशा विनम्र, स्पष्ट और सहायक रहें। सरल हिंदी का उपयोग करें।"""
    else:
        return """You are SarkariSaathi, a helpful AI assistant that helps Indian citizens learn about government schemes.

Your job:
1. Collect user information (age, state, income, occupation)
2. Recommend suitable government schemes
3. Explain scheme benefits and eligibility criteria
4. Help with the application process

Always be polite, clear, and helpful. Use simple language."""


def generate_bedrock_response(message, context, language):
    """Generate response using Amazon Bedrock (Claude)"""
    try:
        # Build messages for Claude
        messages = [
            {
                'role': 'user',
                'content': message
            }
        ]
        
        # Prepare request body
        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'system': context['content'],
            'messages': messages,
            'temperature': 0.7
        }
        
        # Invoke Bedrock
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        ai_message = response_body['content'][0]['text']
        
        return ai_message
        
    except Exception as e:
        log_error(f"Bedrock error: {str(e)}")
        
        # Fallback response
        if language == 'hi':
            return "क्षमा करें, मुझे आपके संदेश को संसाधित करने में समस्या हुई। कृपया पुनः प्रयास करें।"
        else:
            return "Sorry, I had trouble processing your message. Please try again."


def update_session(session_id, user_message, ai_response):
    """Update session with new messages"""
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        
        timestamp = datetime.utcnow().isoformat()
        
        # Add messages to session
        table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET messages = list_append(if_not_exists(messages, :empty_list), :new_messages), updatedAt = :timestamp',
            ExpressionAttributeValues={
                ':empty_list': [],
                ':new_messages': [
                    {
                        'role': 'user',
                        'content': user_message,
                        'timestamp': timestamp
                    },
                    {
                        'role': 'assistant',
                        'content': ai_response,
                        'timestamp': timestamp
                    }
                ],
                ':timestamp': timestamp
            }
        )
        
    except Exception as e:
        log_error(f"Update session error: {str(e)}")

"""
IVR Handler Lambda Function

Handles Amazon Connect IVR interactions with DTMF support for feature phones.
Integrates with conversation_manager.py for dynamic responses.
Implements call recording, queuing, and callback system.
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
connect = boto3.client('connect', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
polly = boto3.client('polly', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

# Environment variables
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'SarkariSaathi-Sessions')
USERS_TABLE = os.environ.get('USERS_TABLE', 'SarkariSaathi-Users')
IVR_CALLBACKS_TABLE = os.environ.get('IVR_CALLBACKS_TABLE', 'SarkariSaathi-IvrCallbacks')
CONVERSATION_MANAGER_FUNCTION = os.environ.get('CONVERSATION_MANAGER_FUNCTION', 'SarkariSaathi-ConversationManager')
TTS_CACHE_BUCKET = os.environ.get('TTS_CACHE_BUCKET')
CONNECT_INSTANCE_ID = os.environ.get('CONNECT_INSTANCE_ID')

# DTMF menu options
DTMF_MENU = {
    '1': 'scheme_discovery',
    '2': 'eligibility_check',
    '3': 'application_guidance',
    '4': 'speak_to_agent',
    '9': 'repeat_menu',
    '0': 'end_call'
}


def lambda_handler(event, context):
    """Main Lambda handler for IVR processing."""
    try:
        # Amazon Connect passes contact flow parameters
        action = event.get('Details', {}).get('Parameters', {}).get('action', 'handleIncomingCall')
        
        handlers = {
            'handleIncomingCall': handle_incoming_call,
            'processDtmfInput': process_dtmf_input,
            'generateResponse': generate_response,
            'scheduleCallback': schedule_callback,
            'getCallbackStatus': get_callback_status
        }
        
        handler = handlers.get(action)
        if not handler:
            return create_ivr_response(
                f"Unknown action: {action}",
                should_end=True
            )
        
        result = handler(event, context)
        return result
        
    except Exception as e:
        print(f"Error in IVR handler: {str(e)}")
        return create_ivr_response(
            "We're experiencing technical difficulties. Please try again later.",
            should_end=True
        )


def create_ivr_response(message: str, should_end: bool = False, 
                       next_action: str = None, language: str = 'en') -> Dict[str, Any]:
    """
    Create standardized IVR response for Amazon Connect.
    """
    response = {
        'message': message,
        'shouldEnd': should_end,
        'language': language
    }
    
    if next_action:
        response['nextAction'] = next_action
    
    return response



def get_or_create_session(phone_number: str, contact_id: str) -> str:
    """Get existing session or create new one for IVR call."""
    try:
        # Try to find existing active session
        users_table = dynamodb.Table(USERS_TABLE)
        
        # Look up user by phone number
        user_id = None
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
        session_id = f"ivr-{contact_id}"
        
        timestamp = datetime.utcnow().isoformat()
        ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        
        session_item = {
            'sessionId': session_id,
            'userId': user_id or f"phone-{phone_number}",
            'phoneNumber': phone_number,
            'contactId': contact_id,
            'channel': 'ivr',
            'currentState': 'Welcome',
            'context': json.dumps({}),
            'language': 'en',
            'messages': [],
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'ttl': ttl
        }
        
        sessions_table.put_item(Item=session_item)
        print(f"Created new IVR session: {session_id}")
        
        return session_id
        
    except Exception as e:
        print(f"Error getting/creating session: {str(e)}")
        return f"ivr-{contact_id}"


def handle_incoming_call(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle incoming IVR call - present main menu."""
    try:
        # Extract contact information from Amazon Connect event
        contact_data = event.get('Details', {}).get('ContactData', {})
        phone_number = contact_data.get('CustomerEndpoint', {}).get('Address', '')
        contact_id = contact_data.get('ContactId', '')
        
        # Get or create session
        session_id = get_or_create_session(phone_number, contact_id)
        
        # Get session context to check if returning user
        sessions_table = dynamodb.Table(SESSIONS_TABLE)
        response = sessions_table.get_item(Key={'sessionId': session_id})
        
        is_returning = False
        language = 'en'
        
        if 'Item' in response:
            context_data = response['Item'].get('context', '{}')
            if isinstance(context_data, str):
                context_data = json.loads(context_data)
            is_returning = bool(context_data.get('userProfile'))
            language = response['Item'].get('language', 'en')
        
        # Generate welcome message with menu
        if language == 'hi':
            if is_returning:
                message = "नमस्ते! SarkariSaathi में आपका स्वागत है। "
            else:
                message = "नमस्ते! SarkariSaathi में आपका स्वागत है। मैं आपको सरकारी योजनाओं के बारे में जानकारी देने में मदद कर सकता हूं। "
            
            message += """कृपया चुनें:
1 - योजनाओं की खोज करें
2 - पात्रता जांचें
3 - आवेदन सहायता
4 - एजेंट से बात करें
9 - मेनू दोहराएं
0 - कॉल समाप्त करें"""
        else:
            if is_returning:
                message = "Welcome back to SarkariSaathi! "
            else:
                message = "Welcome to SarkariSaathi! I can help you discover government schemes. "
            
            message += """Please select:
1 - Discover schemes
2 - Check eligibility
3 - Application help
4 - Speak to agent
9 - Repeat menu
0 - End call"""
        
        return create_ivr_response(
            message,
            should_end=False,
            next_action='waitForDtmf',
            language=language
        )
        
    except Exception as e:
        print(f"Error handling incoming call: {str(e)}")
        return create_ivr_response(
            "We're experiencing technical difficulties. Please try again later.",
            should_end=True
        )



def process_dtmf_input(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process DTMF (touch-tone) input from user."""
    try:
        # Extract DTMF input from Amazon Connect event
        parameters = event.get('Details', {}).get('Parameters', {})
        dtmf_input = parameters.get('dtmfInput', '')
        contact_data = event.get('Details', {}).get('ContactData', {})
        phone_number = contact_data.get('CustomerEndpoint', {}).get('Address', '')
        contact_id = contact_data.get('ContactId', '')
        
        # Get session
        session_id = f"ivr-{contact_id}"
        sessions_table = dynamodb.Table(SESSIONS_TABLE)
        response = sessions_table.get_item(Key={'sessionId': session_id})
        
        language = 'en'
        context_data = {}
        
        if 'Item' in response:
            language = response['Item'].get('language', 'en')
            context_data = response['Item'].get('context', '{}')
            if isinstance(context_data, str):
                context_data = json.loads(context_data)
        
        # Map DTMF to action
        action = DTMF_MENU.get(dtmf_input)
        
        if not action:
            # Invalid input
            if language == 'hi':
                message = "अमान्य इनपुट। कृपया 0 से 9 के बीच एक नंबर दबाएं।"
            else:
                message = "Invalid input. Please press a number between 0 and 9."
            
            return create_ivr_response(
                message,
                should_end=False,
                next_action='waitForDtmf',
                language=language
            )
        
        # Handle special actions
        if action == 'end_call':
            if language == 'hi':
                message = "धन्यवाद! SarkariSaathi का उपयोग करने के लिए धन्यवाद। अलविदा!"
            else:
                message = "Thank you for using SarkariSaathi. Goodbye!"
            
            return create_ivr_response(message, should_end=True, language=language)
        
        if action == 'repeat_menu':
            # Return to main menu
            return handle_incoming_call(event, context)
        
        if action == 'speak_to_agent':
            # Transfer to agent queue
            if language == 'hi':
                message = "कृपया प्रतीक्षा करें, मैं आपको एक एजेंट से जोड़ रहा हूं।"
            else:
                message = "Please wait while I connect you to an agent."
            
            return create_ivr_response(
                message,
                should_end=False,
                next_action='transferToAgent',
                language=language
            )
        
        # For other actions, invoke conversation manager
        conversation_event = {
            'action': 'determineState',
            'sessionId': session_id,
            'userMessage': f"User selected: {action}",
            'language': language,
            'channel': 'ivr',
            'dtmfAction': action
        }
        
        # Call conversation manager
        cm_response = lambda_client.invoke(
            FunctionName=CONVERSATION_MANAGER_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(conversation_event)
        )
        
        response_payload = json.loads(cm_response['Payload'].read())
        
        # Extract response
        if response_payload.get('statusCode') == 200:
            response_body = json.loads(response_payload.get('body', '{}'))
            next_state = response_body.get('nextState', 'Welcome')
            
            # Update session with new state
            sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression='SET currentState = :state, updatedAt = :updated',
                ExpressionAttributeValues={
                    ':state': next_state,
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            
            # Generate appropriate response based on action
            return generate_response_for_action(action, language, context_data)
        else:
            if language == 'hi':
                message = "क्षमा करें, कुछ गलत हो गया। कृपया पुनः प्रयास करें।"
            else:
                message = "Sorry, something went wrong. Please try again."
            
            return create_ivr_response(
                message,
                should_end=False,
                next_action='returnToMenu',
                language=language
            )
        
    except Exception as e:
        print(f"Error processing DTMF input: {str(e)}")
        return create_ivr_response(
            "We're experiencing technical difficulties.",
            should_end=True
        )



def generate_response_for_action(action: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate IVR response based on selected action."""
    try:
        user_profile = context.get('userProfile', {})
        
        if action == 'scheme_discovery':
            if not user_profile:
                # Need to collect profile first
                if language == 'hi':
                    message = """योजनाओं की खोज के लिए, मुझे आपके बारे में कुछ जानकारी चाहिए।
कृपया दबाएं:
1 - 18 से 30 वर्ष की आयु
2 - 31 से 50 वर्ष की आयु
3 - 50 वर्ष से अधिक आयु
9 - मुख्य मेनू पर वापस जाएं"""
                else:
                    message = """To discover schemes, I need some information about you.
Please press:
1 - Age 18-30 years
2 - Age 31-50 years
3 - Age above 50 years
9 - Return to main menu"""
                
                return create_ivr_response(
                    message,
                    should_end=False,
                    next_action='collectAge',
                    language=language
                )
            else:
                # Have profile, can search schemes
                if language == 'hi':
                    message = """योजना श्रेणी चुनें:
1 - शिक्षा
2 - स्वास्थ्य
3 - रोजगार
4 - कृषि
5 - सभी योजनाएं
9 - मुख्य मेनू"""
                else:
                    message = """Select scheme category:
1 - Education
2 - Healthcare
3 - Employment
4 - Agriculture
5 - All schemes
9 - Main menu"""
                
                return create_ivr_response(
                    message,
                    should_end=False,
                    next_action='selectCategory',
                    language=language
                )
        
        elif action == 'eligibility_check':
            if language == 'hi':
                message = """पात्रता जांच के लिए, कृपया योजना का नाम बताएं या:
1 - लोकप्रिय योजनाएं देखें
9 - मुख्य मेनू"""
            else:
                message = """For eligibility check, please tell the scheme name or:
1 - View popular schemes
9 - Main menu"""
            
            return create_ivr_response(
                message,
                should_end=False,
                next_action='selectScheme',
                language=language
            )
        
        elif action == 'application_guidance':
            if language == 'hi':
                message = """आवेदन सहायता के लिए:
1 - आवश्यक दस्तावेज़ जानें
2 - आवेदन प्रक्रिया सुनें
3 - कॉलबैक शेड्यूल करें
9 - मुख्य मेनू"""
            else:
                message = """For application help:
1 - Know required documents
2 - Hear application process
3 - Schedule callback
9 - Main menu"""
            
            return create_ivr_response(
                message,
                should_end=False,
                next_action='applicationHelp',
                language=language
            )
        
        else:
            # Default to main menu
            if language == 'hi':
                message = "मुख्य मेनू पर लौट रहे हैं।"
            else:
                message = "Returning to main menu."
            
            return create_ivr_response(
                message,
                should_end=False,
                next_action='returnToMenu',
                language=language
            )
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return create_ivr_response(
            "Error generating response.",
            should_end=True
        )


def generate_response(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Generate dynamic response using conversation manager."""
    try:
        parameters = event.get('Details', {}).get('Parameters', {})
        session_id = parameters.get('sessionId')
        user_input = parameters.get('userInput', '')
        language = parameters.get('language', 'en')
        
        # Invoke conversation manager
        conversation_event = {
            'action': 'determineState',
            'sessionId': session_id,
            'userMessage': user_input,
            'language': language,
            'channel': 'ivr'
        }
        
        response = lambda_client.invoke(
            FunctionName=CONVERSATION_MANAGER_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(conversation_event)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            response_body = json.loads(response_payload.get('body', '{}'))
            response_text = response_body.get('response', 'I could not process your request.')
            
            return create_ivr_response(
                response_text,
                should_end=False,
                next_action='waitForDtmf',
                language=language
            )
        else:
            if language == 'hi':
                message = "क्षमा करें, मैं आपका अनुरोध संसाधित नहीं कर सका।"
            else:
                message = "Sorry, I could not process your request."
            
            return create_ivr_response(
                message,
                should_end=False,
                next_action='returnToMenu',
                language=language
            )
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return create_ivr_response(
            "Error generating response.",
            should_end=True
        )



def schedule_callback(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Schedule a callback for the user."""
    try:
        parameters = event.get('Details', {}).get('Parameters', {})
        contact_data = event.get('Details', {}).get('ContactData', {})
        
        phone_number = contact_data.get('CustomerEndpoint', {}).get('Address', '')
        contact_id = contact_data.get('ContactId', '')
        callback_time = parameters.get('callbackTime', 'next_available')
        language = parameters.get('language', 'en')
        reason = parameters.get('reason', 'general_inquiry')
        
        # Store callback request in DynamoDB
        callbacks_table = dynamodb.Table(IVR_CALLBACKS_TABLE)
        
        callback_id = hashlib.md5(f"{phone_number}{time.time()}".encode()).hexdigest()
        timestamp = datetime.utcnow().isoformat()
        
        # Calculate callback time
        if callback_time == 'next_available':
            scheduled_time = datetime.utcnow() + timedelta(hours=1)
        else:
            # Parse callback time (format: HH:MM)
            try:
                hour, minute = map(int, callback_time.split(':'))
                now = datetime.utcnow()
                scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if scheduled_time < now:
                    scheduled_time += timedelta(days=1)
            except:
                scheduled_time = datetime.utcnow() + timedelta(hours=1)
        
        # TTL: 7 days from now
        ttl = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        
        callback_item = {
            'callbackId': callback_id,
            'phoneNumber': phone_number,
            'contactId': contact_id,
            'scheduledTime': scheduled_time.isoformat(),
            'status': 'pending',
            'reason': reason,
            'language': language,
            'createdAt': timestamp,
            'ttl': ttl
        }
        
        callbacks_table.put_item(Item=callback_item)
        
        # Generate confirmation message
        if language == 'hi':
            message = f"आपका कॉलबैक {scheduled_time.strftime('%I:%M %p')} बजे शेड्यूल किया गया है। धन्यवाद!"
        else:
            message = f"Your callback has been scheduled for {scheduled_time.strftime('%I:%M %p')}. Thank you!"
        
        return create_ivr_response(
            message,
            should_end=True,
            language=language
        )
        
    except Exception as e:
        print(f"Error scheduling callback: {str(e)}")
        if language == 'hi':
            message = "कॉलबैक शेड्यूल करने में त्रुटि। कृपया बाद में पुनः प्रयास करें।"
        else:
            message = "Error scheduling callback. Please try again later."
        
        return create_ivr_response(message, should_end=True)


def get_callback_status(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Get status of scheduled callback."""
    try:
        parameters = event.get('Details', {}).get('Parameters', {})
        phone_number = parameters.get('phoneNumber')
        language = parameters.get('language', 'en')
        
        if not phone_number:
            return create_ivr_response(
                "Phone number required.",
                should_end=True
            )
        
        # Query callbacks for this phone number
        callbacks_table = dynamodb.Table(IVR_CALLBACKS_TABLE)
        
        response = callbacks_table.scan(
            FilterExpression='phoneNumber = :phone AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':phone': phone_number,
                ':status': 'pending'
            }
        )
        
        callbacks = response.get('Items', [])
        
        if not callbacks:
            if language == 'hi':
                message = "आपके पास कोई लंबित कॉलबैक नहीं है।"
            else:
                message = "You have no pending callbacks."
        else:
            callback = callbacks[0]
            scheduled_time = datetime.fromisoformat(callback['scheduledTime'])
            
            if language == 'hi':
                message = f"आपका कॉलबैक {scheduled_time.strftime('%I:%M %p')} बजे शेड्यूल है।"
            else:
                message = f"Your callback is scheduled for {scheduled_time.strftime('%I:%M %p')}."
        
        return create_ivr_response(
            message,
            should_end=False,
            next_action='returnToMenu',
            language=language
        )
        
    except Exception as e:
        print(f"Error getting callback status: {str(e)}")
        return create_ivr_response(
            "Error retrieving callback status.",
            should_end=True
        )

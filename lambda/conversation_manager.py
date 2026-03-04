"""
Conversation Manager Lambda Function

Orchestrates conversational AI flow with state management, intent classification,
language switching, and context retention across multiple turns.
"""

import json
import os
import boto3
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

# Environment variables
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'sarkari-saathi-sessions')
USERS_TABLE = os.environ.get('USERS_TABLE', 'sarkari-saathi-users')
CLAUDE_MODEL_ID = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

# Conversation states
STATES = {
    'WELCOME': 'Welcome',
    'PROFILE_COLLECTION': 'ProfileCollection',
    'SCHEME_DISCOVERY': 'SchemeDiscovery',
    'ELIGIBILITY_CHECK': 'EligibilityCheck',
    'APPLICATION_GUIDANCE': 'ApplicationGuidance'
}

# Language detection patterns
LANGUAGE_PATTERNS = {
    'hi': re.compile(r'[\u0900-\u097F]'),  # Devanagari script
    'ta': re.compile(r'[\u0B80-\u0BFF]'),  # Tamil script
    'te': re.compile(r'[\u0C00-\u0C7F]'),  # Telugu script
    'bn': re.compile(r'[\u0980-\u09FF]'),  # Bengali script
    'mr': re.compile(r'[\u0900-\u097F]'),  # Marathi (Devanagari)
}


def lambda_handler(event, context):
    """Main Lambda handler for conversation management."""
    try:
        action = event.get('action', 'determineState')
        
        handlers = {
            'determineState': determine_state,
            'handleWelcome': handle_welcome,
            'handleProfileCollection': handle_profile_collection,
            'handleSchemeDiscovery': handle_scheme_discovery,
            'handleEligibilityCheck': handle_eligibility_check,
            'handleApplicationGuidance': handle_application_guidance,
            'handleError': handle_error
        }
        
        handler = handlers.get(action)
        if not handler:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
        
        result = handler(event)
        return result
        
    except Exception as e:
        print(f"Error in conversation manager: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def detect_language(text: str, current_language: str = 'en') -> str:
    """
    Detect language from text using script patterns.
    Supports language switching mid-conversation.
    """
    if not text:
        return current_language
    
    # Check for Indian language scripts
    for lang, pattern in LANGUAGE_PATTERNS.items():
        if pattern.search(text):
            return lang
    
    # Default to English if no Indian script detected
    return 'en'


def get_session_context(session_id: str) -> Dict[str, Any]:
    """Retrieve session context from DynamoDB."""
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.get_item(Key={'sessionId': session_id})
        
        if 'Item' in response:
            item = response['Item']
            # Parse context if it's a string
            context = item.get('context', {})
            if isinstance(context, str):
                context = json.loads(context)
            
            return {
                'currentState': item.get('currentState', STATES['WELCOME']),
                'context': context,
                'language': item.get('language', 'en'),
                'messages': item.get('messages', [])
            }
        
        # New session
        return {
            'currentState': STATES['WELCOME'],
            'context': {},
            'language': 'en',
            'messages': []
        }
        
    except Exception as e:
        print(f"Error getting session context: {str(e)}")
        return {
            'currentState': STATES['WELCOME'],
            'context': {},
            'language': 'en',
            'messages': []
        }


def load_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Load user profile from DynamoDB."""
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            return response['Item']
        return None
        
    except Exception as e:
        print(f"Error loading user profile: {str(e)}")
        return None


def classify_intent(user_message: str, context: Dict[str, Any], language: str) -> Tuple[str, Dict[str, Any]]:
    """
    Classify user intent using Claude to determine conversation state.
    Returns (next_state, extracted_entities)
    """
    try:
        system_prompt = """You are an intent classifier for SarkariSaathi, a government schemes assistant.

Analyze the user's message and classify it into one of these intents:
1. WELCOME - User is greeting or starting conversation
2. PROFILE_COLLECTION - User is providing demographic information (age, income, state, occupation, etc.)
3. SCHEME_DISCOVERY - User is asking about available schemes or wants recommendations
4. ELIGIBILITY_CHECK - User is asking if they qualify for a specific scheme
5. APPLICATION_GUIDANCE - User wants help applying for a scheme

Also extract any demographic information mentioned:
- age (number)
- income (number in rupees)
- state (Indian state name)
- occupation (job/profession)
- category (General, OBC, SC, ST)
- hasDisability (boolean)

Respond in JSON format:
{
  "intent": "INTENT_NAME",
  "entities": {
    "age": 35,
    "income": 200000,
    ...
  },
  "confidence": 0.95
}"""
        
        # Build context summary
        context_summary = ""
        if context.get('userProfile'):
            context_summary = f"\nCurrent user profile: {json.dumps(context['userProfile'])}"
        if context.get('currentScheme'):
            context_summary += f"\nCurrently discussing scheme: {context['currentScheme']}"
        
        messages = [
            {
                "role": "user",
                "content": f"{context_summary}\n\nUser message: {user_message}\n\nClassify this message."
            }
        ]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": messages
        }
        
        response = bedrock_runtime.invoke_model(
            modelId=CLAUDE_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text']
        
        # Parse JSON response
        # Extract JSON from markdown code blocks if present
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(response_text)
        
        intent = result.get('intent', 'WELCOME')
        entities = result.get('entities', {})
        
        # Map intent to state
        intent_to_state = {
            'WELCOME': STATES['WELCOME'],
            'PROFILE_COLLECTION': STATES['PROFILE_COLLECTION'],
            'SCHEME_DISCOVERY': STATES['SCHEME_DISCOVERY'],
            'ELIGIBILITY_CHECK': STATES['ELIGIBILITY_CHECK'],
            'APPLICATION_GUIDANCE': STATES['APPLICATION_GUIDANCE']
        }
        
        next_state = intent_to_state.get(intent, STATES['WELCOME'])
        
        return next_state, entities
        
    except Exception as e:
        print(f"Error classifying intent: {str(e)}")
        # Default to profile collection if we have no profile, otherwise scheme discovery
        if not context.get('userProfile'):
            return STATES['PROFILE_COLLECTION'], {}
        return STATES['SCHEME_DISCOVERY'], {}


def determine_state(event: Dict[str, Any]) -> Dict[str, Any]:
    """Determine next conversation state based on user message and context."""
    session_id = event.get('sessionId')
    user_message = event.get('userMessage', '')
    language = event.get('language', 'en')
    
    # Detect language switching
    detected_language = detect_language(user_message, language)
    if detected_language != language:
        print(f"Language switch detected: {language} -> {detected_language}")
        language = detected_language
    
    # Get session context
    session_data = get_session_context(session_id)
    context = session_data['context']
    
    # Load user profile if user_id is in context
    if context.get('userId'):
        user_profile = load_user_profile(context['userId'])
        if user_profile:
            context['userProfile'] = user_profile.get('demographics', {})
    
    # Classify intent and determine next state
    next_state, entities = classify_intent(user_message, context, language)
    
    # Update context with extracted entities
    if entities:
        if 'userProfile' not in context:
            context['userProfile'] = {}
        context['userProfile'].update(entities)
    
    return {
        'nextState': next_state,
        'context': context,
        'language': language,
        'entities': entities
    }


def handle_welcome(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle welcome state - greet user and explain service."""
    session_id = event.get('sessionId')
    language = event.get('language', 'en')
    context = event.get('context', {})
    
    # Check if returning user
    user_profile = context.get('userProfile', {})
    is_returning = bool(user_profile)
    
    # Generate welcome message
    if language == 'hi':
        if is_returning:
            response = f"नमस्ते! आपका फिर से स्वागत है SarkariSaathi में। मैं आपको सरकारी योजनाओं के बारे में जानकारी देने में मदद कर सकता हूं। आप क्या जानना चाहेंगे?"
        else:
            response = """नमस्ते! मैं SarkariSaathi हूं, आपका सरकारी योजना सहायक।

मैं आपकी मदद कर सकता हूं:
• सरकारी योजनाओं की खोज करने में
• पात्रता जांचने में
• आवेदन प्रक्रिया समझने में

शुरू करने के लिए, कृपया मुझे अपने बारे में बताएं - आपकी उम्र, राज्य, और आय।"""
    else:
        if is_returning:
            response = f"Welcome back to SarkariSaathi! I can help you discover government schemes. What would you like to know?"
        else:
            response = """Welcome to SarkariSaathi! I'm your government schemes assistant.

I can help you:
• Discover government schemes you're eligible for
• Check eligibility criteria
• Understand application processes

To get started, please tell me about yourself - your age, state, and income."""
    
    # Determine next state
    next_state = STATES['PROFILE_COLLECTION'] if not is_returning else STATES['SCHEME_DISCOVERY']
    
    return {
        'response': response,
        'nextState': next_state,
        'context': context,
        'language': language,
        'shouldContinue': True
    }



def handle_profile_collection(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle profile collection state - gather user demographics."""
    session_id = event.get('sessionId')
    user_message = event.get('userMessage', '')
    language = event.get('language', 'en')
    context = event.get('context', {})
    
    # Extract entities from message
    _, entities = classify_intent(user_message, context, language)
    
    # Update user profile
    user_profile = context.get('userProfile', {})
    user_profile.update(entities)
    context['userProfile'] = user_profile
    
    # Check what information is still missing
    required_fields = ['age', 'state', 'income']
    missing_fields = [f for f in required_fields if f not in user_profile or user_profile[f] is None]
    
    if missing_fields:
        # Ask for missing information
        if language == 'hi':
            field_names = {
                'age': 'उम्र',
                'state': 'राज्य',
                'income': 'वार्षिक आय'
            }
            missing_names = [field_names.get(f, f) for f in missing_fields]
            response = f"धन्यवाद! कृपया मुझे अपनी {', '.join(missing_names)} भी बताएं।"
        else:
            field_names = {
                'age': 'age',
                'state': 'state',
                'income': 'annual income'
            }
            missing_names = [field_names.get(f, f) for f in missing_fields]
            response = f"Thank you! Please also tell me your {', '.join(missing_names)}."
        
        next_state = STATES['PROFILE_COLLECTION']
    else:
        # Profile complete, move to scheme discovery
        if language == 'hi':
            response = f"""बहुत अच्छा! मैंने आपकी जानकारी सहेज ली है:
• उम्र: {user_profile.get('age')} साल
• राज्य: {user_profile.get('state')}
• वार्षिक आय: ₹{user_profile.get('income'):,}

अब मैं आपके लिए उपयुक्त योजनाएं खोज सकता हूं। आप किस प्रकार की योजनाओं में रुचि रखते हैं? (शिक्षा, स्वास्थ्य, रोजगार, कृषि, आदि)"""
        else:
            response = f"""Great! I've saved your information:
• Age: {user_profile.get('age')} years
• State: {user_profile.get('state')}
• Annual Income: ₹{user_profile.get('income'):,}

Now I can find suitable schemes for you. What type of schemes are you interested in? (Education, Healthcare, Employment, Agriculture, etc.)"""
        
        next_state = STATES['SCHEME_DISCOVERY']
    
    return {
        'response': response,
        'nextState': next_state,
        'context': context,
        'language': language,
        'shouldContinue': True
    }


def handle_scheme_discovery(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scheme discovery state - present matching schemes."""
    session_id = event.get('sessionId')
    user_message = event.get('userMessage', '')
    language = event.get('language', 'en')
    context = event.get('context', {})
    schemes_data = event.get('schemes', {})
    
    # Parse schemes data if it's a string
    if isinstance(schemes_data, str):
        schemes_data = json.loads(schemes_data)
    
    schemes = schemes_data.get('schemes', [])
    
    if not schemes:
        if language == 'hi':
            response = "क्षमा करें, मुझे आपके लिए कोई उपयुक्त योजना नहीं मिली। कृपया अपनी आवश्यकताओं को और विस्तार से बताएं।"
        else:
            response = "I'm sorry, I couldn't find any suitable schemes for you. Please tell me more about your needs."
        
        return {
            'response': response,
            'nextState': STATES['SCHEME_DISCOVERY'],
            'context': context,
            'language': language,
            'shouldContinue': True
        }
    
    # Generate response with scheme recommendations
    if language == 'hi':
        response_parts = [f"मैंने आपके लिए {len(schemes)} योजनाएं पाई हैं:\n"]
        
        for i, scheme in enumerate(schemes[:5], 1):
            name = scheme.get('name', 'Unknown')
            category = scheme.get('category', 'N/A')
            eligibility_score = scheme.get('eligibilityScore', 0)
            benefits = scheme.get('benefits', 'N/A')
            
            response_parts.append(f"\n{i}. **{name}**")
            response_parts.append(f"   श्रेणी: {category}")
            response_parts.append(f"   पात्रता मिलान: {eligibility_score:.0%}")
            response_parts.append(f"   लाभ: {benefits[:200]}...")
        
        response_parts.append("\n\nकिसी योजना के बारे में अधिक जानने के लिए, उसका नाम बताएं या नंबर बताएं।")
        response = '\n'.join(response_parts)
    else:
        response_parts = [f"I found {len(schemes)} schemes for you:\n"]
        
        for i, scheme in enumerate(schemes[:5], 1):
            name = scheme.get('name', 'Unknown')
            category = scheme.get('category', 'N/A')
            eligibility_score = scheme.get('eligibilityScore', 0)
            benefits = scheme.get('benefits', 'N/A')
            
            response_parts.append(f"\n{i}. **{name}**")
            response_parts.append(f"   Category: {category}")
            response_parts.append(f"   Eligibility Match: {eligibility_score:.0%}")
            response_parts.append(f"   Benefits: {benefits[:200]}...")
        
        response_parts.append("\n\nTo learn more about a scheme, tell me its name or number.")
        response = '\n'.join(response_parts)
    
    # Store schemes in context
    context['discoveredSchemes'] = schemes
    
    return {
        'response': response,
        'nextState': STATES['ELIGIBILITY_CHECK'],
        'context': context,
        'language': language,
        'shouldContinue': True
    }


def handle_eligibility_check(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle eligibility check state - explain eligibility for specific scheme."""
    session_id = event.get('sessionId')
    user_message = event.get('userMessage', '')
    language = event.get('language', 'en')
    context = event.get('context', {})
    
    # Try to identify which scheme user is asking about
    discovered_schemes = context.get('discoveredSchemes', [])
    
    # Simple matching - look for scheme name or number in message
    selected_scheme = None
    message_lower = user_message.lower()
    
    # Check for number (1, 2, 3, etc.)
    for i, scheme in enumerate(discovered_schemes, 1):
        if str(i) in user_message or scheme.get('name', '').lower() in message_lower:
            selected_scheme = scheme
            break
    
    if not selected_scheme and discovered_schemes:
        # Default to first scheme if unclear
        selected_scheme = discovered_schemes[0]
    
    if not selected_scheme:
        if language == 'hi':
            response = "कृपया बताएं कि आप किस योजना के बारे में जानना चाहते हैं।"
        else:
            response = "Please tell me which scheme you'd like to know about."
        
        return {
            'response': response,
            'nextState': STATES['ELIGIBILITY_CHECK'],
            'context': context,
            'language': language,
            'shouldContinue': True
        }
    
    # Generate detailed eligibility explanation
    user_profile = context.get('userProfile', {})
    
    if language == 'hi':
        response_parts = [f"**{selected_scheme.get('name')}** के बारे में:\n"]
        response_parts.append(f"विवरण: {selected_scheme.get('description', 'N/A')}\n")
        response_parts.append(f"लाभ: {selected_scheme.get('benefits', 'N/A')}\n")
        response_parts.append(f"पात्रता मिलान: {selected_scheme.get('eligibilityScore', 0):.0%}\n")
        
        if selected_scheme.get('eligibilityScore', 0) >= 0.7:
            response_parts.append("✅ आप इस योजना के लिए पात्र हैं!\n")
        elif selected_scheme.get('eligibilityScore', 0) >= 0.5:
            response_parts.append("⚠️ आप आंशिक रूप से पात्र हो सकते हैं। कुछ मानदंड जांचने की आवश्यकता है।\n")
        else:
            response_parts.append("❌ आप इस योजना के लिए पात्र नहीं हो सकते हैं।\n")
        
        response_parts.append(f"\nआवश्यक दस्तावेज़: {', '.join(selected_scheme.get('requiredDocuments', []))}")
        response_parts.append(f"\n\nक्या आप इस योजना के लिए आवेदन करना चाहेंगे?")
        response = '\n'.join(response_parts)
    else:
        response_parts = [f"**{selected_scheme.get('name')}**:\n"]
        response_parts.append(f"Description: {selected_scheme.get('description', 'N/A')}\n")
        response_parts.append(f"Benefits: {selected_scheme.get('benefits', 'N/A')}\n")
        response_parts.append(f"Eligibility Match: {selected_scheme.get('eligibilityScore', 0):.0%}\n")
        
        if selected_scheme.get('eligibilityScore', 0) >= 0.7:
            response_parts.append("✅ You are eligible for this scheme!\n")
        elif selected_scheme.get('eligibilityScore', 0) >= 0.5:
            response_parts.append("⚠️ You may be partially eligible. Some criteria need verification.\n")
        else:
            response_parts.append("❌ You may not be eligible for this scheme.\n")
        
        response_parts.append(f"\nRequired Documents: {', '.join(selected_scheme.get('requiredDocuments', []))}")
        response_parts.append(f"\n\nWould you like help applying for this scheme?")
        response = '\n'.join(response_parts)
    
    # Store current scheme in context
    context['currentScheme'] = selected_scheme
    
    return {
        'response': response,
        'nextState': STATES['APPLICATION_GUIDANCE'],
        'context': context,
        'language': language,
        'shouldContinue': True
    }


def handle_application_guidance(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle application guidance state - guide user through application process."""
    session_id = event.get('sessionId')
    user_message = event.get('userMessage', '')
    language = event.get('language', 'en')
    context = event.get('context', {})
    
    current_scheme = context.get('currentScheme')
    
    if not current_scheme:
        if language == 'hi':
            response = "कृपया पहले एक योजना चुनें जिसके लिए आप आवेदन करना चाहते हैं।"
        else:
            response = "Please first select a scheme you'd like to apply for."
        
        return {
            'response': response,
            'nextState': STATES['SCHEME_DISCOVERY'],
            'context': context,
            'language': language,
            'shouldContinue': True
        }
    
    # Generate application guidance
    if language == 'hi':
        response_parts = [f"**{current_scheme.get('name')}** के लिए आवेदन प्रक्रिया:\n"]
        response_parts.append(f"{current_scheme.get('applicationProcess', 'जानकारी उपलब्ध नहीं है')}\n")
        response_parts.append(f"\n**आवश्यक दस्तावेज़:**")
        
        for doc in current_scheme.get('requiredDocuments', []):
            response_parts.append(f"• {doc}")
        
        contact_info = current_scheme.get('contactInfo', '')
        if contact_info:
            response_parts.append(f"\n**संपर्क जानकारी:** {contact_info}")
        
        response_parts.append("\n\n💡 सुझाव: आवेदन करने से पहले सभी दस्तावेज़ तैयार रखें।")
        response_parts.append("\n\nक्या आपको किसी और योजना के बारे में जानना है?")
        response = '\n'.join(response_parts)
    else:
        response_parts = [f"**{current_scheme.get('name')}** Application Process:\n"]
        response_parts.append(f"{current_scheme.get('applicationProcess', 'Information not available')}\n")
        response_parts.append(f"\n**Required Documents:**")
        
        for doc in current_scheme.get('requiredDocuments', []):
            response_parts.append(f"• {doc}")
        
        contact_info = current_scheme.get('contactInfo', '')
        if contact_info:
            response_parts.append(f"\n**Contact Information:** {contact_info}")
        
        response_parts.append("\n\n💡 Tip: Keep all documents ready before applying.")
        response_parts.append("\n\nWould you like to know about any other schemes?")
        response = '\n'.join(response_parts)
    
    return {
        'response': response,
        'nextState': STATES['SCHEME_DISCOVERY'],
        'context': context,
        'language': language,
        'shouldContinue': True
    }


def handle_error(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle errors gracefully with user-friendly messages."""
    session_id = event.get('sessionId')
    error = event.get('error', {})
    language = event.get('language', 'en')
    
    error_message = error.get('Error', 'Unknown error')
    
    if language == 'hi':
        response = f"क्षमा करें, कुछ गलत हो गया। कृपया पुनः प्रयास करें या अपना प्रश्न दूसरे तरीके से पूछें।"
    else:
        response = f"I'm sorry, something went wrong. Please try again or rephrase your question."
    
    return {
        'response': response,
        'error': error_message,
        'language': language
    }

"""
Bedrock RAG Service

Integrates Amazon Bedrock with Claude 3.5 Sonnet for conversational AI
with RAG context injection from OpenSearch scheme results.
"""

import json
import os
import boto3
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

# Model configuration
CLAUDE_MODEL_ID = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# Token limits for cost control
MAX_INPUT_TOKENS = 100000  # Claude 3.5 Sonnet supports up to 200K
MAX_OUTPUT_TOKENS = 4096
TOKEN_COST_PER_1K_INPUT = 0.003  # USD
TOKEN_COST_PER_1K_OUTPUT = 0.015  # USD


def count_tokens_estimate(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ≈ 4 characters)."""
    return len(text) // 4


def build_system_prompt() -> str:
    """Build system prompt for SarkariSaathi assistant."""
    return """You are SarkariSaathi, a helpful AI assistant that helps Indian citizens discover and apply for government schemes and benefits.

Your role:
- Help users understand government schemes in simple, clear language
- Explain eligibility criteria and application processes
- Guide users through document requirements
- Provide accurate information about benefits and deadlines
- Be empathetic and patient, especially with users who have limited digital literacy

Guidelines:
- Use simple, non-technical language
- Break down complex information into easy steps
- Always verify eligibility before recommending schemes
- Provide specific, actionable guidance
- Be culturally sensitive and respectful
- If you don't know something, admit it and suggest alternatives
- Focus on the most relevant schemes for the user's situation

When discussing schemes:
- Explain benefits in concrete terms (amounts, coverage, duration)
- List required documents clearly
- Mention application deadlines prominently
- Provide contact information for further help
- Warn about common mistakes or issues"""


def build_rag_context(schemes: List[Dict[str, Any]]) -> str:
    """Build RAG context from scheme search results."""
    if not schemes:
        return "No specific schemes found matching the user's criteria."
    
    context_parts = ["Here are the relevant government schemes for this user:\n"]
    
    for i, scheme_result in enumerate(schemes, 1):
        scheme = scheme_result.get('scheme', {})
        eligibility_score = scheme_result.get('eligibilityScore', 0)
        
        context_parts.append(f"\n{i}. {scheme.get('name', 'Unknown Scheme')}")
        context_parts.append(f"   Category: {scheme.get('category', 'N/A')}")
        context_parts.append(f"   Eligibility Match: {eligibility_score:.0%}")
        context_parts.append(f"   Description: {scheme.get('description', 'N/A')}")
        context_parts.append(f"   Benefits: {scheme.get('benefits', 'N/A')}")
        context_parts.append(f"   Required Documents: {', '.join(scheme.get('requiredDocuments', []))}")
        context_parts.append(f"   Application: {scheme.get('applicationProcess', 'N/A')}")
        context_parts.append(f"   Contact: {scheme.get('contactInfo', 'N/A')}")
        
        eligibility = scheme.get('eligibility', {})
        if eligibility:
            context_parts.append(f"   Eligibility Criteria:")
            context_parts.append(f"     - Age: {eligibility.get('ageMin', 0)}-{eligibility.get('ageMax', 999)} years")
            context_parts.append(f"     - Income: ₹{eligibility.get('incomeMin', 0):,} - ₹{eligibility.get('incomeMax', 999999999):,}")
            context_parts.append(f"     - States: {', '.join(eligibility.get('allowedStates', ['All India']))}")
    
    return '\n'.join(context_parts)


def build_user_context(user_profile: Dict[str, Any]) -> str:
    """Build user context from profile."""
    if not user_profile:
        return "No user profile available."
    
    context_parts = ["User Profile:"]
    
    if user_profile.get('age'):
        context_parts.append(f"- Age: {user_profile['age']} years")
    if user_profile.get('income') is not None:
        context_parts.append(f"- Annual Income: ₹{user_profile['income']:,}")
    if user_profile.get('state'):
        context_parts.append(f"- State: {user_profile['state']}")
    if user_profile.get('category'):
        context_parts.append(f"- Category: {user_profile['category']}")
    if user_profile.get('occupation'):
        context_parts.append(f"- Occupation: {user_profile['occupation']}")
    if user_profile.get('hasDisability'):
        context_parts.append(f"- Has Disability: Yes")
    
    return '\n'.join(context_parts)


def generate_response(
    user_message: str,
    rag_context: str,
    user_profile: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, str]]] = None,
    language: str = 'en'
) -> Dict[str, Any]:
    """
    Generate response using Claude 3.5 Sonnet with RAG context.
    
    Args:
        user_message: User's current message
        rag_context: Context from OpenSearch scheme results
        user_profile: User demographic information
        conversation_history: Previous conversation turns
        language: Response language (en, hi, etc.)
        
    Returns:
        Response with text, token counts, and cost estimate
    """
    try:
        # Build system prompt
        system_prompt = build_system_prompt()
        
        # Add language instruction
        if language != 'en':
            language_names = {
                'hi': 'Hindi',
                'ta': 'Tamil',
                'te': 'Telugu',
                'bn': 'Bengali',
                'mr': 'Marathi'
            }
            lang_name = language_names.get(language, language)
            system_prompt += f"\n\nIMPORTANT: Respond in {lang_name} language."
        
        # Build user context
        user_context = build_user_context(user_profile)
        
        # Build messages
        messages = []
        
        # Add conversation history
        if conversation_history:
            for turn in conversation_history[-5:]:  # Keep last 5 turns for context
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })
        
        # Add current message with RAG context
        current_message = f"""{user_context}

{rag_context}

User Question: {user_message}

Please provide a helpful response based on the user's profile and the relevant schemes above."""
        
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        # Estimate input tokens
        input_text = system_prompt + json.dumps(messages)
        input_tokens_estimate = count_tokens_estimate(input_text)
        
        # Check token limits
        if input_tokens_estimate > MAX_INPUT_TOKENS:
            # Truncate RAG context if too long
            rag_context = rag_context[:10000]
            current_message = f"""{user_context}

{rag_context}

User Question: {user_message}

Please provide a helpful response based on the user's profile and the relevant schemes above."""
            messages[-1]["content"] = current_message
        
        # Prepare request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": TEMPERATURE,
            "system": system_prompt,
            "messages": messages
        }
        
        # Invoke model
        response = bedrock_runtime.invoke_model(
            modelId=CLAUDE_MODEL_ID,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        # Extract response text
        response_text = ""
        for content in response_body.get('content', []):
            if content.get('type') == 'text':
                response_text += content.get('text', '')
        
        # Get token usage
        usage = response_body.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        
        # Calculate cost
        cost = (input_tokens / 1000 * TOKEN_COST_PER_1K_INPUT) + \
               (output_tokens / 1000 * TOKEN_COST_PER_1K_OUTPUT)
        
        return {
            'response': response_text,
            'inputTokens': input_tokens,
            'outputTokens': output_tokens,
            'totalTokens': input_tokens + output_tokens,
            'estimatedCost': cost,
            'model': CLAUDE_MODEL_ID,
            'stopReason': response_body.get('stop_reason')
        }
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        raise


def generate_streaming_response(
    user_message: str,
    rag_context: str,
    user_profile: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, str]]] = None,
    language: str = 'en'
) -> Iterator[Dict[str, Any]]:
    """
    Generate streaming response using Claude 3.5 Sonnet.
    Yields chunks of response as they are generated.
    """
    try:
        # Build system prompt
        system_prompt = build_system_prompt()
        
        if language != 'en':
            language_names = {
                'hi': 'Hindi',
                'ta': 'Tamil',
                'te': 'Telugu',
                'bn': 'Bengali',
                'mr': 'Marathi'
            }
            lang_name = language_names.get(language, language)
            system_prompt += f"\n\nIMPORTANT: Respond in {lang_name} language."
        
        # Build contexts
        user_context = build_user_context(user_profile)
        
        # Build messages
        messages = []
        if conversation_history:
            for turn in conversation_history[-5:]:
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })
        
        current_message = f"""{user_context}

{rag_context}

User Question: {user_message}

Please provide a helpful response based on the user's profile and the relevant schemes above."""
        
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        # Prepare request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": TEMPERATURE,
            "system": system_prompt,
            "messages": messages
        }
        
        # Invoke model with streaming
        response = bedrock_runtime.invoke_model_with_response_stream(
            modelId=CLAUDE_MODEL_ID,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Stream response chunks
        stream = response.get('body')
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_data = json.loads(chunk.get('bytes').decode())
                    
                    if chunk_data.get('type') == 'content_block_delta':
                        delta = chunk_data.get('delta', {})
                        if delta.get('type') == 'text_delta':
                            text = delta.get('text', '')
                            yield {
                                'type': 'text',
                                'text': text
                            }
                    
                    elif chunk_data.get('type') == 'message_stop':
                        yield {
                            'type': 'stop',
                            'stopReason': chunk_data.get('stop_reason')
                        }
        
    except Exception as e:
        print(f"Error in streaming response: {str(e)}")
        yield {
            'type': 'error',
            'error': str(e)
        }


def lambda_handler(event, context):
    """
    Lambda handler for Bedrock RAG service.
    
    Expected event format:
    {
        "userMessage": "Tell me about education schemes",
        "ragContext": "...",  // From eligibility matching service
        "userProfile": {...},
        "conversationHistory": [...],
        "language": "en",
        "streaming": false
    }
    """
    try:
        user_message = event.get('userMessage', '')
        rag_context = event.get('ragContext', '')
        user_profile = event.get('userProfile', {})
        conversation_history = event.get('conversationHistory', [])
        language = event.get('language', 'en')
        streaming = event.get('streaming', False)
        
        if not user_message:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'userMessage is required'
                })
            }
        
        if streaming:
            # For streaming, return error as Lambda doesn't support streaming responses directly
            # This would need API Gateway WebSocket or EventBridge integration
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Streaming not supported in Lambda. Use Step Functions or API Gateway WebSocket.'
                })
            }
        
        # Generate response
        result = generate_response(
            user_message,
            rag_context,
            user_profile,
            conversation_history,
            language
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

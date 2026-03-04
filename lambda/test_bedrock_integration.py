"""
Unit Tests for Bedrock RAG Integration

Tests for Amazon Bedrock integration with Claude 3.5 Sonnet including:
- Prompt template generation with various user contexts
- RAG context injection and response quality
- Token limiting and cost controls

**Validates: Requirements 3.2, 4.2**
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
import os

# Set environment variables before importing
os.environ['AWS_REGION'] = 'ap-south-1'

# Import the Bedrock RAG service
import bedrock_rag_service


class TestPromptTemplateGeneration:
    """
    Tests for prompt template generation with various user contexts.
    
    **Validates: Requirement 3.2** - Explain schemes in simple, non-technical language
    **Validates: Requirement 4.2** - Break down complex eligibility into simple questions
    """
    
    def test_system_prompt_includes_simple_language_instruction(self):
        """Test that system prompt instructs Claude to use simple language."""
        system_prompt = bedrock_rag_service.build_system_prompt()
        
        assert "simple" in system_prompt.lower()
        assert "non-technical" in system_prompt.lower()
        assert "clear" in system_prompt.lower()
        
    def test_system_prompt_includes_eligibility_guidance(self):
        """Test that system prompt includes guidance for eligibility questions."""
        system_prompt = bedrock_rag_service.build_system_prompt()
        
        assert "eligibility" in system_prompt.lower()
        assert "break down" in system_prompt.lower() or "steps" in system_prompt.lower()
    
    def test_user_context_with_complete_profile(self):
        """Test user context generation with complete profile."""
        user_profile = {
            "age": 35,
            "income": 250000,
            "state": "Karnataka",
            "category": "OBC",
            "occupation": "Farmer",
            "hasDisability": False
        }
        
        context = bedrock_rag_service.build_user_context(user_profile)
        
        assert "35" in context
        assert "250,000" in context or "250000" in context
        assert "Karnataka" in context
        assert "OBC" in context
        assert "Farmer" in context
    
    def test_user_context_with_minimal_profile(self):
        """Test user context generation with minimal profile information."""
        user_profile = {
            "age": 25,
            "state": "Delhi"
        }
        
        context = bedrock_rag_service.build_user_context(user_profile)
        
        assert "25" in context
        assert "Delhi" in context
        assert "User Profile" in context
    
    def test_user_context_with_empty_profile(self):
        """Test user context generation with empty profile."""
        user_profile = {}
        
        context = bedrock_rag_service.build_user_context(user_profile)
        
        assert "No user profile available" in context
    
    def test_user_context_with_disability(self):
        """Test user context includes disability information."""
        user_profile = {
            "age": 40,
            "hasDisability": True
        }
        
        context = bedrock_rag_service.build_user_context(user_profile)
        
        assert "Disability" in context
        assert "Yes" in context
    
    def test_user_context_with_zero_income(self):
        """Test user context handles zero income correctly."""
        user_profile = {
            "age": 22,
            "income": 0,
            "state": "Bihar"
        }
        
        context = bedrock_rag_service.build_user_context(user_profile)
        
        assert "0" in context or "₹0" in context
        assert "Bihar" in context
    
    def test_language_instruction_added_for_hindi(self):
        """Test that language instruction is added for Hindi responses."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test response'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="Tell me about schemes",
                rag_context="",
                user_profile={},
                language='hi'
            )
            
            # Verify the call was made
            assert mock_bedrock.invoke_model.called
            call_args = mock_bedrock.invoke_model.call_args
            body = json.loads(call_args[1]['body'])
            
            # Check system prompt includes Hindi instruction
            assert 'Hindi' in body['system']
    
    def test_language_instruction_added_for_tamil(self):
        """Test that language instruction is added for Tamil responses."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test response'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="Tell me about schemes",
                rag_context="",
                user_profile={},
                language='ta'
            )
            
            # Verify the call was made
            assert mock_bedrock.invoke_model.called
            call_args = mock_bedrock.invoke_model.call_args
            body = json.loads(call_args[1]['body'])
            
            # Check system prompt includes Tamil instruction
            assert 'Tamil' in body['system']


class TestRAGContextInjection:
    """
    Tests for RAG context injection from OpenSearch results.
    
    **Validates: Requirement 3.2** - Explain schemes in simple language
    """
    
    def test_rag_context_with_single_scheme(self):
        """Test RAG context generation with a single scheme."""
        schemes = [
            {
                "scheme": {
                    "name": "PM-KISAN",
                    "category": "Agriculture",
                    "description": "Direct income support to farmers",
                    "benefits": "₹6000 per year",
                    "requiredDocuments": ["Aadhaar", "Land Records"],
                    "applicationProcess": "Apply online at pmkisan.gov.in",
                    "contactInfo": "1800-123-4567",
                    "eligibility": {
                        "ageMin": 18,
                        "ageMax": 100,
                        "incomeMin": 0,
                        "incomeMax": 500000,
                        "allowedStates": ["All India"]
                    }
                },
                "eligibilityScore": 0.85
            }
        ]
        
        context = bedrock_rag_service.build_rag_context(schemes)
        
        assert "PM-KISAN" in context
        assert "Agriculture" in context
        assert "85%" in context
        assert "₹6000" in context
        assert "Aadhaar" in context
        assert "Land Records" in context
    
    def test_rag_context_with_multiple_schemes(self):
        """Test RAG context generation with multiple schemes."""
        schemes = [
            {
                "scheme": {
                    "name": "Scheme A",
                    "category": "Healthcare",
                    "description": "Health insurance",
                    "benefits": "₹5 lakh coverage",
                    "requiredDocuments": ["Aadhaar"],
                    "applicationProcess": "Apply online",
                    "contactInfo": "1800-111-111",
                    "eligibility": {
                        "ageMin": 0,
                        "ageMax": 100,
                        "incomeMin": 0,
                        "incomeMax": 500000,
                        "allowedStates": ["All India"]
                    }
                },
                "eligibilityScore": 0.90
            },
            {
                "scheme": {
                    "name": "Scheme B",
                    "category": "Education",
                    "description": "Scholarship for students",
                    "benefits": "₹50,000 per year",
                    "requiredDocuments": ["Aadhaar", "Income Certificate"],
                    "applicationProcess": "Apply through school",
                    "contactInfo": "1800-222-222",
                    "eligibility": {
                        "ageMin": 5,
                        "ageMax": 25,
                        "incomeMin": 0,
                        "incomeMax": 200000,
                        "allowedStates": ["All India"]
                    }
                },
                "eligibilityScore": 0.75
            }
        ]
        
        context = bedrock_rag_service.build_rag_context(schemes)
        
        assert "Scheme A" in context
        assert "Scheme B" in context
        assert "Healthcare" in context
        assert "Education" in context
        assert "90%" in context
        assert "75%" in context
    
    def test_rag_context_with_empty_schemes(self):
        """Test RAG context generation with no schemes."""
        schemes = []
        
        context = bedrock_rag_service.build_rag_context(schemes)
        
        assert "No specific schemes found" in context
    
    def test_rag_context_includes_eligibility_criteria(self):
        """Test that RAG context includes detailed eligibility criteria."""
        schemes = [
            {
                "scheme": {
                    "name": "Test Scheme",
                    "category": "Social Welfare",
                    "description": "Test description",
                    "benefits": "Test benefits",
                    "requiredDocuments": ["Doc1"],
                    "applicationProcess": "Test process",
                    "contactInfo": "Test contact",
                    "eligibility": {
                        "ageMin": 18,
                        "ageMax": 60,
                        "incomeMin": 0,
                        "incomeMax": 300000,
                        "allowedStates": ["Karnataka", "Tamil Nadu"]
                    }
                },
                "eligibilityScore": 0.80
            }
        ]
        
        context = bedrock_rag_service.build_rag_context(schemes)
        
        assert "18-60 years" in context
        assert "₹0" in context or "0" in context
        assert "₹3,00,000" in context or "300000" in context or "₹300,000" in context
        assert "Karnataka" in context
        assert "Tamil Nadu" in context
    
    def test_rag_context_injection_in_generate_response(self):
        """Test that RAG context is properly injected into the prompt."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test response'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            rag_context = "Scheme: PM-KISAN\nBenefits: ₹6000 per year"
            
            result = bedrock_rag_service.generate_response(
                user_message="Tell me about farming schemes",
                rag_context=rag_context,
                user_profile={"age": 35, "occupation": "Farmer"},
                language='en'
            )
            
            # Verify the call was made
            assert mock_bedrock.invoke_model.called
            call_args = mock_bedrock.invoke_model.call_args
            body = json.loads(call_args[1]['body'])
            
            # Check that RAG context is in the messages
            messages = body['messages']
            assert len(messages) > 0
            assert "PM-KISAN" in messages[-1]['content']
            assert "₹6000" in messages[-1]['content']


class TestTokenLimitingAndCostControls:
    """
    Tests for token counting, limiting, and cost control mechanisms.
    
    **Validates: Requirement 4.2** - Efficient processing with cost controls
    """
    
    def test_token_count_estimate(self):
        """Test token count estimation function."""
        text = "Hello, this is a test message."
        tokens = bedrock_rag_service.count_tokens_estimate(text)
        
        # Rough estimate: 1 token ≈ 4 characters
        expected_tokens = len(text) // 4
        assert tokens == expected_tokens
    
    def test_token_count_estimate_with_long_text(self):
        """Test token count estimation with long text."""
        text = "a" * 10000
        tokens = bedrock_rag_service.count_tokens_estimate(text)
        
        assert tokens == 2500  # 10000 / 4
    
    def test_max_input_tokens_constant(self):
        """Test that MAX_INPUT_TOKENS is set correctly."""
        assert bedrock_rag_service.MAX_INPUT_TOKENS == 100000
        assert bedrock_rag_service.MAX_INPUT_TOKENS <= 200000  # Claude 3.5 limit
    
    def test_max_output_tokens_constant(self):
        """Test that MAX_OUTPUT_TOKENS is set correctly."""
        assert bedrock_rag_service.MAX_OUTPUT_TOKENS == 4096
    
    def test_token_cost_constants(self):
        """Test that token cost constants are defined."""
        assert bedrock_rag_service.TOKEN_COST_PER_1K_INPUT == 0.003
        assert bedrock_rag_service.TOKEN_COST_PER_1K_OUTPUT == 0.015
    
    def test_cost_calculation_in_response(self):
        """Test that cost is calculated and returned in response."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test response'}],
                'usage': {
                    'input_tokens': 1000,
                    'output_tokens': 500
                },
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="Test message",
                rag_context="Test context",
                user_profile={},
                language='en'
            )
            
            # Verify cost calculation
            assert 'estimatedCost' in result
            expected_cost = (1000 / 1000 * 0.003) + (500 / 1000 * 0.015)
            assert abs(result['estimatedCost'] - expected_cost) < 0.0001
    
    def test_token_usage_returned_in_response(self):
        """Test that token usage is returned in response."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test response'}],
                'usage': {
                    'input_tokens': 1500,
                    'output_tokens': 800
                },
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="Test message",
                rag_context="Test context",
                user_profile={},
                language='en'
            )
            
            assert result['inputTokens'] == 1500
            assert result['outputTokens'] == 800
            assert result['totalTokens'] == 2300
    
    def test_rag_context_truncation_when_too_long(self):
        """Test that RAG context is truncated when input exceeds token limit."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test response'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            # Create very long RAG context
            long_context = "a" * 500000  # 125k tokens estimated
            
            result = bedrock_rag_service.generate_response(
                user_message="Test message",
                rag_context=long_context,
                user_profile={},
                language='en'
            )
            
            # Verify the call was made (context should be truncated)
            assert mock_bedrock.invoke_model.called
            call_args = mock_bedrock.invoke_model.call_args
            body = json.loads(call_args[1]['body'])
            
            # Check that the message content is not the full long context
            message_content = body['messages'][-1]['content']
            assert len(message_content) < len(long_context)
    
    def test_conversation_history_limited_to_last_5_turns(self):
        """Test that conversation history is limited to last 5 turns."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test response'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            # Create 10 conversation turns
            conversation_history = [
                {"role": "user", "content": f"Message {i}"}
                for i in range(10)
            ]
            
            result = bedrock_rag_service.generate_response(
                user_message="Current message",
                rag_context="",
                user_profile={},
                conversation_history=conversation_history,
                language='en'
            )
            
            # Verify only last 5 turns are included
            call_args = mock_bedrock.invoke_model.call_args
            body = json.loads(call_args[1]['body'])
            messages = body['messages']
            
            # Should have 5 history messages + 1 current message
            assert len(messages) == 6


class TestBedrockAPIIntegration:
    """
    Tests for Bedrock API integration and error handling.
    """
    
    def test_successful_response_generation(self):
        """Test successful response generation from Bedrock."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [
                    {'type': 'text', 'text': 'This is a helpful response about government schemes.'}
                ],
                'usage': {
                    'input_tokens': 500,
                    'output_tokens': 200
                },
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="Tell me about education schemes",
                rag_context="Scheme: Scholarship Program",
                user_profile={"age": 20, "occupation": "Student"},
                language='en'
            )
            
            assert result['response'] == 'This is a helpful response about government schemes.'
            assert result['model'] == 'anthropic.claude-3-5-sonnet-20240620-v1:0'
            assert result['stopReason'] == 'end_turn'
    
    def test_bedrock_api_error_handling(self):
        """Test error handling when Bedrock API fails."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_bedrock.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'InvokeModel'
            )
            
            with pytest.raises(ClientError):
                bedrock_rag_service.generate_response(
                    user_message="Test message",
                    rag_context="",
                    user_profile={},
                    language='en'
                )
    
    def test_model_id_is_correct(self):
        """Test that the correct Claude model ID is used."""
        assert bedrock_rag_service.CLAUDE_MODEL_ID == 'anthropic.claude-3-5-sonnet-20240620-v1:0'
    
    def test_temperature_setting(self):
        """Test that temperature is set correctly."""
        assert bedrock_rag_service.TEMPERATURE == 0.7
    
    def test_request_body_structure(self):
        """Test that request body has correct structure."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Test'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            bedrock_rag_service.generate_response(
                user_message="Test",
                rag_context="",
                user_profile={},
                language='en'
            )
            
            call_args = mock_bedrock.invoke_model.call_args
            body = json.loads(call_args[1]['body'])
            
            assert 'anthropic_version' in body
            assert body['anthropic_version'] == 'bedrock-2023-05-31'
            assert 'max_tokens' in body
            assert body['max_tokens'] == 4096
            assert 'temperature' in body
            assert body['temperature'] == 0.7
            assert 'system' in body
            assert 'messages' in body


class TestLambdaHandler:
    """
    Tests for the Lambda handler function.
    """
    
    def test_lambda_handler_success(self):
        """Test successful Lambda handler execution."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'type': 'text', 'text': 'Response'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            event = {
                'userMessage': 'Tell me about schemes',
                'ragContext': 'Scheme info',
                'userProfile': {'age': 30},
                'language': 'en'
            }
            
            response = bedrock_rag_service.lambda_handler(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'response' in body
            assert 'inputTokens' in body
            assert 'outputTokens' in body
    
    def test_lambda_handler_missing_user_message(self):
        """Test Lambda handler with missing userMessage."""
        event = {
            'ragContext': 'Scheme info',
            'userProfile': {'age': 30}
        }
        
        response = bedrock_rag_service.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'userMessage' in body['error']
    
    def test_lambda_handler_streaming_not_supported(self):
        """Test that streaming returns error in Lambda."""
        event = {
            'userMessage': 'Test',
            'streaming': True
        }
        
        response = bedrock_rag_service.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Streaming not supported' in body['error']
    
    def test_lambda_handler_error_handling(self):
        """Test Lambda handler error handling."""
        with patch('bedrock_rag_service.generate_response') as mock_generate:
            mock_generate.side_effect = Exception('Test error')
            
            event = {
                'userMessage': 'Test message',
                'ragContext': '',
                'userProfile': {}
            }
            
            response = bedrock_rag_service.lambda_handler(event, None)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body


class TestResponseQuality:
    """
    Tests for response quality and content validation.
    
    **Validates: Requirement 3.2** - Simple, non-technical language
    **Validates: Requirement 4.2** - Break down complex eligibility
    """
    
    def test_response_contains_text(self):
        """Test that response contains actual text content."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [
                    {'type': 'text', 'text': 'Here are the schemes you qualify for.'}
                ],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="What schemes am I eligible for?",
                rag_context="Scheme: PM-KISAN",
                user_profile={"age": 35, "occupation": "Farmer"},
                language='en'
            )
            
            assert len(result['response']) > 0
            assert isinstance(result['response'], str)
    
    def test_multiple_content_blocks_concatenated(self):
        """Test that multiple content blocks are concatenated."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [
                    {'type': 'text', 'text': 'First part. '},
                    {'type': 'text', 'text': 'Second part.'}
                ],
                'usage': {'input_tokens': 100, 'output_tokens': 50},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="Test",
                rag_context="",
                user_profile={},
                language='en'
            )
            
            assert result['response'] == 'First part. Second part.'
    
    def test_empty_response_handling(self):
        """Test handling of empty response from Bedrock."""
        with patch('bedrock_rag_service.bedrock_runtime') as mock_bedrock:
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [],
                'usage': {'input_tokens': 100, 'output_tokens': 0},
                'stop_reason': 'end_turn'
            }).encode()
            mock_bedrock.invoke_model.return_value = mock_response
            
            result = bedrock_rag_service.generate_response(
                user_message="Test",
                rag_context="",
                user_profile={},
                language='en'
            )
            
            assert result['response'] == ''
            assert result['outputTokens'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

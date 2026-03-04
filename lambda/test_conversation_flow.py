"""
Unit Tests for Conversation Flow

Tests state transitions, context retention, language switching, and session management
for the SarkariSaathi conversation manager.

**Validates: Requirements 2.2, 6.2**
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

# Import conversation manager functions
import conversation_manager


class TestStateTransitions:
    """Test conversation state transitions with various user inputs."""
    
    def test_welcome_to_profile_collection_for_new_user(self):
        """Test transition from Welcome to ProfileCollection for new users."""
        event = {
            'sessionId': 'test-session-1',
            'language': 'en',
            'context': {}
        }
        
        result = conversation_manager.handle_welcome(event)
        
        assert result['nextState'] == conversation_manager.STATES['PROFILE_COLLECTION']
        assert 'Welcome to SarkariSaathi' in result['response']
        assert result['shouldContinue'] is True
    
    def test_welcome_to_scheme_discovery_for_returning_user(self):
        """Test transition from Welcome to SchemeDiscovery for returning users."""
        event = {
            'sessionId': 'test-session-2',
            'language': 'en',
            'context': {
                'userProfile': {
                    'age': 30,
                    'state': 'Maharashtra',
                    'income': 300000
                }
            }
        }
        
        result = conversation_manager.handle_welcome(event)
        
        assert result['nextState'] == conversation_manager.STATES['SCHEME_DISCOVERY']
        assert 'Welcome back' in result['response']
        assert result['shouldContinue'] is True
    
    def test_profile_collection_stays_when_info_missing(self):
        """Test ProfileCollection state remains when required info is missing."""
        event = {
            'sessionId': 'test-session-3',
            'userMessage': 'I am 25 years old',
            'language': 'en',
            'context': {
                'userProfile': {
                    'age': 25
                }
            }
        }
        
        with patch('conversation_manager.classify_intent') as mock_classify:
            mock_classify.return_value = (conversation_manager.STATES['PROFILE_COLLECTION'], {})
            
            result = conversation_manager.handle_profile_collection(event)
            
            assert result['nextState'] == conversation_manager.STATES['PROFILE_COLLECTION']
            assert 'state' in result['response'].lower() or 'income' in result['response'].lower()
    
    def test_profile_collection_to_scheme_discovery_when_complete(self):
        """Test transition from ProfileCollection to SchemeDiscovery when profile is complete."""
        event = {
            'sessionId': 'test-session-4',
            'userMessage': 'My income is 200000',
            'language': 'en',
            'context': {
                'userProfile': {
                    'age': 25,
                    'state': 'Karnataka',
                    'income': 200000
                }
            }
        }
        
        with patch('conversation_manager.classify_intent') as mock_classify:
            mock_classify.return_value = (conversation_manager.STATES['PROFILE_COLLECTION'], {})
            
            result = conversation_manager.handle_profile_collection(event)
            
            assert result['nextState'] == conversation_manager.STATES['SCHEME_DISCOVERY']
            assert 'Age: 25' in result['response'] or 'उम्र: 25' in result['response']
    
    def test_scheme_discovery_to_eligibility_check(self):
        """Test transition from SchemeDiscovery to EligibilityCheck."""
        schemes = [
            {
                'name': 'PM-KISAN',
                'category': 'Agriculture',
                'eligibilityScore': 0.85,
                'benefits': 'Direct income support of ₹6000 per year'
            }
        ]
        
        event = {
            'sessionId': 'test-session-5',
            'userMessage': 'Tell me about schemes',
            'language': 'en',
            'context': {},
            'schemes': {'schemes': schemes}
        }
        
        result = conversation_manager.handle_scheme_discovery(event)
        
        assert result['nextState'] == conversation_manager.STATES['ELIGIBILITY_CHECK']
        assert 'PM-KISAN' in result['response']
        assert result['context']['discoveredSchemes'] == schemes
    
    def test_eligibility_check_to_application_guidance(self):
        """Test transition from EligibilityCheck to ApplicationGuidance."""
        scheme = {
            'name': 'PM-KISAN',
            'description': 'Income support for farmers',
            'benefits': 'Direct income support of ₹6000 per year',
            'eligibilityScore': 0.85,
            'requiredDocuments': ['Aadhaar', 'Land Records']
        }
        
        event = {
            'sessionId': 'test-session-6',
            'userMessage': 'Tell me about PM-KISAN',
            'language': 'en',
            'context': {
                'discoveredSchemes': [scheme]
            }
        }
        
        result = conversation_manager.handle_eligibility_check(event)
        
        assert result['nextState'] == conversation_manager.STATES['APPLICATION_GUIDANCE']
        assert 'PM-KISAN' in result['response']
        assert result['context']['currentScheme'] == scheme
    
    def test_application_guidance_back_to_scheme_discovery(self):
        """Test transition from ApplicationGuidance back to SchemeDiscovery."""
        scheme = {
            'name': 'PM-KISAN',
            'applicationProcess': 'Apply online at pmkisan.gov.in',
            'requiredDocuments': ['Aadhaar', 'Land Records'],
            'contactInfo': '1800-180-1551'
        }
        
        event = {
            'sessionId': 'test-session-7',
            'userMessage': 'How do I apply?',
            'language': 'en',
            'context': {
                'currentScheme': scheme
            }
        }
        
        result = conversation_manager.handle_application_guidance(event)
        
        assert result['nextState'] == conversation_manager.STATES['SCHEME_DISCOVERY']
        assert 'pmkisan.gov.in' in result['response'] or 'Application Process' in result['response']


class TestContextRetention:
    """Test conversation context retention across multiple turns."""
    
    @patch('conversation_manager.dynamodb')
    def test_session_context_persists_across_turns(self, mock_dynamodb):
        """Test that session context is maintained across multiple conversation turns."""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # First turn - save context
        mock_table.get_item.return_value = {
            'Item': {
                'sessionId': 'test-session-8',
                'currentState': 'ProfileCollection',
                'context': json.dumps({
                    'userProfile': {
                        'age': 30,
                        'state': 'Maharashtra'
                    }
                }),
                'language': 'en',
                'messages': []
            }
        }
        
        context = conversation_manager.get_session_context('test-session-8')
        
        assert context['currentState'] == 'ProfileCollection'
        assert context['context']['userProfile']['age'] == 30
        assert context['context']['userProfile']['state'] == 'Maharashtra'
        assert context['language'] == 'en'
    
    @patch('conversation_manager.dynamodb')
    def test_user_profile_loaded_for_returning_user(self, mock_dynamodb):
        """Test that user profile is automatically loaded for returning users."""
        # Mock DynamoDB tables
        mock_sessions_table = Mock()
        mock_users_table = Mock()
        
        def table_side_effect(table_name):
            if 'sessions' in table_name.lower():
                return mock_sessions_table
            elif 'users' in table_name.lower():
                return mock_users_table
            return Mock()
        
        mock_dynamodb.Table.side_effect = table_side_effect
        
        # Mock session with userId
        mock_sessions_table.get_item.return_value = {
            'Item': {
                'sessionId': 'test-session-9',
                'currentState': 'Welcome',
                'context': json.dumps({'userId': 'user-123'}),
                'language': 'en',
                'messages': []
            }
        }
        
        # Mock user profile
        mock_users_table.get_item.return_value = {
            'Item': {
                'userId': 'user-123',
                'demographics': {
                    'age': 35,
                    'state': 'Karnataka',
                    'income': 400000
                }
            }
        }
        
        profile = conversation_manager.load_user_profile('user-123')
        
        assert profile is not None
        assert profile['userId'] == 'user-123'
        assert profile['demographics']['age'] == 35
    
    def test_context_accumulates_user_information(self):
        """Test that context accumulates user information across multiple turns."""
        # Turn 1: User provides age
        event1 = {
            'sessionId': 'test-session-10',
            'userMessage': 'I am 28 years old',
            'language': 'en',
            'context': {}
        }
        
        with patch('conversation_manager.classify_intent') as mock_classify:
            mock_classify.return_value = (
                conversation_manager.STATES['PROFILE_COLLECTION'],
                {'age': 28}
            )
            
            result1 = conversation_manager.handle_profile_collection(event1)
            context_after_turn1 = result1['context']
            
            assert context_after_turn1['userProfile']['age'] == 28
        
        # Turn 2: User provides state (context should retain age)
        event2 = {
            'sessionId': 'test-session-10',
            'userMessage': 'I live in Tamil Nadu',
            'language': 'en',
            'context': context_after_turn1
        }
        
        with patch('conversation_manager.classify_intent') as mock_classify:
            mock_classify.return_value = (
                conversation_manager.STATES['PROFILE_COLLECTION'],
                {'state': 'Tamil Nadu'}
            )
            
            result2 = conversation_manager.handle_profile_collection(event2)
            context_after_turn2 = result2['context']
            
            # Both age and state should be present
            assert context_after_turn2['userProfile']['age'] == 28
            assert context_after_turn2['userProfile']['state'] == 'Tamil Nadu'
    
    def test_discovered_schemes_retained_in_context(self):
        """Test that discovered schemes are retained in context for eligibility checks."""
        schemes = [
            {'name': 'Scheme A', 'eligibilityScore': 0.9},
            {'name': 'Scheme B', 'eligibilityScore': 0.7}
        ]
        
        # Scheme discovery
        event1 = {
            'sessionId': 'test-session-11',
            'userMessage': 'Show me schemes',
            'language': 'en',
            'context': {},
            'schemes': {'schemes': schemes}
        }
        
        result1 = conversation_manager.handle_scheme_discovery(event1)
        
        # Schemes should be in context
        assert 'discoveredSchemes' in result1['context']
        assert len(result1['context']['discoveredSchemes']) == 2
        
        # Eligibility check should access schemes from context
        event2 = {
            'sessionId': 'test-session-11',
            'userMessage': 'Tell me about Scheme A',
            'language': 'en',
            'context': result1['context']
        }
        
        result2 = conversation_manager.handle_eligibility_check(event2)
        
        assert result2['context']['currentScheme']['name'] == 'Scheme A'


class TestLanguageSwitching:
    """Test language switching detection and handling."""
    
    def test_detect_hindi_language(self):
        """Test detection of Hindi language from Devanagari script."""
        hindi_text = "मैं 25 साल का हूं"
        detected = conversation_manager.detect_language(hindi_text, 'en')
        
        assert detected == 'hi'
    
    def test_detect_tamil_language(self):
        """Test detection of Tamil language from Tamil script."""
        tamil_text = "நான் 25 வயது"
        detected = conversation_manager.detect_language(tamil_text, 'en')
        
        assert detected == 'ta'
    
    def test_detect_telugu_language(self):
        """Test detection of Telugu language from Telugu script."""
        telugu_text = "నాకు 25 సంవత్సరాలు"
        detected = conversation_manager.detect_language(telugu_text, 'en')
        
        assert detected == 'te'
    
    def test_detect_bengali_language(self):
        """Test detection of Bengali language from Bengali script."""
        bengali_text = "আমার বয়স 25"
        detected = conversation_manager.detect_language(bengali_text, 'en')
        
        assert detected == 'bn'
    
    def test_english_remains_default(self):
        """Test that English remains the default for Latin script."""
        english_text = "I am 25 years old"
        detected = conversation_manager.detect_language(english_text, 'en')
        
        assert detected == 'en'
    
    def test_language_switch_mid_conversation(self):
        """Test language switching mid-conversation updates response language."""
        # Start in English
        event_en = {
            'sessionId': 'test-session-12',
            'userMessage': 'Hello',
            'language': 'en'
        }
        
        with patch('conversation_manager.get_session_context') as mock_get_context:
            with patch('conversation_manager.classify_intent') as mock_classify:
                mock_get_context.return_value = {
                    'currentState': 'Welcome',
                    'context': {},
                    'language': 'en',
                    'messages': []
                }
                mock_classify.return_value = (conversation_manager.STATES['WELCOME'], {})
                
                result_en = conversation_manager.determine_state(event_en)
                assert result_en['language'] == 'en'
        
        # Switch to Hindi
        event_hi = {
            'sessionId': 'test-session-12',
            'userMessage': 'मुझे योजनाओं के बारे में बताएं',
            'language': 'en'  # Previous language
        }
        
        with patch('conversation_manager.get_session_context') as mock_get_context:
            with patch('conversation_manager.classify_intent') as mock_classify:
                mock_get_context.return_value = {
                    'currentState': 'SchemeDiscovery',
                    'context': {},
                    'language': 'en',
                    'messages': []
                }
                mock_classify.return_value = (conversation_manager.STATES['SCHEME_DISCOVERY'], {})
                
                result_hi = conversation_manager.determine_state(event_hi)
                assert result_hi['language'] == 'hi'
    
    def test_hindi_response_for_hindi_input(self):
        """Test that Hindi input generates Hindi response."""
        event = {
            'sessionId': 'test-session-13',
            'language': 'hi',
            'context': {}
        }
        
        result = conversation_manager.handle_welcome(event)
        
        assert result['language'] == 'hi'
        assert 'नमस्ते' in result['response'] or 'SarkariSaathi' in result['response']
    
    def test_profile_collection_in_hindi(self):
        """Test profile collection responses in Hindi."""
        event = {
            'sessionId': 'test-session-14',
            'userMessage': 'मैं 30 साल का हूं',
            'language': 'hi',
            'context': {
                'userProfile': {
                    'age': 30
                }
            }
        }
        
        with patch('conversation_manager.classify_intent') as mock_classify:
            mock_classify.return_value = (conversation_manager.STATES['PROFILE_COLLECTION'], {})
            
            result = conversation_manager.handle_profile_collection(event)
            
            assert result['language'] == 'hi'
            # Should ask for missing info in Hindi
            assert 'राज्य' in result['response'] or 'आय' in result['response']


class TestSessionStateManagement:
    """Test session state management in DynamoDB."""
    
    @patch('conversation_manager.dynamodb')
    def test_new_session_creates_default_context(self, mock_dynamodb):
        """Test that new sessions get default context."""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # No existing session
        mock_table.get_item.return_value = {}
        
        context = conversation_manager.get_session_context('new-session')
        
        assert context['currentState'] == conversation_manager.STATES['WELCOME']
        assert context['context'] == {}
        assert context['language'] == 'en'
        assert context['messages'] == []
    
    @patch('conversation_manager.dynamodb')
    def test_existing_session_loads_context(self, mock_dynamodb):
        """Test that existing sessions load their context."""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Existing session
        mock_table.get_item.return_value = {
            'Item': {
                'sessionId': 'existing-session',
                'currentState': 'SchemeDiscovery',
                'context': json.dumps({
                    'userProfile': {'age': 40},
                    'discoveredSchemes': []
                }),
                'language': 'hi',
                'messages': ['Hello', 'नमस्ते']
            }
        }
        
        context = conversation_manager.get_session_context('existing-session')
        
        assert context['currentState'] == 'SchemeDiscovery'
        assert context['context']['userProfile']['age'] == 40
        assert context['language'] == 'hi'
        assert len(context['messages']) == 2
    
    @patch('conversation_manager.dynamodb')
    def test_context_handles_string_json(self, mock_dynamodb):
        """Test that context correctly parses JSON strings."""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Context stored as JSON string
        mock_table.get_item.return_value = {
            'Item': {
                'sessionId': 'test-session-15',
                'currentState': 'ProfileCollection',
                'context': '{"userProfile": {"age": 25, "state": "Kerala"}}',
                'language': 'en',
                'messages': []
            }
        }
        
        context = conversation_manager.get_session_context('test-session-15')
        
        assert isinstance(context['context'], dict)
        assert context['context']['userProfile']['age'] == 25
        assert context['context']['userProfile']['state'] == 'Kerala'
    
    @patch('conversation_manager.dynamodb')
    def test_error_handling_returns_default_context(self, mock_dynamodb):
        """Test that errors in loading context return default context."""
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Simulate DynamoDB error
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        
        context = conversation_manager.get_session_context('error-session')
        
        # Should return default context instead of crashing
        assert context['currentState'] == conversation_manager.STATES['WELCOME']
        assert context['context'] == {}
        assert context['language'] == 'en'


class TestErrorHandling:
    """Test error handling in conversation flow."""
    
    def test_error_handler_returns_user_friendly_message(self):
        """Test that error handler returns user-friendly messages."""
        event = {
            'sessionId': 'test-session-16',
            'error': {'Error': 'Internal server error'},
            'language': 'en'
        }
        
        result = conversation_manager.handle_error(event)
        
        assert 'sorry' in result['response'].lower()
        assert 'try again' in result['response'].lower()
    
    def test_error_handler_in_hindi(self):
        """Test error handler provides Hindi messages for Hindi users."""
        event = {
            'sessionId': 'test-session-17',
            'error': {'Error': 'Internal server error'},
            'language': 'hi'
        }
        
        result = conversation_manager.handle_error(event)
        
        assert result['language'] == 'hi'
        assert 'क्षमा' in result['response']
    
    def test_missing_scheme_in_eligibility_check(self):
        """Test handling when no schemes are available for eligibility check."""
        event = {
            'sessionId': 'test-session-18',
            'userMessage': 'Tell me about scheme',
            'language': 'en',
            'context': {
                'discoveredSchemes': []
            }
        }
        
        result = conversation_manager.handle_eligibility_check(event)
        
        assert 'which scheme' in result['response'].lower()
        assert result['nextState'] == conversation_manager.STATES['ELIGIBILITY_CHECK']
    
    def test_missing_scheme_in_application_guidance(self):
        """Test handling when no scheme is selected for application guidance."""
        event = {
            'sessionId': 'test-session-19',
            'userMessage': 'How do I apply?',
            'language': 'en',
            'context': {}
        }
        
        result = conversation_manager.handle_application_guidance(event)
        
        assert 'select a scheme' in result['response'].lower()
        assert result['nextState'] == conversation_manager.STATES['SCHEME_DISCOVERY']


class TestIntentClassification:
    """Test intent classification and entity extraction."""
    
    @patch('conversation_manager.bedrock_runtime')
    def test_classify_welcome_intent(self, mock_bedrock):
        """Test classification of welcome/greeting intent."""
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'intent': 'WELCOME',
                        'entities': {},
                        'confidence': 0.95
                    })
                }]
            }).encode())
        }
        
        next_state, entities = conversation_manager.classify_intent(
            "Hello", {}, 'en'
        )
        
        assert next_state == conversation_manager.STATES['WELCOME']
        assert entities == {}
    
    @patch('conversation_manager.bedrock_runtime')
    def test_classify_profile_collection_with_entities(self, mock_bedrock):
        """Test classification of profile collection with entity extraction."""
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'intent': 'PROFILE_COLLECTION',
                        'entities': {
                            'age': 30,
                            'state': 'Maharashtra',
                            'income': 300000
                        },
                        'confidence': 0.92
                    })
                }]
            }).encode())
        }
        
        next_state, entities = conversation_manager.classify_intent(
            "I am 30 years old from Maharashtra with income 300000", {}, 'en'
        )
        
        assert next_state == conversation_manager.STATES['PROFILE_COLLECTION']
        assert entities['age'] == 30
        assert entities['state'] == 'Maharashtra'
        assert entities['income'] == 300000
    
    @patch('conversation_manager.bedrock_runtime')
    def test_classify_scheme_discovery_intent(self, mock_bedrock):
        """Test classification of scheme discovery intent."""
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'intent': 'SCHEME_DISCOVERY',
                        'entities': {},
                        'confidence': 0.88
                    })
                }]
            }).encode())
        }
        
        next_state, entities = conversation_manager.classify_intent(
            "What schemes are available for me?", {}, 'en'
        )
        
        assert next_state == conversation_manager.STATES['SCHEME_DISCOVERY']
    
    @patch('conversation_manager.bedrock_runtime')
    def test_classify_intent_handles_markdown_json(self, mock_bedrock):
        """Test that intent classification handles JSON in markdown code blocks."""
        mock_bedrock.invoke_model.return_value = {
            'body': Mock(read=lambda: json.dumps({
                'content': [{
                    'text': '```json\n{"intent": "ELIGIBILITY_CHECK", "entities": {}, "confidence": 0.9}\n```'
                }]
            }).encode())
        }
        
        next_state, entities = conversation_manager.classify_intent(
            "Am I eligible for PM-KISAN?", {}, 'en'
        )
        
        assert next_state == conversation_manager.STATES['ELIGIBILITY_CHECK']
    
    @patch('conversation_manager.bedrock_runtime')
    def test_classify_intent_error_defaults_to_profile_collection(self, mock_bedrock):
        """Test that classification errors default to appropriate state."""
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock error")
        
        # Without user profile, should default to profile collection
        next_state, entities = conversation_manager.classify_intent(
            "Some message", {}, 'en'
        )
        
        assert next_state == conversation_manager.STATES['PROFILE_COLLECTION']
        assert entities == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

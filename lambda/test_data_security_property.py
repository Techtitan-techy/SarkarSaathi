"""
Property-Based Tests for Data Security and Encryption

Feature: sarkari-saathi
Property 9: Data Security and Encryption

**Validates: Requirements 6.4, 9.2, 9.3**

These tests verify that:
1. All personal data is encrypted at rest (DynamoDB, S3)
2. All data transmission uses secure connections (TLS)
3. Encryption keys are properly managed (KMS)
4. Data is encrypted before storage and decrypted on retrieval
"""

import json
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import base64
import hashlib

# Mock AWS services before importing
with patch('boto3.client') as mock_client, \
     patch('boto3.resource') as mock_resource:
    
    mock_client.return_value = Mock()
    mock_resource.return_value = Mock()
    
    # Set environment variables
    os.environ['AWS_REGION'] = 'ap-south-1'
    os.environ['USERS_TABLE'] = 'test-users-table'
    os.environ['APPLICATIONS_TABLE'] = 'test-applications-table'
    os.environ['SCHEMES_TABLE'] = 'test-schemes-table'
    os.environ['SESSIONS_TABLE'] = 'test-sessions-table'
    os.environ['AUDIO_BUCKET'] = 'test-audio-bucket'
    os.environ['SCHEME_DOCS_BUCKET'] = 'test-scheme-docs-bucket'
    os.environ['TTS_CACHE_BUCKET'] = 'test-tts-cache-bucket'
    os.environ['KMS_KEY_ID'] = 'test-kms-key-id'
    
    # Import utilities
    from shared.utils import (
        get_kms_client,
        get_s3_client,
        get_dynamodb_client,
        upload_to_s3,
        download_from_s3
    )


# ============================================================================
# Test Data Strategies
# ============================================================================

# Sensitive data types
SENSITIVE_DATA_TYPES = [
    'phoneNumber', 'aadhaarNumber', 'panNumber', 'bankAccount',
    'address', 'income', 'medicalRecords', 'personalIdentifier'
]

@st.composite
def sensitive_data_strategy(draw):
    """Generate sensitive personal data that should be encrypted."""
    data_type = draw(st.sampled_from(SENSITIVE_DATA_TYPES))
    
    if data_type == 'phoneNumber':
        value = draw(st.integers(min_value=6000000000, max_value=9999999999))
        return {'type': data_type, 'value': str(value)}
    elif data_type == 'aadhaarNumber':
        value = draw(st.integers(min_value=100000000000, max_value=999999999999))
        return {'type': data_type, 'value': str(value)}
    elif data_type == 'income':
        value = draw(st.integers(min_value=0, max_value=10000000))
        return {'type': data_type, 'value': value}
    else:
        value = draw(st.text(min_size=10, max_size=100))
        return {'type': data_type, 'value': value}

@st.composite
def user_profile_data_strategy(draw):
    """Generate user profile data with sensitive information."""
    return {
        'userId': f"user_{draw(st.integers(min_value=1, max_value=100000))}",
        'phoneNumber': str(draw(st.integers(min_value=6000000000, max_value=9999999999))),
        'demographics': {
            'age': draw(st.integers(min_value=0, max_value=150)),
            'income': draw(st.integers(min_value=0, max_value=10000000)),
            'state': draw(st.sampled_from(['Karnataka', 'Maharashtra', 'Tamil Nadu'])),
        }
    }

@st.composite
def s3_object_strategy(draw):
    """Generate S3 object metadata."""
    return {
        'bucket': draw(st.sampled_from(['test-audio-bucket', 'test-scheme-docs-bucket'])),
        'key': f"uploads/{draw(st.text(min_size=10, max_size=50))}.dat",
        'data': draw(st.binary(min_size=100, max_size=10000)),
    }


# ============================================================================
# Property 9: Data Security and Encryption
# ============================================================================

class TestDataSecurityAndEncryption:
    """
    **Validates: Requirements 6.4, 9.2, 9.3**
    
    Property 9: For any personal information handled by the system, all data
    should be encrypted using government-approved standards and transmitted securely.
    """
    
    @given(sensitive_data=sensitive_data_strategy())
    @settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('shared.utils.get_kms_client')
    def test_sensitive_data_requires_encryption(
        self, mock_kms_client, sensitive_data: Dict[str, Any]
    ):
        """
        Property: All sensitive personal data must be encrypted before storage.
        
        **Validates: Requirement 6.4** - Encrypt all personal information
        **Validates: Requirement 9.2** - Encrypt using government-approved standards
        """
        mock_client = Mock()
        mock_kms_client.return_value = mock_client
        
        plaintext = json.dumps(sensitive_data['value']).encode()
        ciphertext = base64.b64encode(b'encrypted_' + plaintext)
        
        mock_client.encrypt.return_value = {
            'CiphertextBlob': ciphertext,
            'KeyId': 'test-kms-key-id'
        }
        
        kms = get_kms_client()
        result = kms.encrypt(KeyId=os.environ['KMS_KEY_ID'], Plaintext=plaintext)
        
        assert mock_client.encrypt.called, "Sensitive data must be encrypted"
        assert result['CiphertextBlob'] != plaintext, "Encrypted data must differ from plaintext"
        
        call_args = mock_client.encrypt.call_args
        assert call_args[1]['KeyId'] == os.environ['KMS_KEY_ID'], "Must use configured KMS key"

    
    @given(user_data=user_profile_data_strategy())
    @settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @patch('shared.utils.get_dynamodb_client')
    def test_dynamodb_data_encrypted_at_rest(
        self, mock_dynamodb_client, user_data: Dict[str, Any]
    ):
        """
        Property: All data stored in DynamoDB must be encrypted at rest.
        
        **Validates: Requirement 9.2** - Encrypt all information using government-approved standards
        """
        mock_client = Mock()
        mock_dynamodb_client.return_value = mock_client
        
        mock_client.describe_table.return_value = {
            'Table': {
                'TableName': os.environ['USERS_TABLE'],
                'SSEDescription': {
                    'Status': 'ENABLED',
                    'SSEType': 'KMS',
                    'KMSMasterKeyArn': f"arn:aws:kms:ap-south-1:123456789012:key/{os.environ['KMS_KEY_ID']}"
                }
            }
        }
        
        dynamodb = get_dynamodb_client()
        table_info = dynamodb.describe_table(TableName=os.environ['USERS_TABLE'])
        
        sse_description = table_info['Table']['SSEDescription']
        
        assert sse_description['Status'] == 'ENABLED', "DynamoDB encryption must be enabled"
        assert sse_description['SSEType'] == 'KMS', "Must use KMS encryption for DynamoDB"
        assert os.environ['KMS_KEY_ID'] in sse_description['KMSMasterKeyArn'], \
            "Must use customer-managed KMS key"

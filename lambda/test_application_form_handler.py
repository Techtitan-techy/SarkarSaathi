"""
Unit Tests for Application Form Handler

Tests form generation, validation, and auto-save functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from application_form_handler import (
    generate_form_fields,
    validate_form_data,
    save_application,
    get_scheme_from_opensearch,
    lambda_handler
)


# Mock scheme data
MOCK_SCHEME = {
    'schemeId': 'pm-kisan',
    'name': {
        'en': 'PM-KISAN',
        'hi': 'प्रधानमंत्री किसान सम्मान निधि'
    },
    'description': {
        'en': 'Financial support for farmers',
        'hi': 'किसानों के लिए वित्तीय सहायता'
    },
    'category': 'Agriculture',
    'eligibility': {
        'ageMin': 18,
        'ageMax': 100,
        'incomeMin': 0,
        'incomeMax': 500000,
        'allowedStates': ['All India'],
        'allowedCategories': ['General', 'OBC', 'SC', 'ST'],
        'requiredOccupations': ['Farmer'],
        'excludedOccupations': []
    },
    'requiredDocuments': [
        {
            'documentId': 'land_records',
            'name': {
                'en': 'Land Ownership Records',
                'hi': 'भूमि स्वामित्व रिकॉर्ड'
            },
            'description': {
                'en': 'Proof of land ownership',
                'hi': 'भूमि स्वामित्व का प्रमाण'
            },
            'isRequired': True
        },
        {
            'documentId': 'aadhar_card',
            'name': {
                'en': 'Aadhar Card',
                'hi': 'आधार कार्ड'
            },
            'description': {
                'en': 'Identity proof',
                'hi': 'पहचान प्रमाण'
            },
            'isRequired': True
        }
    ],
    'applicationProcess': []
}


class TestFormGeneration:
    """Test dynamic form field generation."""
    
    def test_generate_basic_fields(self):
        """Test that basic fields are always generated."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        field_ids = [f['fieldId'] for f in form_fields]
        
        # Check basic fields exist
        assert 'applicantName' in field_ids
        assert 'dateOfBirth' in field_ids
        assert 'gender' in field_ids
        assert 'phoneNumber' in field_ids
        assert 'address' in field_ids
        assert 'state' in field_ids
        assert 'aadharNumber' in field_ids
        assert 'bankAccountNumber' in field_ids
    
    def test_generate_category_specific_fields(self):
        """Test that category-specific fields are generated."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        field_ids = [f['fieldId'] for f in form_fields]
        
        # Agriculture scheme should have land holding field
        assert 'landHolding' in field_ids
    
    def test_generate_document_upload_fields(self):
        """Test that document upload fields are generated."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        field_ids = [f['fieldId'] for f in form_fields]
        
        # Check document fields
        assert 'document_land_records' in field_ids
        assert 'document_aadhar_card' in field_ids
    
    def test_multilingual_labels(self):
        """Test that fields have multilingual labels."""
        form_fields_en = generate_form_fields(MOCK_SCHEME, 'en')
        form_fields_hi = generate_form_fields(MOCK_SCHEME, 'hi')
        
        # Find name field
        name_field_en = next(f for f in form_fields_en if f['fieldId'] == 'applicantName')
        name_field_hi = next(f for f in form_fields_hi if f['fieldId'] == 'applicantName')
        
        # Check labels exist in both languages
        assert 'en' in name_field_en['label']
        assert 'hi' in name_field_en['label']
        assert name_field_en['label']['en'] == 'Full Name'
        assert name_field_en['label']['hi'] == 'पूरा नाम'
    
    def test_field_ordering(self):
        """Test that fields are properly ordered."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        # Check that fields have order attribute
        for field in form_fields:
            assert 'order' in field
        
        # Check that fields are sorted by order
        orders = [f['order'] for f in form_fields]
        assert orders == sorted(orders)
    
    def test_required_field_marking(self):
        """Test that required fields are properly marked."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        # Name should be required
        name_field = next(f for f in form_fields if f['fieldId'] == 'applicantName')
        assert name_field['required'] is True
        
        # Email should be optional
        email_field = next(f for f in form_fields if f['fieldId'] == 'email')
        assert email_field['required'] is False
    
    def test_validation_rules(self):
        """Test that validation rules are included."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        # Phone field should have pattern validation
        phone_field = next(f for f in form_fields if f['fieldId'] == 'phoneNumber')
        assert 'validation' in phone_field
        assert phone_field['validation']['validation'] == 'phone'
        
        # Number field should have min/max validation
        land_field = next(f for f in form_fields if f['fieldId'] == 'landHolding')
        assert 'validation' in land_field
        assert 'min' in land_field['validation']


class TestFormValidation:
    """Test form data validation."""
    
    def test_validate_complete_valid_form(self):
        """Test validation of complete valid form data."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        form_data = {
            'applicantName': 'Rajesh Kumar',
            'dateOfBirth': '1985-05-15',
            'gender': 'male',
            'phoneNumber': '+919876543210',
            'email': 'rajesh@example.com',
            'address': '123 Main Street',
            'state': 'Maharashtra',
            'district': 'Pune',
            'pincode': 411001,
            'landHolding': 5.5,
            'annualIncome': 300000,
            'categoryType': 'General',
            'aadharNumber': '123456789012',
            'bankAccountNumber': '1234567890',
            'ifscCode': 'SBIN0001234',
            'bankName': 'State Bank of India',
            'document_land_records': 'land_records.pdf',
            'document_aadhar_card': 'aadhar.pdf'
        }
        
        is_valid, errors = validate_form_data(form_data, form_fields)
        
        # Print errors for debugging
        if not is_valid:
            print(f"Validation errors: {errors}")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        form_data = {
            'applicantName': 'Rajesh Kumar',
            # Missing other required fields
        }
        
        is_valid, errors = validate_form_data(form_data, form_fields)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_invalid_phone_number(self):
        """Test validation fails for invalid phone number."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        # Get only phone field for focused test
        phone_field = next(f for f in form_fields if f['fieldId'] == 'phoneNumber')
        
        form_data = {
            'phoneNumber': '1234567890'  # Missing +91 prefix
        }
        
        is_valid, errors = validate_form_data(form_data, [phone_field])
        
        assert is_valid is False
        assert any('phone' in err.lower() for err in errors)
    
    def test_validate_invalid_email(self):
        """Test validation fails for invalid email."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        email_field = next(f for f in form_fields if f['fieldId'] == 'email')
        
        form_data = {
            'email': 'invalid-email'
        }
        
        is_valid, errors = validate_form_data(form_data, [email_field])
        
        assert is_valid is False
        assert any('email' in err.lower() for err in errors)
    
    def test_validate_invalid_aadhar(self):
        """Test validation fails for invalid Aadhar number."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        aadhar_field = next(f for f in form_fields if f['fieldId'] == 'aadharNumber')
        
        form_data = {
            'aadharNumber': '12345'  # Too short
        }
        
        is_valid, errors = validate_form_data(form_data, [aadhar_field])
        
        assert is_valid is False
        assert any('aadhar' in err.lower() for err in errors)
    
    def test_validate_number_range(self):
        """Test validation of number ranges."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        income_field = next(f for f in form_fields if f['fieldId'] == 'annualIncome')
        
        # Test exceeding max income
        form_data = {
            'annualIncome': 600000  # Exceeds scheme limit of 500000
        }
        
        is_valid, errors = validate_form_data(form_data, [income_field])
        
        assert is_valid is False
        assert any('exceed' in err.lower() for err in errors)
    
    def test_validate_dropdown_options(self):
        """Test validation of dropdown selections."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        gender_field = next(f for f in form_fields if f['fieldId'] == 'gender')
        
        # Test invalid option
        form_data = {
            'gender': 'invalid_option'
        }
        
        is_valid, errors = validate_form_data(form_data, [gender_field])
        
        assert is_valid is False
    
    def test_validate_optional_fields(self):
        """Test that optional fields can be empty."""
        form_fields = generate_form_fields(MOCK_SCHEME, 'en')
        
        email_field = next(f for f in form_fields if f['fieldId'] == 'email')
        
        # Empty optional field should be valid
        form_data = {
            'email': ''
        }
        
        is_valid, errors = validate_form_data(form_data, [email_field])
        
        assert is_valid is True


class TestApplicationSave:
    """Test application save functionality."""
    
    @patch('application_form_handler.applications_table')
    def test_save_new_application(self, mock_table):
        """Test saving a new application."""
        mock_table.put_item = Mock()
        
        user_id = 'user_123'
        scheme_id = 'pm-kisan'
        form_data = {'applicantName': 'Test User'}
        
        result = save_application(user_id, scheme_id, form_data, 'draft')
        
        assert result['userId'] == user_id
        assert result['schemeId'] == scheme_id
        assert result['status'] == 'draft'
        assert result['formData'] == form_data
        assert 'applicationId' in result
        assert 'lastUpdated' in result
        
        mock_table.put_item.assert_called_once()
    
    @patch('application_form_handler.applications_table')
    def test_update_existing_application(self, mock_table):
        """Test updating an existing application."""
        mock_table.put_item = Mock()
        
        application_id = 'app_123'
        user_id = 'user_123'
        scheme_id = 'pm-kisan'
        form_data = {'applicantName': 'Updated User'}
        
        result = save_application(user_id, scheme_id, form_data, 'draft', application_id)
        
        assert result['applicationId'] == application_id
        assert result['formData'] == form_data
        
        mock_table.put_item.assert_called_once()
    
    @patch('application_form_handler.applications_table')
    def test_save_submitted_application(self, mock_table):
        """Test saving a submitted application."""
        mock_table.put_item = Mock()
        
        user_id = 'user_123'
        scheme_id = 'pm-kisan'
        form_data = {'applicantName': 'Test User'}
        
        result = save_application(user_id, scheme_id, form_data, 'submitted')
        
        assert result['status'] == 'submitted'
        
        mock_table.put_item.assert_called_once()


class TestLambdaHandler:
    """Test Lambda handler endpoints."""
    
    @patch('application_form_handler.opensearch_client')
    def test_generate_form_endpoint(self, mock_opensearch):
        """Test form generation endpoint."""
        mock_opensearch.get = Mock(return_value={'_source': MOCK_SCHEME})
        
        event = {
            'httpMethod': 'POST',
            'path': '/applications/form/generate',
            'body': json.dumps({
                'schemeId': 'pm-kisan',
                'language': 'en'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'formFields' in body['data']
        assert len(body['data']['formFields']) > 0
    
    @patch('application_form_handler.opensearch_client')
    def test_validate_form_endpoint(self, mock_opensearch):
        """Test form validation endpoint."""
        mock_opensearch.get = Mock(return_value={'_source': MOCK_SCHEME})
        
        event = {
            'httpMethod': 'POST',
            'path': '/applications/form/validate',
            'body': json.dumps({
                'schemeId': 'pm-kisan',
                'language': 'en',
                'formData': {
                    'applicantName': 'Test User',
                    'phoneNumber': '+919876543210'
                }
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'isValid' in body['data']
        assert 'errors' in body['data']
    
    @patch('application_form_handler.applications_table')
    @patch('application_form_handler.opensearch_client')
    def test_save_draft_endpoint(self, mock_opensearch, mock_table):
        """Test saving draft application."""
        mock_opensearch.get = Mock(return_value={'_source': MOCK_SCHEME})
        mock_table.put_item = Mock()
        
        event = {
            'httpMethod': 'POST',
            'path': '/applications/form/save',
            'body': json.dumps({
                'userId': 'user_123',
                'schemeId': 'pm-kisan',
                'formData': {
                    'applicantName': 'Test User'
                },
                'submit': False
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'application' in body['data']
        assert body['data']['application']['status'] == 'draft'
    
    @patch('application_form_handler.applications_table')
    def test_get_application_endpoint(self, mock_table):
        """Test getting existing application."""
        mock_application = {
            'applicationId': 'app_123',
            'userId': 'user_123',
            'schemeId': 'pm-kisan',
            'status': 'draft',
            'formData': {'applicantName': 'Test User'}
        }
        
        mock_table.get_item = Mock(return_value={'Item': mock_application})
        
        event = {
            'httpMethod': 'GET',
            'path': '/applications/app_123',
            'pathParameters': {
                'applicationId': 'app_123'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['application']['applicationId'] == 'app_123'
    
    @patch('application_form_handler.opensearch_client')
    def test_scheme_not_found(self, mock_opensearch):
        """Test error handling when scheme is not found."""
        mock_opensearch.get = Mock(side_effect=Exception("Not found"))
        
        event = {
            'httpMethod': 'POST',
            'path': '/applications/form/generate',
            'body': json.dumps({
                'schemeId': 'invalid_scheme',
                'language': 'en'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

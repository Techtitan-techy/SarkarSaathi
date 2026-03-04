"""
Application Form Handler

Handles dynamic form generation and validation based on scheme metadata.
Supports auto-save for partial applications and multilingual form labels.

Requirements: 5.1, 5.2
"""

import json
import os
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from shared.utils import (
    get_dynamodb_resource,
    generate_application_id,
    get_current_timestamp,
    build_success_response,
    build_error_response,
    validate_required_fields
)
from shared.models import ApplicationStatus
from shared.error_handler import (
    ValidationError,
    DatabaseError,
    error_handler,
    with_error_handling
)

# Environment variables
APPLICATIONS_TABLE = os.environ.get('APPLICATIONS_TABLE', 'sarkari-saathi-applications')
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', '')
OPENSEARCH_INDEX = 'schemes'
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# Initialize AWS clients
dynamodb = get_dynamodb_resource()
applications_table = dynamodb.Table(APPLICATIONS_TABLE)

# Initialize OpenSearch client
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    AWS_REGION,
    'es',
    session_token=credentials.token
)

opensearch_client = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT.replace('https://', ''), 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30
)


# Field type definitions
FIELD_TYPES = {
    'text': {'validation': 'string', 'maxLength': 500},
    'number': {'validation': 'number', 'min': 0},
    'date': {'validation': 'date', 'format': 'YYYY-MM-DD'},
    'dropdown': {'validation': 'enum', 'options': []},
    'checkbox': {'validation': 'boolean'},
    'file': {'validation': 'file', 'maxSize': 5242880},  # 5MB
    'phone': {'validation': 'phone', 'pattern': r'^\+91[6-9]\d{9}$'},
    'email': {'validation': 'email', 'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'},
    'aadhar': {'validation': 'aadhar', 'pattern': r'^\d{12}$'},
    'pan': {'validation': 'pan', 'pattern': r'^[A-Z]{5}\d{4}[A-Z]$'}
}


def get_scheme_from_opensearch(scheme_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch scheme details from OpenSearch.
    
    Args:
        scheme_id: Unique scheme identifier
        
    Returns:
        Scheme document or None if not found
    """
    try:
        response = opensearch_client.get(
            index=OPENSEARCH_INDEX,
            id=scheme_id
        )
        return response['_source']
    except Exception as e:
        print(f"Error fetching scheme from OpenSearch: {str(e)}")
        return None


def generate_form_fields(
    scheme: Dict[str, Any],
    language: str = 'en'
) -> List[Dict[str, Any]]:
    """
    Generate dynamic form fields based on scheme metadata.
    
    Args:
        scheme: Scheme document from OpenSearch
        language: Language code for field labels
        
    Returns:
        List of form field definitions
    """
    form_fields = []
    
    # Extract application requirements from scheme
    application_process = scheme.get('applicationProcess', [])
    required_documents = scheme.get('requiredDocuments', [])
    eligibility = scheme.get('eligibility', {})
    
    # Basic applicant information fields
    basic_fields = [
        {
            'fieldId': 'applicantName',
            'fieldType': 'text',
            'label': {
                'en': 'Full Name',
                'hi': 'पूरा नाम'
            },
            'required': True,
            'validation': FIELD_TYPES['text'],
            'order': 1
        },
        {
            'fieldId': 'dateOfBirth',
            'fieldType': 'date',
            'label': {
                'en': 'Date of Birth',
                'hi': 'जन्म तिथि'
            },
            'required': True,
            'validation': FIELD_TYPES['date'],
            'order': 2
        },
        {
            'fieldId': 'gender',
            'fieldType': 'dropdown',
            'label': {
                'en': 'Gender',
                'hi': 'लिंग'
            },
            'required': True,
            'options': [
                {'value': 'male', 'label': {'en': 'Male', 'hi': 'पुरुष'}},
                {'value': 'female', 'label': {'en': 'Female', 'hi': 'महिला'}},
                {'value': 'other', 'label': {'en': 'Other', 'hi': 'अन्य'}}
            ],
            'validation': {'validation': 'enum', 'options': ['male', 'female', 'other']},
            'order': 3
        },
        {
            'fieldId': 'phoneNumber',
            'fieldType': 'phone',
            'label': {
                'en': 'Mobile Number',
                'hi': 'मोबाइल नंबर'
            },
            'required': True,
            'validation': FIELD_TYPES['phone'],
            'placeholder': {
                'en': '+91XXXXXXXXXX',
                'hi': '+91XXXXXXXXXX'
            },
            'order': 4
        },
        {
            'fieldId': 'email',
            'fieldType': 'email',
            'label': {
                'en': 'Email Address',
                'hi': 'ईमेल पता'
            },
            'required': False,
            'validation': FIELD_TYPES['email'],
            'order': 5
        }
    ]
    
    form_fields.extend(basic_fields)
    order = 6
    
    # Address fields
    address_fields = [
        {
            'fieldId': 'address',
            'fieldType': 'text',
            'label': {
                'en': 'Residential Address',
                'hi': 'आवासीय पता'
            },
            'required': True,
            'validation': FIELD_TYPES['text'],
            'order': order
        },
        {
            'fieldId': 'state',
            'fieldType': 'dropdown',
            'label': {
                'en': 'State',
                'hi': 'राज्य'
            },
            'required': True,
            'options': get_indian_states(),
            'validation': {'validation': 'enum', 'options': [s['value'] for s in get_indian_states()]},
            'order': order + 1
        },
        {
            'fieldId': 'district',
            'fieldType': 'text',
            'label': {
                'en': 'District',
                'hi': 'जिला'
            },
            'required': True,
            'validation': FIELD_TYPES['text'],
            'order': order + 2
        },
        {
            'fieldId': 'pincode',
            'fieldType': 'number',
            'label': {
                'en': 'PIN Code',
                'hi': 'पिन कोड'
            },
            'required': True,
            'validation': {'validation': 'number', 'min': 100000, 'max': 999999},
            'order': order + 3
        }
    ]
    
    form_fields.extend(address_fields)
    order += 4
    
    # Category-specific fields based on scheme category
    category = scheme.get('category', '')
    
    if 'Agriculture' in category or 'Farmer' in category:
        form_fields.append({
            'fieldId': 'landHolding',
            'fieldType': 'number',
            'label': {
                'en': 'Land Holding (in acres)',
                'hi': 'भूमि धारण (एकड़ में)'
            },
            'required': True,
            'validation': {'validation': 'number', 'min': 0},
            'order': order
        })
        order += 1
    
    if 'Education' in category:
        form_fields.extend([
            {
                'fieldId': 'educationLevel',
                'fieldType': 'dropdown',
                'label': {
                    'en': 'Current Education Level',
                    'hi': 'वर्तमान शिक्षा स्तर'
                },
                'required': True,
                'options': [
                    {'value': 'primary', 'label': {'en': 'Primary', 'hi': 'प्राथमिक'}},
                    {'value': 'secondary', 'label': {'en': 'Secondary', 'hi': 'माध्यमिक'}},
                    {'value': 'higher_secondary', 'label': {'en': 'Higher Secondary', 'hi': 'उच्च माध्यमिक'}},
                    {'value': 'undergraduate', 'label': {'en': 'Undergraduate', 'hi': 'स्नातक'}},
                    {'value': 'postgraduate', 'label': {'en': 'Postgraduate', 'hi': 'स्नातकोत्तर'}}
                ],
                'validation': {'validation': 'enum', 'options': ['primary', 'secondary', 'higher_secondary', 'undergraduate', 'postgraduate']},
                'order': order
            },
            {
                'fieldId': 'institutionName',
                'fieldType': 'text',
                'label': {
                    'en': 'Institution Name',
                    'hi': 'संस्थान का नाम'
                },
                'required': True,
                'validation': FIELD_TYPES['text'],
                'order': order + 1
            }
        ])
        order += 2
    
    # Income-related fields
    if eligibility.get('incomeMax', 0) < 999999999:
        form_fields.append({
            'fieldId': 'annualIncome',
            'fieldType': 'number',
            'label': {
                'en': 'Annual Family Income (₹)',
                'hi': 'वार्षिक पारिवारिक आय (₹)'
            },
            'required': True,
            'validation': {'validation': 'number', 'min': 0, 'max': eligibility.get('incomeMax', 999999999)},
            'helpText': {
                'en': f"Maximum income limit: ₹{eligibility.get('incomeMax', 0):,}",
                'hi': f"अधिकतम आय सीमा: ₹{eligibility.get('incomeMax', 0):,}"
            },
            'order': order
        })
        order += 1
    
    # Category certificate field
    allowed_categories = eligibility.get('allowedCategories', [])
    if allowed_categories and 'General' not in allowed_categories:
        form_fields.append({
            'fieldId': 'categoryType',
            'fieldType': 'dropdown',
            'label': {
                'en': 'Category',
                'hi': 'श्रेणी'
            },
            'required': True,
            'options': [
                {'value': cat, 'label': {'en': cat, 'hi': cat}}
                for cat in allowed_categories
            ],
            'validation': {'validation': 'enum', 'options': allowed_categories},
            'order': order
        })
        order += 1
    
    # Identity document fields
    identity_fields = [
        {
            'fieldId': 'aadharNumber',
            'fieldType': 'aadhar',
            'label': {
                'en': 'Aadhar Number',
                'hi': 'आधार नंबर'
            },
            'required': True,
            'validation': FIELD_TYPES['aadhar'],
            'placeholder': {
                'en': '12-digit Aadhar number',
                'hi': '12 अंकों का आधार नंबर'
            },
            'order': order
        }
    ]
    
    form_fields.extend(identity_fields)
    order += 1
    
    # Bank account fields for direct benefit transfer
    bank_fields = [
        {
            'fieldId': 'bankAccountNumber',
            'fieldType': 'text',
            'label': {
                'en': 'Bank Account Number',
                'hi': 'बैंक खाता संख्या'
            },
            'required': True,
            'validation': FIELD_TYPES['text'],
            'order': order
        },
        {
            'fieldId': 'ifscCode',
            'fieldType': 'text',
            'label': {
                'en': 'IFSC Code',
                'hi': 'आईएफएससी कोड'
            },
            'required': True,
            'validation': {'validation': 'string', 'pattern': r'^[A-Z]{4}0[A-Z0-9]{6}$', 'maxLength': 11},
            'order': order + 1
        },
        {
            'fieldId': 'bankName',
            'fieldType': 'text',
            'label': {
                'en': 'Bank Name',
                'hi': 'बैंक का नाम'
            },
            'required': True,
            'validation': FIELD_TYPES['text'],
            'order': order + 2
        }
    ]
    
    form_fields.extend(bank_fields)
    order += 3
    
    # Document upload fields
    for doc in required_documents:
        doc_id = doc.get('documentId', '')
        doc_name = doc.get('name', {})
        is_required = doc.get('isRequired', True)
        
        form_fields.append({
            'fieldId': f'document_{doc_id}',
            'fieldType': 'file',
            'label': doc_name,
            'required': is_required,
            'validation': FIELD_TYPES['file'],
            'helpText': doc.get('description', {}),
            'acceptedFormats': ['pdf', 'jpg', 'jpeg', 'png'],
            'order': order
        })
        order += 1
    
    # Sort fields by order
    form_fields.sort(key=lambda x: x.get('order', 999))
    
    return form_fields


def get_indian_states() -> List[Dict[str, Any]]:
    """Get list of Indian states for dropdown."""
    states = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
        'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
        'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
        'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
    ]
    
    return [{'value': state, 'label': {'en': state, 'hi': state}} for state in states]


def validate_form_data(
    form_data: Dict[str, Any],
    form_fields: List[Dict[str, Any]]
) -> tuple[bool, List[str]]:
    """
    Validate form data against field definitions.
    
    Args:
        form_data: User-submitted form data
        form_fields: Form field definitions
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    for field in form_fields:
        field_id = field['fieldId']
        field_type = field['fieldType']
        required = field.get('required', False)
        validation = field.get('validation', {})
        
        value = form_data.get(field_id)
        
        # Check required fields
        if required and (value is None or value == ''):
            label = field.get('label', {}).get('en', field_id)
            errors.append(f"{label} is required")
            continue
        
        # Skip validation if field is optional and empty
        if not required and (value is None or value == ''):
            continue
        
        # Type-specific validation
        if field_type == 'number':
            try:
                num_value = float(value)
                if 'min' in validation and num_value < validation['min']:
                    errors.append(f"{field_id} must be at least {validation['min']}")
                if 'max' in validation and num_value > validation['max']:
                    errors.append(f"{field_id} must not exceed {validation['max']}")
            except (ValueError, TypeError):
                errors.append(f"{field_id} must be a valid number")
        
        elif field_type == 'email':
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(value)):
                errors.append(f"{field_id} must be a valid email address")
        
        elif field_type == 'phone':
            import re
            if not re.match(r'^\+91[6-9]\d{9}$', str(value)):
                errors.append(f"{field_id} must be a valid Indian mobile number (+91XXXXXXXXXX)")
        
        elif field_type == 'aadhar':
            import re
            if not re.match(r'^\d{12}$', str(value)):
                errors.append(f"{field_id} must be a 12-digit Aadhar number")
        
        elif field_type == 'pan':
            import re
            if not re.match(r'^[A-Z]{5}\d{4}[A-Z]$', str(value)):
                errors.append(f"{field_id} must be a valid PAN number")
        
        elif field_type == 'dropdown':
            allowed_options = validation.get('options', [])
            if value not in allowed_options:
                errors.append(f"{field_id} must be one of: {', '.join(allowed_options)}")
        
        elif field_type == 'date':
            try:
                datetime.fromisoformat(str(value))
            except (ValueError, TypeError):
                errors.append(f"{field_id} must be a valid date in YYYY-MM-DD format")
        
        elif field_type == 'text':
            max_length = validation.get('maxLength', 500)
            if len(str(value)) > max_length:
                errors.append(f"{field_id} must not exceed {max_length} characters")
    
    return len(errors) == 0, errors


def save_application(
    user_id: str,
    scheme_id: str,
    form_data: Dict[str, Any],
    status: str = 'draft',
    application_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save or update application in DynamoDB.
    
    Args:
        user_id: User identifier
        scheme_id: Scheme identifier
        form_data: Form data to save
        status: Application status
        application_id: Existing application ID for updates
        
    Returns:
        Saved application data
    """
    try:
        if not application_id:
            application_id = generate_application_id()
        
        timestamp = get_current_timestamp()
        
        application_data = {
            'applicationId': application_id,
            'userId': user_id,
            'schemeId': scheme_id,
            'status': status,
            'formData': form_data,
            'lastUpdated': timestamp,
            'createdAt': timestamp if not application_id else None
        }
        
        # Remove None values
        application_data = {k: v for k, v in application_data.items() if v is not None}
        
        applications_table.put_item(Item=application_data)
        
        return application_data
        
    except Exception as e:
        print(f"Error saving application: {str(e)}")
        raise DatabaseError(f"Failed to save application: {str(e)}")


@with_error_handling(language_field='language')
def lambda_handler(event, context):
    """
    Lambda handler for application form operations.
    
    Endpoints:
    - POST /applications/form/generate - Generate form fields for a scheme
    - POST /applications/form/validate - Validate form data
    - POST /applications/form/save - Save partial or complete application
    - GET /applications/{applicationId} - Get existing application
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}'))
        language = body.get('language', 'en')
        
        # Generate form fields
        if http_method == 'POST' and path.endswith('/form/generate'):
            scheme_id = body.get('schemeId')
            if not scheme_id:
                raise ValidationError("schemeId is required", "schemeId")
            
            # Fetch scheme from OpenSearch
            scheme = get_scheme_from_opensearch(scheme_id)
            if not scheme:
                return build_error_response(
                    error_message="Scheme not found",
                    error_code="SCHEME_NOT_FOUND",
                    status_code=404
                )
            
            # Generate form fields
            form_fields = generate_form_fields(scheme, language)
            
            return build_success_response({
                'schemeId': scheme_id,
                'schemeName': scheme.get('name', {}),
                'formFields': form_fields,
                'totalFields': len(form_fields)
            })
        
        # Validate form data
        elif http_method == 'POST' and path.endswith('/form/validate'):
            scheme_id = body.get('schemeId')
            form_data = body.get('formData', {})
            
            if not scheme_id or not form_data:
                raise ValidationError("schemeId and formData are required", "request")
            
            # Fetch scheme and generate form fields
            scheme = get_scheme_from_opensearch(scheme_id)
            if not scheme:
                return build_error_response(
                    error_message="Scheme not found",
                    error_code="SCHEME_NOT_FOUND",
                    status_code=404
                )
            
            form_fields = generate_form_fields(scheme, language)
            
            # Validate form data
            is_valid, errors = validate_form_data(form_data, form_fields)
            
            return build_success_response({
                'isValid': is_valid,
                'errors': errors,
                'validatedFields': len([f for f in form_fields if form_data.get(f['fieldId']) is not None])
            })
        
        # Save application (auto-save or submit)
        elif http_method == 'POST' and path.endswith('/form/save'):
            user_id = body.get('userId')
            scheme_id = body.get('schemeId')
            form_data = body.get('formData', {})
            application_id = body.get('applicationId')  # For updates
            is_submit = body.get('submit', False)
            
            if not user_id or not scheme_id:
                raise ValidationError("userId and schemeId are required", "request")
            
            # Determine status
            status = 'submitted' if is_submit else 'draft'
            
            # If submitting, validate all required fields
            if is_submit:
                scheme = get_scheme_from_opensearch(scheme_id)
                if not scheme:
                    return build_error_response(
                        error_message="Scheme not found",
                        error_code="SCHEME_NOT_FOUND",
                        status_code=404
                    )
                
                form_fields = generate_form_fields(scheme, language)
                is_valid, errors = validate_form_data(form_data, form_fields)
                
                if not is_valid:
                    return build_error_response(
                        error_message="Form validation failed",
                        error_code="VALIDATION_ERROR",
                        status_code=400
                    )
            
            # Save application
            saved_application = save_application(
                user_id,
                scheme_id,
                form_data,
                status,
                application_id
            )
            
            return build_success_response({
                'application': saved_application,
                'message': 'Application submitted successfully' if is_submit else 'Application saved as draft'
            })
        
        # Get existing application
        elif http_method == 'GET' and '/applications/' in path:
            path_params = event.get('pathParameters', {})
            application_id = path_params.get('applicationId')
            
            if not application_id:
                raise ValidationError("applicationId is required", "applicationId")
            
            # Fetch from DynamoDB
            response = applications_table.get_item(Key={'applicationId': application_id})
            application = response.get('Item')
            
            if not application:
                return build_error_response(
                    error_message="Application not found",
                    error_code="APPLICATION_NOT_FOUND",
                    status_code=404
                )
            
            return build_success_response({'application': application})
        
        else:
            return build_error_response(
                error_message="Invalid endpoint",
                error_code="INVALID_ENDPOINT",
                status_code=400
            )
        
    except ValidationError as e:
        raise
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        raise


if __name__ == '__main__':
    # Test locally
    test_event = {
        'httpMethod': 'POST',
        'path': '/applications/form/generate',
        'body': json.dumps({
            'schemeId': 'pm-kisan',
            'language': 'en'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))

"""
Document Checklist Generator

Generates personalized document checklists for scheme applications based on:
- Scheme requirements
- User profile (some documents may not be needed)
- Document procurement guidance
- Upload status tracking

Requirements: 5.1, 5.3
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
    get_current_timestamp,
    build_success_response,
    build_error_response,
    validate_required_fields
)
from shared.error_handler import (
    ValidationError,
    DatabaseError,
    error_handler,
    with_error_handling
)

# Environment variables
APPLICATIONS_TABLE = os.environ.get('APPLICATIONS_TABLE', 'sarkari-saathi-applications')
USERS_TABLE = os.environ.get('USERS_TABLE', 'sarkari-saathi-users')
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', '')
OPENSEARCH_INDEX = 'schemes'
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# Initialize AWS clients
dynamodb = get_dynamodb_resource()
applications_table = dynamodb.Table(APPLICATIONS_TABLE)
users_table = dynamodb.Table(USERS_TABLE)

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


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user profile from DynamoDB.
    
    Args:
        user_id: User identifier
        
    Returns:
        User profile or None if not found
    """
    try:
        response = users_table.get_item(Key={'userId': user_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error fetching user profile: {str(e)}")
        return None


def get_application(application_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch application from DynamoDB.
    
    Args:
        application_id: Application identifier
        
    Returns:
        Application data or None if not found
    """
    try:
        response = applications_table.get_item(Key={'applicationId': application_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error fetching application: {str(e)}")
        return None


def personalize_document_checklist(
    required_documents: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    scheme: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Personalize document checklist based on user profile.
    Some documents may not be needed based on user's demographics.
    
    Args:
        required_documents: List of required documents from scheme
        user_profile: User profile data
        scheme: Scheme metadata
        
    Returns:
        Personalized document checklist
    """
    personalized_docs = []
    demographics = user_profile.get('demographics', {})
    
    for doc in required_documents:
        doc_id = doc.get('documentId', '')
        doc_name = doc.get('name', {})
        is_required = doc.get('isRequired', True)
        
        # Check if document is applicable to user
        is_applicable = True
        reason_not_applicable = None
        
        # Category certificate logic
        if 'category' in doc_id.lower() or 'caste' in doc_id.lower():
            user_category = demographics.get('category', 'General')
            allowed_categories = scheme.get('eligibilityCriteria', {}).get('allowedCategories', [])
            
            # If scheme is for all categories or user is General, category certificate may not be needed
            if user_category == 'General' and 'General' in allowed_categories:
                is_applicable = False
                reason_not_applicable = {
                    'en': 'Not required for General category applicants',
                    'hi': 'सामान्य श्रेणी के आवेदकों के लिए आवश्यक नहीं'
                }
        
        # Income certificate logic
        if 'income' in doc_id.lower():
            income_max = scheme.get('eligibilityCriteria', {}).get('incomeRange', {}).get('max', 999999999)
            # If there's no income limit, income certificate may not be needed
            if income_max >= 999999999:
                is_applicable = False
                reason_not_applicable = {
                    'en': 'No income limit for this scheme',
                    'hi': 'इस योजना के लिए कोई आय सीमा नहीं'
                }
        
        # Land documents for non-farmers
        if 'land' in doc_id.lower() or 'property' in doc_id.lower():
            user_occupation = demographics.get('occupation', '').lower()
            if 'farmer' not in user_occupation and 'agriculture' not in user_occupation:
                # Check if scheme is agriculture-related
                scheme_category = scheme.get('category', '')
                if 'agriculture' not in scheme_category.lower():
                    is_applicable = False
                    reason_not_applicable = {
                        'en': 'Not applicable for non-agricultural applicants',
                        'hi': 'गैर-कृषि आवेदकों के लिए लागू नहीं'
                    }
        
        # Disability certificate logic
        if 'disability' in doc_id.lower():
            has_disability = demographics.get('hasDisability', False)
            if not has_disability:
                is_applicable = False
                reason_not_applicable = {
                    'en': 'Not applicable as you have not indicated a disability',
                    'hi': 'लागू नहीं क्योंकि आपने विकलांगता का संकेत नहीं दिया है'
                }
        
        personalized_docs.append({
            'documentId': doc_id,
            'name': doc_name,
            'description': doc.get('description', {}),
            'isRequired': is_required and is_applicable,
            'isApplicable': is_applicable,
            'reasonNotApplicable': reason_not_applicable,
            'alternatives': doc.get('alternatives', []),
            'howToObtain': doc.get('howToObtain', {}),
            'uploadStatus': 'not_uploaded'
        })
    
    return personalized_docs


def add_procurement_guidance(
    documents: List[Dict[str, Any]],
    language: str = 'en'
) -> List[Dict[str, Any]]:
    """
    Add detailed procurement guidance for each document.
    
    Args:
        documents: List of documents
        language: Language code for guidance
        
    Returns:
        Documents with procurement guidance
    """
    # Common document procurement guidance
    procurement_guides = {
        'aadhar': {
            'en': 'Visit nearest Aadhaar Enrollment Center or download from UIDAI website (uidai.gov.in). For new enrollment, carry proof of identity and address.',
            'hi': 'निकटतम आधार नामांकन केंद्र पर जाएं या UIDAI वेबसाइट (uidai.gov.in) से डाउनलोड करें। नए नामांकन के लिए, पहचान और पते का प्रमाण ले जाएं।'
        },
        'income': {
            'en': 'Apply at Tehsil office or online through state portal. Required: Salary slips/ITR, Aadhaar, address proof. Processing time: 7-15 days.',
            'hi': 'तहसील कार्यालय में या राज्य पोर्टल के माध्यम से ऑनलाइन आवेदन करें। आवश्यक: वेतन पर्ची/आईटीआर, आधार, पते का प्रमाण। प्रसंस्करण समय: 7-15 दिन।'
        },
        'category': {
            'en': 'Apply at Tehsil/SDM office with proof of caste. Required: Aadhaar, address proof, caste affidavit. Processing time: 15-30 days.',
            'hi': 'जाति प्रमाण के साथ तहसील/एसडीएम कार्यालय में आवेदन करें। आवश्यक: आधार, पते का प्रमाण, जाति शपथ पत्र। प्रसंस्करण समय: 15-30 दिन।'
        },
        'bank': {
            'en': 'Visit your bank branch to get account statement or passbook copy. Can also download from net banking.',
            'hi': 'खाता विवरण या पासबुक की प्रति प्राप्त करने के लिए अपनी बैंक शाखा में जाएं। नेट बैंकिंग से भी डाउनलोड कर सकते हैं।'
        },
        'land': {
            'en': 'Obtain from Revenue Department/Tehsil office. Required: Land survey number, Aadhaar. Also available online through state land records portal.',
            'hi': 'राजस्व विभाग/तहसील कार्यालय से प्राप्त करें। आवश्यक: भूमि सर्वेक्षण संख्या, आधार। राज्य भूमि रिकॉर्ड पोर्टल के माध्यम से ऑनलाइन भी उपलब्ध।'
        },
        'ration': {
            'en': 'Apply at local Food & Civil Supplies office or online through state portal. Required: Aadhaar, address proof, family details.',
            'hi': 'स्थानीय खाद्य और नागरिक आपूर्ति कार्यालय में या राज्य पोर्टल के माध्यम से ऑनलाइन आवेदन करें। आवश्यक: आधार, पते का प्रमाण, परिवार का विवरण।'
        },
        'disability': {
            'en': 'Get assessed at government hospital by medical board. Apply at District Social Welfare office. Processing time: 30-45 days.',
            'hi': 'सरकारी अस्पताल में चिकित्सा बोर्ड द्वारा मूल्यांकन कराएं। जिला समाज कल्याण कार्यालय में आवेदन करें। प्रसंस्करण समय: 30-45 दिन।'
        },
        'photo': {
            'en': 'Recent passport-size photograph (3.5cm x 4.5cm) with white background. Available at photo studios.',
            'hi': 'सफेद पृष्ठभूमि के साथ हाल की पासपोर्ट आकार की तस्वीर (3.5 सेमी x 4.5 सेमी)। फोटो स्टूडियो में उपलब्ध।'
        }
    }
    
    for doc in documents:
        doc_id = doc.get('documentId', '').lower()
        
        # If document already has procurement guidance, keep it
        if doc.get('howToObtain'):
            continue
        
        # Match document ID with procurement guides
        guidance = None
        for key, guide in procurement_guides.items():
            if key in doc_id:
                guidance = guide
                break
        
        # Add generic guidance if no specific match
        if not guidance:
            guidance = {
                'en': 'Contact the issuing authority or visit the relevant government office. Carry Aadhaar and address proof.',
                'hi': 'जारी करने वाले प्राधिकरण से संपर्क करें या संबंधित सरकारी कार्यालय में जाएं। आधार और पते का प्रमाण ले जाएं।'
            }
        
        doc['howToObtain'] = guidance
    
    return documents


def update_upload_status(
    documents: List[Dict[str, Any]],
    application: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Update document upload status based on application data.
    
    Args:
        documents: List of documents in checklist
        application: Application data with uploaded documents
        
    Returns:
        Documents with updated upload status
    """
    if not application:
        return documents
    
    uploaded_docs = application.get('documents', [])
    uploaded_doc_ids = {doc.get('documentId') for doc in uploaded_docs}
    
    for doc in documents:
        doc_id = doc.get('documentId')
        if doc_id in uploaded_doc_ids:
            doc['uploadStatus'] = 'uploaded'
            # Find the uploaded document details
            for uploaded_doc in uploaded_docs:
                if uploaded_doc.get('documentId') == doc_id:
                    doc['uploadedAt'] = uploaded_doc.get('uploadedAt')
                    doc['s3Key'] = uploaded_doc.get('s3Key')
                    doc['verified'] = uploaded_doc.get('verified', False)
                    break
        else:
            doc['uploadStatus'] = 'not_uploaded'
    
    return documents


def calculate_completion_percentage(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate checklist completion percentage.
    
    Args:
        documents: List of documents in checklist
        
    Returns:
        Completion statistics
    """
    total_required = sum(1 for doc in documents if doc.get('isRequired') and doc.get('isApplicable', True))
    total_uploaded = sum(1 for doc in documents if doc.get('uploadStatus') == 'uploaded' and doc.get('isRequired'))
    total_verified = sum(1 for doc in documents if doc.get('verified', False) and doc.get('isRequired'))
    
    completion_percentage = (total_uploaded / total_required * 100) if total_required > 0 else 0
    verification_percentage = (total_verified / total_required * 100) if total_required > 0 else 0
    
    return {
        'totalRequired': total_required,
        'totalUploaded': total_uploaded,
        'totalVerified': total_verified,
        'completionPercentage': round(completion_percentage, 2),
        'verificationPercentage': round(verification_percentage, 2),
        'isComplete': total_uploaded >= total_required
    }


def generate_checklist_summary(
    documents: List[Dict[str, Any]],
    language: str = 'en'
) -> Dict[str, Any]:
    """
    Generate a summary of the document checklist.
    
    Args:
        documents: List of documents
        language: Language code
        
    Returns:
        Checklist summary
    """
    required_docs = [doc for doc in documents if doc.get('isRequired') and doc.get('isApplicable', True)]
    optional_docs = [doc for doc in documents if not doc.get('isRequired') and doc.get('isApplicable', True)]
    not_applicable_docs = [doc for doc in documents if not doc.get('isApplicable', True)]
    
    pending_docs = [doc for doc in required_docs if doc.get('uploadStatus') != 'uploaded']
    
    summary = {
        'totalDocuments': len(documents),
        'requiredDocuments': len(required_docs),
        'optionalDocuments': len(optional_docs),
        'notApplicableDocuments': len(not_applicable_docs),
        'pendingDocuments': len(pending_docs),
        'pendingDocumentNames': [doc.get('name', {}).get(language, '') for doc in pending_docs]
    }
    
    return summary


@with_error_handling(language_field='language')
def lambda_handler(event, context):
    """
    Lambda handler for document checklist operations.
    
    Endpoints:
    - POST /applications/checklist/generate - Generate personalized document checklist
    - GET /applications/{applicationId}/checklist - Get checklist for existing application
    - POST /applications/{applicationId}/checklist/update - Update document upload status
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}'))
        path_params = event.get('pathParameters', {})
        language = body.get('language', 'en')
        
        # Generate new checklist
        if http_method == 'POST' and path.endswith('/checklist/generate'):
            user_id = body.get('userId')
            scheme_id = body.get('schemeId')
            application_id = body.get('applicationId')  # Optional, for existing applications
            
            if not user_id or not scheme_id:
                raise ValidationError("userId and schemeId are required", "request")
            
            # Fetch scheme from OpenSearch
            scheme = get_scheme_from_opensearch(scheme_id)
            if not scheme:
                return build_error_response(
                    error_message="Scheme not found",
                    error_code="SCHEME_NOT_FOUND",
                    status_code=404
                )
            
            # Fetch user profile
            user_profile = get_user_profile(user_id)
            if not user_profile:
                return build_error_response(
                    error_message="User profile not found",
                    error_code="USER_NOT_FOUND",
                    status_code=404
                )
            
            # Extract required documents from scheme
            required_documents = scheme.get('requiredDocuments', [])
            
            # Personalize checklist based on user profile
            personalized_docs = personalize_document_checklist(
                required_documents,
                user_profile,
                scheme
            )
            
            # Add procurement guidance
            personalized_docs = add_procurement_guidance(personalized_docs, language)
            
            # Update upload status if application exists
            application = None
            if application_id:
                application = get_application(application_id)
            
            personalized_docs = update_upload_status(personalized_docs, application)
            
            # Calculate completion percentage
            completion_stats = calculate_completion_percentage(personalized_docs)
            
            # Generate summary
            summary = generate_checklist_summary(personalized_docs, language)
            
            return build_success_response({
                'schemeId': scheme_id,
                'schemeName': scheme.get('name', {}),
                'userId': user_id,
                'applicationId': application_id,
                'documents': personalized_docs,
                'completionStats': completion_stats,
                'summary': summary,
                'generatedAt': get_current_timestamp()
            })
        
        # Get checklist for existing application
        elif http_method == 'GET' and '/checklist' in path:
            application_id = path_params.get('applicationId')
            
            if not application_id:
                raise ValidationError("applicationId is required", "applicationId")
            
            # Fetch application
            application = get_application(application_id)
            if not application:
                return build_error_response(
                    error_message="Application not found",
                    error_code="APPLICATION_NOT_FOUND",
                    status_code=404
                )
            
            user_id = application.get('userId')
            scheme_id = application.get('schemeId')
            
            # Fetch scheme and user profile
            scheme = get_scheme_from_opensearch(scheme_id)
            user_profile = get_user_profile(user_id)
            
            if not scheme or not user_profile:
                return build_error_response(
                    error_message="Required data not found",
                    error_code="DATA_NOT_FOUND",
                    status_code=404
                )
            
            # Generate checklist
            required_documents = scheme.get('requiredDocuments', [])
            personalized_docs = personalize_document_checklist(
                required_documents,
                user_profile,
                scheme
            )
            personalized_docs = add_procurement_guidance(personalized_docs, language)
            personalized_docs = update_upload_status(personalized_docs, application)
            
            completion_stats = calculate_completion_percentage(personalized_docs)
            summary = generate_checklist_summary(personalized_docs, language)
            
            return build_success_response({
                'applicationId': application_id,
                'schemeId': scheme_id,
                'schemeName': scheme.get('name', {}),
                'documents': personalized_docs,
                'completionStats': completion_stats,
                'summary': summary
            })
        
        # Update document upload status
        elif http_method == 'POST' and '/checklist/update' in path:
            application_id = path_params.get('applicationId')
            document_id = body.get('documentId')
            upload_status = body.get('uploadStatus')
            s3_key = body.get('s3Key')
            
            if not application_id or not document_id:
                raise ValidationError("applicationId and documentId are required", "request")
            
            # Fetch application
            application = get_application(application_id)
            if not application:
                return build_error_response(
                    error_message="Application not found",
                    error_code="APPLICATION_NOT_FOUND",
                    status_code=404
                )
            
            # Update document status
            documents = application.get('documents', [])
            document_found = False
            
            for doc in documents:
                if doc.get('documentId') == document_id:
                    doc['uploadStatus'] = upload_status
                    if s3_key:
                        doc['s3Key'] = s3_key
                    doc['uploadedAt'] = get_current_timestamp()
                    document_found = True
                    break
            
            # If document not in list, add it
            if not document_found and upload_status == 'uploaded':
                documents.append({
                    'documentId': document_id,
                    's3Key': s3_key,
                    'uploadedAt': get_current_timestamp(),
                    'verified': False
                })
            
            # Update application in DynamoDB
            applications_table.update_item(
                Key={'applicationId': application_id},
                UpdateExpression='SET documents = :docs, lastUpdated = :updated',
                ExpressionAttributeValues={
                    ':docs': documents,
                    ':updated': get_current_timestamp()
                }
            )
            
            return build_success_response({
                'applicationId': application_id,
                'documentId': document_id,
                'uploadStatus': upload_status,
                'message': 'Document status updated successfully'
            })
        
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
        'path': '/applications/checklist/generate',
        'body': json.dumps({
            'userId': 'user_test123',
            'schemeId': 'pm-kisan-2024',
            'language': 'en'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))

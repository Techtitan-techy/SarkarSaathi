"""
Application Submission Handler
Manages the complete application submission workflow including review, confirmation,
tracking number generation, and notifications.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import boto3
from boto3.dynamodb.conditions import Key

# AWS clients
dynamodb = boto3.resource('dynamodb')
pinpoint = boto3.client('pinpoint')
eventbridge = boto3.client('events')

# Environment variables
APPLICATIONS_TABLE = os.environ.get('APPLICATIONS_TABLE', 'SarkariSaathi-Applications')
USERS_TABLE = os.environ.get('USERS_TABLE', 'SarkariSaathi-Users')
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'SarkariSaathi-Schemes')
PINPOINT_PROJECT_ID = os.environ.get('PINPOINT_PROJECT_ID', '')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')

applications_table = dynamodb.Table(APPLICATIONS_TABLE)
users_table = dynamodb.Table(USERS_TABLE)
schemes_table = dynamodb.Table(SCHEMES_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for application submission workflow"""
    try:
        action = event.get('action', 'submit')
        
        if action == 'review':
            return review_application(event)
        elif action == 'submit':
            return submit_application(event)
        elif action == 'track':
            return track_application(event)
        elif action == 'update_status':
            return update_application_status(event)
        else:
            return error_response(f"Unknown action: {action}", 400)
            
    except Exception as e:
        print(f"Error in application submission handler: {str(e)}")
        return error_response(str(e), 500)


def review_application(event: Dict[str, Any]) -> Dict[str, Any]:
    """Generate application summary for user review"""
    try:
        user_id = event['userId']
        scheme_id = event['schemeId']
        form_data = event.get('formData', {})
        documents = event.get('documents', [])
        
        scheme = get_scheme_details(scheme_id)
        if not scheme:
            return error_response("Scheme not found", 404)
        
        user = get_user_profile(user_id)
        if not user:
            return error_response("User not found", 404)
        
        validation_result = validate_application(scheme, form_data, documents)
        
        summary = {
            'schemeId': scheme_id,
            'schemeName': scheme.get('name', {}),
            'applicantName': user.get('name', ''),
            'phoneNumber': user.get('phoneNumber', ''),
            'formData': form_data,
            'documents': documents,
            'validation': validation_result,
            'estimatedProcessingTime': scheme.get('processingTime', '30-45 days'),
            'benefits': scheme.get('benefits', {}),
            'isComplete': validation_result['isValid'],
            'missingFields': validation_result.get('missingFields', []),
            'missingDocuments': validation_result.get('missingDocuments', [])
        }
        
        return success_response(summary)
        
    except Exception as e:
        print(f"Error reviewing application: {str(e)}")
        return error_response(str(e), 500)


def submit_application(event: Dict[str, Any]) -> Dict[str, Any]:
    """Submit application and generate tracking number"""
    try:
        user_id = event['userId']
        scheme_id = event['schemeId']
        form_data = event.get('formData', {})
        documents = event.get('documents', [])
        language = event.get('language', 'en')
        
        scheme = get_scheme_details(scheme_id)
        user = get_user_profile(user_id)
        
        if not scheme or not user:
            return error_response("Scheme or user not found", 404)
        
        validation_result = validate_application(scheme, form_data, documents)
        if not validation_result['isValid']:
            return error_response("Application incomplete", 400, validation_result)
        
        tracking_number = generate_tracking_number(scheme_id)
        deadline = calculate_deadline(scheme)
        
        application = {
            'applicationId': str(uuid.uuid4()),
            'trackingNumber': tracking_number,
            'userId': user_id,
            'schemeId': scheme_id,
            'schemeName': scheme.get('name', {}),
            'formData': form_data,
            'documents': documents,
            'status': 'submitted',
            'submittedAt': datetime.utcnow().isoformat(),
            'deadline': deadline.isoformat() if deadline else None,
            'statusHistory': [
                {
                    'status': 'submitted',
                    'timestamp': datetime.utcnow().isoformat(),
                    'note': 'Application submitted successfully'
                }
            ]
        }
        
        applications_table.put_item(Item=application)
        send_confirmation_sms(user, tracking_number, scheme, language)
        
        if deadline:
            schedule_deadline_reminder(user, tracking_number, deadline, language)
        
        return success_response({
            'applicationId': application['applicationId'],
            'trackingNumber': tracking_number,
            'status': 'submitted',
            'submittedAt': application['submittedAt'],
            'deadline': application.get('deadline'),
            'message': get_confirmation_message(language)
        })
        
    except Exception as e:
        print(f"Error submitting application: {str(e)}")
        return error_response(str(e), 500)


def track_application(event: Dict[str, Any]) -> Dict[str, Any]:
    """Track application status by tracking number or application ID"""
    try:
        tracking_number = event.get('trackingNumber')
        application_id = event.get('applicationId')
        user_id = event.get('userId')
        
        if tracking_number:
            response = applications_table.scan(
                FilterExpression=Key('trackingNumber').eq(tracking_number)
            )
            applications = response.get('Items', [])
            if not applications:
                return error_response("Application not found", 404)
            application = applications[0]
        elif application_id:
            response = applications_table.get_item(Key={'applicationId': application_id})
            application = response.get('Item')
            if not application:
                return error_response("Application not found", 404)
        elif user_id:
            response = applications_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression=Key('userId').eq(user_id)
            )
            applications = response.get('Items', [])
            return success_response({'applications': applications})
        else:
            return error_response("Tracking number, application ID, or user ID required", 400)
        
        days_remaining = None
        if application.get('deadline'):
            deadline = datetime.fromisoformat(application['deadline'])
            days_remaining = (deadline - datetime.utcnow()).days
        
        return success_response({
            'application': application,
            'daysRemaining': days_remaining,
            'statusSummary': get_status_summary(application['status'])
        })
        
    except Exception as e:
        print(f"Error tracking application: {str(e)}")
        return error_response(str(e), 500)


def update_application_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Update application status (for admin/system use)"""
    try:
        application_id = event['applicationId']
        new_status = event['status']
        note = event.get('note', '')
        
        response = applications_table.get_item(Key={'applicationId': application_id})
        application = response.get('Item')
        
        if not application:
            return error_response("Application not found", 404)
        
        status_entry = {
            'status': new_status,
            'timestamp': datetime.utcnow().isoformat(),
            'note': note
        }
        
        status_history = application.get('statusHistory', [])
        status_history.append(status_entry)
        
        applications_table.update_item(
            Key={'applicationId': application_id},
            UpdateExpression='SET #status = :status, statusHistory = :history, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':history': status_history,
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        user = get_user_profile(application['userId'])
        if user:
            send_status_update_sms(user, application['trackingNumber'], new_status)
        
        return success_response({
            'applicationId': application_id,
            'status': new_status,
            'updatedAt': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error updating application status: {str(e)}")
        return error_response(str(e), 500)


def validate_application(scheme: Dict[str, Any], form_data: Dict[str, Any], 
                        documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate application completeness"""
    missing_fields = []
    missing_documents = []
    
    required_fields = scheme.get('requiredFields', [])
    for field in required_fields:
        field_id = field.get('id', '')
        if field_id not in form_data or not form_data[field_id]:
            missing_fields.append(field.get('label', {}).get('en', field_id))
    
    required_docs = scheme.get('requiredDocuments', [])
    submitted_doc_types = [doc.get('type') for doc in documents]
    
    for doc in required_docs:
        doc_type = doc.get('type', '')
        if doc_type not in submitted_doc_types:
            missing_documents.append(doc.get('name', {}).get('en', doc_type))
    
    is_valid = len(missing_fields) == 0 and len(missing_documents) == 0
    
    return {
        'isValid': is_valid,
        'missingFields': missing_fields,
        'missingDocuments': missing_documents,
        'completeness': calculate_completeness(required_fields, required_docs, 
                                               form_data, documents)
    }


def calculate_completeness(required_fields: List, required_docs: List,
                          form_data: Dict, documents: List) -> float:
    """Calculate application completeness percentage"""
    total_items = len(required_fields) + len(required_docs)
    if total_items == 0:
        return 100.0
    
    completed_fields = sum(1 for field in required_fields 
                          if field.get('id') in form_data and form_data[field.get('id')])
    
    submitted_doc_types = [doc.get('type') for doc in documents]
    completed_docs = sum(1 for doc in required_docs 
                        if doc.get('type') in submitted_doc_types)
    
    return round((completed_fields + completed_docs) / total_items * 100, 1)


def generate_tracking_number(scheme_id: str) -> str:
    """Generate unique tracking number"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    scheme_prefix = scheme_id[:4].upper()
    random_suffix = str(uuid.uuid4())[:6].upper()
    return f"{scheme_prefix}-{timestamp}-{random_suffix}"


def calculate_deadline(scheme: Dict[str, Any]) -> Optional[datetime]:
    """Calculate application deadline"""
    deadline_days = scheme.get('deadlineDays')
    if deadline_days:
        return datetime.utcnow() + timedelta(days=deadline_days)
    
    deadline_date = scheme.get('deadlineDate')
    if deadline_date:
        return datetime.fromisoformat(deadline_date)
    
    return None


def send_confirmation_sms(user: Dict[str, Any], tracking_number: str, 
                         scheme: Dict[str, Any], language: str):
    """Send application confirmation SMS"""
    try:
        phone_number = user.get('phoneNumber', '')
        if not phone_number or not PINPOINT_PROJECT_ID:
            return
        
        messages = {
            'en': f"Application submitted! Tracking: {tracking_number}. You'll receive updates via SMS.",
            'hi': f"आवेदन जमा हो गया! ट्रैकिंग: {tracking_number}। आपको SMS के माध्यम से अपडेट मिलेंगे।"
        }
        
        message = messages.get(language, messages['en'])
        
        pinpoint.send_messages(
            ApplicationId=PINPOINT_PROJECT_ID,
            MessageRequest={
                'Addresses': {
                    phone_number: {'ChannelType': 'SMS'}
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'MessageType': 'TRANSACTIONAL'
                    }
                }
            }
        )
    except Exception as e:
        print(f"Error sending confirmation SMS: {str(e)}")


def send_status_update_sms(user: Dict[str, Any], tracking_number: str, status: str):
    """Send application status update SMS"""
    try:
        phone_number = user.get('phoneNumber', '')
        language = user.get('preferredLanguage', 'en')
        
        if not phone_number or not PINPOINT_PROJECT_ID:
            return
        
        status_messages = {
            'en': {
                'under_review': f"Your application {tracking_number} is under review.",
                'approved': f"Congratulations! Your application {tracking_number} has been approved.",
                'rejected': f"Your application {tracking_number} has been rejected. Contact support for details.",
                'pending_documents': f"Additional documents required for {tracking_number}. Check your account."
            },
            'hi': {
                'under_review': f"आपका आवेदन {tracking_number} समीक्षाधीन है।",
                'approved': f"बधाई हो! आपका आवेदन {tracking_number} स्वीकृत हो गया है।",
                'rejected': f"आपका आवेदन {tracking_number} अस्वीकृत कर दिया गया है। विवरण के लिए सहायता से संपर्क करें।",
                'pending_documents': f"{tracking_number} के लिए अतिरिक्त दस्तावेज़ आवश्यक हैं। अपना खाता जांचें।"
            }
        }
        
        message = status_messages.get(language, status_messages['en']).get(
            status, f"Application {tracking_number} status updated to: {status}"
        )
        
        pinpoint.send_messages(
            ApplicationId=PINPOINT_PROJECT_ID,
            MessageRequest={
                'Addresses': {
                    phone_number: {'ChannelType': 'SMS'}
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'MessageType': 'TRANSACTIONAL'
                    }
                }
            }
        )
    except Exception as e:
        print(f"Error sending status update SMS: {str(e)}")


def schedule_deadline_reminder(user: Dict[str, Any], tracking_number: str, 
                               deadline: datetime, language: str):
    """Schedule deadline reminder using EventBridge"""
    try:
        reminder_date = deadline - timedelta(days=3)
        
        if reminder_date <= datetime.utcnow():
            return
        
        rule_name = f"deadline-reminder-{tracking_number}"
        
        eventbridge.put_rule(
            Name=rule_name,
            ScheduleExpression=f"at({reminder_date.strftime('%Y-%m-%dT%H:%M:%S')})",
            State='ENABLED',
            Description=f"Deadline reminder for application {tracking_number}"
        )
        
        eventbridge.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': '1',
                    'Arn': os.environ.get('REMINDER_LAMBDA_ARN', ''),
                    'Input': json.dumps({
                        'userId': user.get('userId'),
                        'trackingNumber': tracking_number,
                        'deadline': deadline.isoformat(),
                        'language': language
                    })
                }
            ]
        )
    except Exception as e:
        print(f"Error scheduling deadline reminder: {str(e)}")


def get_scheme_details(scheme_id: str) -> Optional[Dict[str, Any]]:
    """Get scheme details from DynamoDB"""
    try:
        response = schemes_table.get_item(Key={'schemeId': scheme_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error getting scheme details: {str(e)}")
        return None


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile from DynamoDB"""
    try:
        response = users_table.get_item(Key={'userId': user_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return None


def get_status_summary(status: str) -> Dict[str, Any]:
    """Get human-readable status summary"""
    summaries = {
        'submitted': {
            'en': 'Application submitted and awaiting review',
            'hi': 'आवेदन जमा किया गया और समीक्षा की प्रतीक्षा में'
        },
        'under_review': {
            'en': 'Application is being reviewed by authorities',
            'hi': 'आवेदन की अधिकारियों द्वारा समीक्षा की जा रही है'
        },
        'approved': {
            'en': 'Application approved! Benefits will be disbursed soon',
            'hi': 'आवेदन स्वीकृत! लाभ जल्द ही वितरित किए जाएंगे'
        },
        'rejected': {
            'en': 'Application rejected. Contact support for details',
            'hi': 'आवेदन अस्वीकृत। विवरण के लिए सहायता से संपर्क करें'
        },
        'pending_documents': {
            'en': 'Additional documents required',
            'hi': 'अतिरिक्त दस्तावेज़ आवश्यक'
        }
    }
    
    return summaries.get(status, {'en': status, 'hi': status})


def get_confirmation_message(language: str) -> str:
    """Get confirmation message in specified language"""
    messages = {
        'en': 'Your application has been submitted successfully. You will receive updates via SMS.',
        'hi': 'आपका आवेदन सफलतापूर्वक जमा कर दिया गया है। आपको SMS के माध्यम से अपडेट मिलेंगे।'
    }
    return messages.get(language, messages['en'])


def success_response(data: Any) -> Dict[str, Any]:
    """Generate success response"""
    return {
        'statusCode': 200,
        'body': json.dumps(data),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }


def error_response(message: str, status_code: int = 500, details: Any = None) -> Dict[str, Any]:
    """Generate error response"""
    body = {'error': message}
    if details:
        body['details'] = details
    
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }

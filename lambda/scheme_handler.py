"""
Scheme Matching Lambda Handler
Handles scheme search and eligibility matching
"""
import json
import boto3
import os
from datetime import datetime
from shared.utils import (
    create_response,
    get_dynamodb_client,
    log_info,
    log_error
)

# Initialize AWS clients
dynamodb = get_dynamodb_client()

# Environment variables
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'sarkari-saathi-schemes')

# Mock scheme data (will be replaced with DynamoDB/OpenSearch)
MOCK_SCHEMES = [
    {
        'id': 'pm-kisan',
        'name': 'PM-KISAN',
        'nameHi': 'प्रधानमंत्री किसान सम्मान निधि',
        'category': 'Agriculture',
        'description': 'Financial support of ₹6000 per year to farmer families',
        'descriptionHi': 'किसान परिवारों को प्रति वर्ष ₹6000 की वित्तीय सहायता',
        'benefits': ['₹6000 per year in 3 installments', 'Direct bank transfer'],
        'benefitsHi': ['प्रति वर्ष ₹6000 तीन किस्तों में', 'सीधे बैंक खाते में'],
        'eligibility': {
            'minAge': 18,
            'maxAge': 100,
            'minIncome': 0,
            'maxIncome': 500000,
            'states': ['all'],
            'occupation': ['farmer', 'agriculture']
        }
    },
    {
        'id': 'ayushman-bharat',
        'name': 'Ayushman Bharat',
        'nameHi': 'आयुष्मान भारत',
        'category': 'Healthcare',
        'description': 'Health insurance coverage of ₹5 lakh per family per year',
        'descriptionHi': 'प्रति परिवार प्रति वर्ष ₹5 लाख का स्वास्थ्य बीमा कवरेज',
        'benefits': ['₹5 lakh health coverage', 'Cashless treatment'],
        'benefitsHi': ['₹5 लाख स्वास्थ्य कवरेज', 'कैशलेस उपचार'],
        'eligibility': {
            'minAge': 0,
            'maxAge': 100,
            'minIncome': 0,
            'maxIncome': 300000,
            'states': ['all'],
            'occupation': ['all']
        }
    }
]


def lambda_handler(event, context):
    """
    Main handler for scheme operations
    
    Endpoints:
    - GET /schemes - Get all schemes
    - GET /schemes/{schemeId} - Get specific scheme
    - POST /schemes/match - Match schemes based on user profile
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        log_info(f"Scheme handler called: {http_method} {path}")
        
        if http_method == 'GET':
            if '/schemes/' in path and path.split('/')[-1]:
                return get_scheme(event)
            else:
                return get_all_schemes(event)
        elif http_method == 'POST' and path.endswith('/match'):
            return match_schemes(event)
        
        return create_response(400, {'error': 'Invalid endpoint'})
        
    except Exception as e:
        log_error(f"Scheme handler error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def get_all_schemes(event):
    """Get all available schemes"""
    try:
        query_params = event.get('queryStringParameters') or {}
        category = query_params.get('category')
        state = query_params.get('state')
        
        schemes = MOCK_SCHEMES.copy()
        
        # Filter by category
        if category:
            schemes = [s for s in schemes if s['category'].lower() == category.lower()]
        
        # Filter by state
        if state:
            schemes = [s for s in schemes if 'all' in s['eligibility']['states'] or state in s['eligibility']['states']]
        
        log_info(f"Retrieved {len(schemes)} schemes")
        
        return create_response(200, {
            'schemes': schemes,
            'count': len(schemes)
        })
        
    except Exception as e:
        log_error(f"Get schemes error: {str(e)}")
        return create_response(500, {'error': 'Failed to get schemes'})


def get_scheme(event):
    """Get specific scheme by ID"""
    try:
        path_params = event.get('pathParameters', {})
        scheme_id = path_params.get('schemeId')
        
        if not scheme_id:
            return create_response(400, {'error': 'No scheme ID provided'})
        
        scheme = next((s for s in MOCK_SCHEMES if s['id'] == scheme_id), None)
        
        if not scheme:
            return create_response(404, {'error': 'Scheme not found'})
        
        return create_response(200, scheme)
        
    except Exception as e:
        log_error(f"Get scheme error: {str(e)}")
        return create_response(500, {'error': 'Failed to get scheme'})


def match_schemes(event):
    """Match schemes based on user profile"""
    try:
        body = json.loads(event.get('body', '{}'))
        user_profile = body.get('userProfile', {})
        
        age = user_profile.get('age')
        income = user_profile.get('income')
        state = user_profile.get('state')
        occupation = user_profile.get('occupation')
        
        matched_schemes = []
        
        for scheme in MOCK_SCHEMES:
            eligibility = scheme['eligibility']
            score = 0
            
            # Check age eligibility
            if age:
                if eligibility['minAge'] <= age <= eligibility['maxAge']:
                    score += 25
                else:
                    continue  # Skip if age doesn't match
            
            # Check income eligibility
            if income:
                if eligibility['minIncome'] <= income <= eligibility['maxIncome']:
                    score += 25
                else:
                    continue  # Skip if income doesn't match
            
            # Check state eligibility
            if state:
                if 'all' in eligibility['states'] or state in eligibility['states']:
                    score += 25
                else:
                    continue  # Skip if state doesn't match
            
            # Check occupation eligibility
            if occupation:
                if 'all' in eligibility['occupation'] or occupation in eligibility['occupation']:
                    score += 25
                else:
                    continue  # Skip if occupation doesn't match
            
            # Add scheme with score
            scheme_with_score = scheme.copy()
            scheme_with_score['matchScore'] = score
            matched_schemes.append(scheme_with_score)
        
        # Sort by match score
        matched_schemes.sort(key=lambda x: x['matchScore'], reverse=True)
        
        log_info(f"Matched {len(matched_schemes)} schemes for user")
        
        return create_response(200, {
            'schemes': matched_schemes,
            'count': len(matched_schemes),
            'userProfile': user_profile
        })
        
    except Exception as e:
        log_error(f"Match schemes error: {str(e)}")
        return create_response(500, {'error': 'Failed to match schemes'})

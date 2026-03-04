#!/usr/bin/env python3
"""
Seed DynamoDB with test data for SarkariSaathi
Creates sample user profiles, applications, and sessions
"""

import json
import boto3
from datetime import datetime, timedelta
import random
import uuid
import sys

# Initialize DynamoDB client
try:
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    print("✓ Connected to DynamoDB")
except Exception as e:
    print(f"✗ Error connecting to DynamoDB: {e}")
    print("Note: This script requires AWS credentials and deployed DynamoDB tables")
    print("Creating local JSON files instead...")
    dynamodb = None

# Table names
USERS_TABLE = 'SarkariSaathi-Users'
APPLICATIONS_TABLE = 'SarkariSaathi-Applications'
SCHEMES_TABLE = 'SarkariSaathi-Schemes'
SESSIONS_TABLE = 'SarkariSaathi-Sessions'

# Sample data generators
STATES = ['Maharashtra', 'Uttar Pradesh', 'Bihar', 'West Bengal', 'Tamil Nadu', 
          'Karnataka', 'Gujarat', 'Rajasthan', 'Punjab', 'Haryana']

DISTRICTS = {
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik'],
    'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Varanasi', 'Agra'],
    'Bihar': ['Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli'],
    'Karnataka': ['Bangalore', 'Mysore', 'Hubli', 'Mangalore']
}

OCCUPATIONS = ['farmer', 'daily wage worker', 'small business owner', 'unemployed', 
               'self-employed', 'construction worker', 'domestic worker']

CATEGORIES = ['General', 'OBC', 'SC', 'ST']

LANGUAGES = ['Hindi', 'English', 'Tamil', 'Telugu', 'Bengali', 'Marathi']

def generate_phone_number():
    """Generate random Indian phone number"""
    return f"+91{random.randint(7000000000, 9999999999)}"

def generate_user_profile():
    """Generate a sample user profile with diverse demographics"""
    state = random.choice(STATES)
    district = random.choice(DISTRICTS.get(state, ['District1']))
    
    user_id = str(uuid.uuid4())
    age = random.randint(18, 75)
    
    return {
        'userId': user_id,
        'phoneNumber': generate_phone_number(),
        'preferredLanguage': random.choice(LANGUAGES),
        'demographics': {
            'age': age,
            'gender': random.choice(['Male', 'Female', 'Other']),
            'state': state,
            'district': district,
            'income': random.randint(0, 500000),
            'category': random.choice(CATEGORIES),
            'occupation': random.choice(OCCUPATIONS),
            'education': random.choice(['Illiterate', 'Primary', 'Secondary', 'Graduate']),
            'familySize': random.randint(1, 8),
            'hasDisability': random.choice([True, False]) if random.random() < 0.1 else False
        },
        'eligibleSchemes': [],
        'applications': [],
        'createdAt': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
        'updatedAt': datetime.now().isoformat()
    }

def seed_users(count=50):
    """Seed DynamoDB Users table with sample profiles"""
    users = []
    
    print(f"Creating {count} sample user profiles...")
    for i in range(count):
        user = generate_user_profile()
        users.append(user)
        
        if dynamodb:
            try:
                table = dynamodb.Table(USERS_TABLE)
                table.put_item(Item=user)
            except Exception as e:
                if i == 0:  # Only print error once
                    print(f"  Warning: Could not write to DynamoDB: {e}")
                    print("  Continuing with JSON file generation...")
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} users...")
    
    # Save to JSON file
    with open('data/seed_users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Successfully created {count} user profiles")
    print(f"✓ Saved to data/seed_users.json")
    return users

def seed_applications(users, count=100):
    """Generate test applications in various states"""
    applications = []
    
    # Load schemes to reference
    with open('data/schemes_database.json', 'r', encoding='utf-8') as f:
        schemes_data = json.load(f)
        schemes = schemes_data['schemes']
    
    statuses = ['draft', 'submitted', 'under_review', 'approved', 'rejected']
    
    print(f"Creating {count} sample applications...")
    for i in range(count):
        user = random.choice(users)
        scheme = random.choice(schemes)
        
        application = {
            'applicationId': str(uuid.uuid4()),
            'userId': user['userId'],
            'schemeId': scheme['schemeId'],
            'schemeName': scheme['name']['en'],
            'status': random.choice(statuses),
            'formData': {
                'name': f"User {user['userId'][:8]}",
                'age': user['demographics']['age'],
                'state': user['demographics']['state'],
                'income': user['demographics']['income']
            },
            'documents': [],
            'createdAt': (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
            'updatedAt': datetime.now().isoformat()
        }
        
        # Add submission details for non-draft applications
        if application['status'] != 'draft':
            application['submittedAt'] = (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            application['trackingNumber'] = f"APP{random.randint(100000, 999999)}"
        
        applications.append(application)
        
        if dynamodb:
            try:
                table = dynamodb.Table(APPLICATIONS_TABLE)
                table.put_item(Item=application)
            except Exception as e:
                if i == 0:
                    print(f"  Warning: Could not write to DynamoDB: {e}")
        
        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1} applications...")
    
    # Save to JSON file
    with open('data/seed_applications.json', 'w', encoding='utf-8') as f:
        json.dump(applications, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Successfully created {count} applications")
    print(f"✓ Saved to data/seed_applications.json")

def seed_sessions(users, count=75):
    """Create sample conversation sessions"""
    sessions = []
    
    intents = ['scheme_discovery', 'eligibility_check', 'application_help', 'general_query']
    
    print(f"Creating {count} sample sessions...")
    for i in range(count):
        user = random.choice(users)
        
        session = {
            'sessionId': str(uuid.uuid4()),
            'userId': user['userId'],
            'channel': random.choice(['voice', 'sms', 'web']),
            'language': user['preferredLanguage'],
            'intent': random.choice(intents),
            'conversationHistory': [],
            'currentState': random.choice(['welcome', 'profile_collection', 'scheme_discovery', 'completed']),
            'createdAt': (datetime.now() - timedelta(hours=random.randint(1, 720))).isoformat(),
            'updatedAt': datetime.now().isoformat(),
            'ttl': int((datetime.now() + timedelta(days=7)).timestamp())
        }
        
        sessions.append(session)
        
        if dynamodb:
            try:
                table = dynamodb.Table(SESSIONS_TABLE)
                table.put_item(Item=session)
            except Exception as e:
                if i == 0:
                    print(f"  Warning: Could not write to DynamoDB: {e}")
        
        if (i + 1) % 15 == 0:
            print(f"  Created {i + 1} sessions...")
    
    # Save to JSON file
    with open('data/seed_sessions.json', 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Successfully created {count} sessions")
    print(f"✓ Saved to data/seed_sessions.json")

def main():
    """Main seeding function"""
    print("=" * 60)
    print("SarkariSaathi DynamoDB Seeding Script")
    print("=" * 60)
    print()
    
    # Seed users
    users = seed_users(count=50)
    print()
    
    # Seed applications
    seed_applications(users, count=100)
    print()
    
    # Seed sessions
    seed_sessions(users, count=75)
    print()
    
    print("=" * 60)
    print("✓ Database seeding completed successfully!")
    print("=" * 60)
    print()
    print("Summary:")
    print("  - 50 user profiles created")
    print("  - 100 applications created")
    print("  - 75 conversation sessions created")
    print()

if __name__ == '__main__':
    main()

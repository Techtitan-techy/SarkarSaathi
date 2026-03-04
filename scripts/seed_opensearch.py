#!/usr/bin/env python3
"""
Seed OpenSearch with sample government schemes.

This script loads sample schemes from data/sample_schemes.json and
invokes the scheme ingestion Lambda function to index them in OpenSearch.
"""

import json
import boto3
import sys
from pathlib import Path

# AWS clients
lambda_client = boto3.client('lambda', region_name='ap-south-1')

def load_sample_schemes():
    """Load sample schemes from JSON file."""
    schemes_file = Path(__file__).parent.parent / 'data' / 'schemes_database.json'
    
    if not schemes_file.exists():
        print(f"Error: Schemes database file not found at {schemes_file}")
        sys.exit(1)
    
    with open(schemes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        schemes = data.get('schemes', [])
    
    print(f"Loaded {len(schemes)} schemes from comprehensive database")
    print(f"Categories: {', '.join(set([s.get('category', 'Unknown') for s in schemes]))}")
    return schemes


def invoke_ingestion_lambda(schemes):
    """Invoke the scheme ingestion Lambda function."""
    function_name = 'SarkariSaathi-SchemeIngestion'
    
    try:
        # Prepare payload
        payload = {
            'schemes': schemes
        }
        
        print(f"Invoking Lambda function: {function_name}")
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(response_payload.get('body', '{}'))
            print(f"✓ Successfully indexed schemes")
            print(f"  Results: {json.dumps(body, indent=2)}")
            return True
        else:
            print(f"✗ Lambda invocation failed")
            print(f"  Response: {json.dumps(response_payload, indent=2)}")
            return False
            
    except Exception as e:
        print(f"✗ Error invoking Lambda: {str(e)}")
        return False


def main():
    """Main function."""
    print("=" * 60)
    print("SarkariSaathi - OpenSearch Seeding Script")
    print("=" * 60)
    print()
    
    # Load sample schemes
    schemes = load_sample_schemes()
    
    # Invoke ingestion Lambda
    success = invoke_ingestion_lambda(schemes)
    
    print()
    if success:
        print("✓ OpenSearch seeding completed successfully!")
        print()
        print("You can now test the eligibility matching service with:")
        print("  aws lambda invoke --function-name SarkariSaathi-EligibilityMatching \\")
        print("    --payload '{\"query\": \"education schemes\", \"userProfile\": {\"age\": 25, \"income\": 300000, \"state\": \"Maharashtra\"}}' \\")
        print("    response.json")
    else:
        print("✗ OpenSearch seeding failed")
        sys.exit(1)


if __name__ == '__main__':
    main()

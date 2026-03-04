"""
Scheme Document Ingestion Handler

Processes government scheme documents from S3, extracts text and metadata,
generates embeddings using Amazon Titan, and indexes in OpenSearch.
"""

import json
import os
import boto3
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# AWS clients
s3_client = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

# OpenSearch configuration
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', '')
OPENSEARCH_INDEX = 'schemes'
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

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


def create_index_if_not_exists():
    """Create OpenSearch index with proper mappings for scheme documents."""
    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "schemeId": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "description": {"type": "text"},
                "category": {"type": "keyword"},
                "state": {"type": "keyword"},
                "launchingAuthority": {"type": "keyword"},
                "eligibility": {
                    "properties": {
                        "ageMin": {"type": "integer"},
                        "ageMax": {"type": "integer"},
                        "incomeMin": {"type": "long"},
                        "incomeMax": {"type": "long"},
                        "allowedStates": {"type": "keyword"},
                        "allowedCategories": {"type": "keyword"},
                        "requiredOccupations": {"type": "keyword"},
                        "excludedOccupations": {"type": "keyword"}
                    }
                },
                "benefits": {"type": "text"},
                "applicationProcess": {"type": "text"},
                "requiredDocuments": {"type": "keyword"},
                "deadlines": {"type": "date"},
                "contactInfo": {"type": "text"},
                "fullText": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "createdAt": {"type": "date"},
                "updatedAt": {"type": "date"}
            }
        }
    }
    
    if not opensearch_client.indices.exists(index=OPENSEARCH_INDEX):
        opensearch_client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
        print(f"Created index: {OPENSEARCH_INDEX}")
    else:
        print(f"Index already exists: {OPENSEARCH_INDEX}")


def generate_embedding(text: str) -> List[float]:
    """Generate embeddings using Amazon Titan Embeddings model."""
    try:
        # Truncate text if too long (Titan has 8K token limit)
        max_chars = 25000
        if len(text) > max_chars:
            text = text[:max_chars]
        
        request_body = json.dumps({
            "inputText": text
        })
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=request_body,
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding', [])
        
        print(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        raise


def extract_scheme_metadata(scheme_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and structure scheme metadata for indexing."""
    # Build full text for embedding
    full_text_parts = [
        scheme_data.get('name', {}).get('en', ''),
        scheme_data.get('description', {}).get('en', ''),
        scheme_data.get('benefits', ''),
        scheme_data.get('applicationProcess', '')
    ]
    full_text = ' '.join(filter(None, full_text_parts))
    
    # Extract eligibility criteria
    eligibility = scheme_data.get('eligibilityCriteria', {})
    age_range = eligibility.get('ageRange', {})
    income_range = eligibility.get('incomeRange', {})
    
    metadata = {
        "schemeId": scheme_data.get('schemeId', ''),
        "name": scheme_data.get('name', {}).get('en', ''),
        "description": scheme_data.get('description', {}).get('en', ''),
        "category": scheme_data.get('category', ''),
        "state": scheme_data.get('state', 'All India'),
        "launchingAuthority": scheme_data.get('launchingAuthority', ''),
        "eligibility": {
            "ageMin": age_range.get('min', 0),
            "ageMax": age_range.get('max', 999),
            "incomeMin": income_range.get('min', 0),
            "incomeMax": income_range.get('max', 999999999),
            "allowedStates": eligibility.get('allowedStates', []),
            "allowedCategories": eligibility.get('allowedCategories', []),
            "requiredOccupations": eligibility.get('requiredOccupations', []),
            "excludedOccupations": eligibility.get('excludedOccupations', [])
        },
        "benefits": scheme_data.get('benefits', ''),
        "applicationProcess": scheme_data.get('applicationProcess', ''),
        "requiredDocuments": scheme_data.get('requiredDocuments', []),
        "deadlines": scheme_data.get('deadlines', []),
        "contactInfo": scheme_data.get('contactInfo', ''),
        "fullText": full_text,
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }
    
    return metadata


def index_scheme_document(scheme_data: Dict[str, Any]) -> Dict[str, Any]:
    """Index a single scheme document in OpenSearch with embeddings."""
    try:
        # Extract metadata
        metadata = extract_scheme_metadata(scheme_data)
        
        # Generate embedding for full text
        embedding = generate_embedding(metadata['fullText'])
        metadata['embedding'] = embedding
        
        # Index document
        scheme_id = metadata['schemeId']
        response = opensearch_client.index(
            index=OPENSEARCH_INDEX,
            id=scheme_id,
            body=metadata,
            refresh=True
        )
        
        print(f"Indexed scheme: {scheme_id} - {metadata['name']}")
        return {
            'schemeId': scheme_id,
            'status': 'indexed',
            'result': response['result']
        }
        
    except Exception as e:
        print(f"Error indexing scheme: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Lambda handler for scheme document ingestion.
    
    Triggered by S3 events or direct invocation with scheme data.
    """
    try:
        # Create index if it doesn't exist
        create_index_if_not_exists()
        
        results = []
        
        # Handle S3 event trigger
        if 'Records' in event:
            for record in event['Records']:
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                
                # Download scheme document from S3
                response = s3_client.get_object(Bucket=bucket, Key=key)
                scheme_data = json.loads(response['Body'].read())
                
                # Index the scheme
                result = index_scheme_document(scheme_data)
                results.append(result)
        
        # Handle direct invocation with scheme data
        elif 'schemes' in event:
            schemes = event['schemes']
            if not isinstance(schemes, list):
                schemes = [schemes]
            
            for scheme_data in schemes:
                result = index_scheme_document(scheme_data)
                results.append(result)
        
        # Handle batch ingestion from S3 bucket
        elif 'bucket' in event and 'prefix' in event:
            bucket = event['bucket']
            prefix = event.get('prefix', '')
            
            # List all scheme files in bucket
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key.endswith('.json'):
                        response = s3_client.get_object(Bucket=bucket, Key=key)
                        scheme_data = json.loads(response['Body'].read())
                        result = index_scheme_document(scheme_data)
                        results.append(result)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid event format. Expected S3 event, schemes array, or bucket/prefix.'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully indexed {len(results)} schemes',
                'results': results
            })
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

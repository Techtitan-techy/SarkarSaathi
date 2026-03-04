"""
Eligibility Matching Service

Implements hybrid search combining keyword and semantic matching to find
relevant government schemes based on user demographics and query.
"""

import json
import os
import boto3
from typing import Dict, List, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# AWS clients
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


def generate_query_embedding(text: str) -> List[float]:
    """Generate embeddings for search query using Amazon Titan."""
    try:
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
        return response_body.get('embedding', [])
        
    except Exception as e:
        print(f"Error generating query embedding: {str(e)}")
        return []


def calculate_eligibility_score(scheme: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
    """
    Calculate eligibility score based on user demographics.
    Returns score between 0 and 1.
    """
    score = 0.0
    max_score = 0.0
    
    eligibility = scheme.get('eligibility', {})
    
    # Age check (weight: 20%)
    max_score += 20
    age = user_profile.get('age', 0)
    age_min = eligibility.get('ageMin', 0)
    age_max = eligibility.get('ageMax', 999)
    if age_min <= age <= age_max:
        score += 20
    
    # Income check (weight: 25%)
    max_score += 25
    income = user_profile.get('income', 0)
    income_min = eligibility.get('incomeMin', 0)
    income_max = eligibility.get('incomeMax', 999999999)
    if income_min <= income <= income_max:
        score += 25
    elif income < income_max:
        # Partial score if close to limit
        score += 15
    
    # State check (weight: 15%)
    max_score += 15
    user_state = user_profile.get('state', '')
    allowed_states = eligibility.get('allowedStates', [])
    if 'All India' in allowed_states or user_state in allowed_states:
        score += 15
    
    # Category check (weight: 15%)
    max_score += 15
    user_category = user_profile.get('category', 'General')
    allowed_categories = eligibility.get('allowedCategories', [])
    if not allowed_categories or user_category in allowed_categories:
        score += 15
    
    # Occupation check (weight: 15%)
    max_score += 15
    user_occupation = user_profile.get('occupation', '')
    required_occupations = eligibility.get('requiredOccupations', [])
    excluded_occupations = eligibility.get('excludedOccupations', [])
    
    if user_occupation in excluded_occupations:
        score += 0
    elif not required_occupations or user_occupation in required_occupations:
        score += 15
    
    # Disability check (weight: 10%)
    max_score += 10
    has_disability = user_profile.get('hasDisability', False)
    scheme_category = scheme.get('category', '')
    if has_disability and 'Disability' in scheme_category:
        score += 10
    elif not has_disability:
        score += 5
    
    # Normalize score to 0-1 range
    return score / max_score if max_score > 0 else 0.0


def build_filter_query(user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build OpenSearch filter query based on user profile."""
    filters = []
    
    # Age filter
    age = user_profile.get('age')
    if age:
        filters.append({
            "range": {
                "eligibility.ageMin": {"lte": age}
            }
        })
        filters.append({
            "range": {
                "eligibility.ageMax": {"gte": age}
            }
        })
    
    # Income filter (with buffer for schemes slightly above income)
    income = user_profile.get('income')
    if income is not None:
        income_buffer = income * 1.2  # 20% buffer
        filters.append({
            "range": {
                "eligibility.incomeMax": {"gte": income}
            }
        })
    
    # State filter
    state = user_profile.get('state')
    if state:
        filters.append({
            "bool": {
                "should": [
                    {"term": {"eligibility.allowedStates": "All India"}},
                    {"term": {"eligibility.allowedStates": state}}
                ],
                "minimum_should_match": 1
            }
        })
    
    return filters


def hybrid_search(
    query: str,
    user_profile: Dict[str, Any],
    category: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining keyword and semantic matching.
    
    Args:
        query: User's search query
        user_profile: User demographic information
        category: Optional category filter
        top_k: Number of results to return
        
    Returns:
        List of matching schemes with scores
    """
    try:
        # Generate query embedding for semantic search
        query_embedding = generate_query_embedding(query)
        
        # Build filter query
        filters = build_filter_query(user_profile)
        
        # Add category filter if specified
        if category:
            filters.append({
                "term": {"category": category}
            })
        
        # Build hybrid search query
        search_query = {
            "size": top_k * 3,  # Get more results for re-ranking
            "query": {
                "bool": {
                    "should": [
                        # Keyword search (40% weight)
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^3", "description^2", "benefits", "fullText"],
                                "type": "best_fields",
                                "boost": 0.4
                            }
                        },
                        # Semantic search (60% weight)
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": top_k * 2
                                }
                            }
                        } if query_embedding else {}
                    ],
                    "filter": filters,
                    "minimum_should_match": 1
                }
            }
        }
        
        # Execute search
        response = opensearch_client.search(
            index=OPENSEARCH_INDEX,
            body=search_query
        )
        
        # Process results and calculate eligibility scores
        results = []
        for hit in response['hits']['hits']:
            scheme = hit['_source']
            search_score = hit['_score']
            
            # Calculate eligibility score
            eligibility_score = calculate_eligibility_score(scheme, user_profile)
            
            # Combined score (50% search relevance, 50% eligibility)
            combined_score = (search_score * 0.5) + (eligibility_score * 0.5)
            
            results.append({
                'scheme': scheme,
                'searchScore': search_score,
                'eligibilityScore': eligibility_score,
                'combinedScore': combined_score,
                'confidence': eligibility_score  # Confidence is based on eligibility match
            })
        
        # Sort by combined score and return top K
        results.sort(key=lambda x: x['combinedScore'], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        print(f"Error in hybrid_search: {str(e)}")
        raise


def filter_schemes_by_criteria(
    user_profile: Dict[str, Any],
    category: Optional[str] = None,
    state: Optional[str] = None,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Filter schemes by specific criteria without text query.
    Useful for browsing schemes by category or state.
    """
    try:
        filters = build_filter_query(user_profile)
        
        if category:
            filters.append({"term": {"category": category}})
        
        if state:
            filters.append({
                "bool": {
                    "should": [
                        {"term": {"eligibility.allowedStates": "All India"}},
                        {"term": {"eligibility.allowedStates": state}}
                    ],
                    "minimum_should_match": 1
                }
            })
        
        search_query = {
            "size": top_k * 2,
            "query": {
                "bool": {
                    "filter": filters
                }
            }
        }
        
        response = opensearch_client.search(
            index=OPENSEARCH_INDEX,
            body=search_query
        )
        
        # Calculate eligibility scores and sort
        results = []
        for hit in response['hits']['hits']:
            scheme = hit['_source']
            eligibility_score = calculate_eligibility_score(scheme, user_profile)
            
            results.append({
                'scheme': scheme,
                'eligibilityScore': eligibility_score,
                'confidence': eligibility_score
            })
        
        results.sort(key=lambda x: x['eligibilityScore'], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        print(f"Error in filter_schemes_by_criteria: {str(e)}")
        raise


def lambda_handler(event, context):
    """
    Lambda handler for eligibility matching service.
    
    Expected event format:
    {
        "query": "education schemes for farmers",
        "userProfile": {
            "age": 35,
            "income": 200000,
            "state": "Maharashtra",
            "category": "OBC",
            "occupation": "Farmer",
            "hasDisability": false
        },
        "category": "Education",  // optional
        "topK": 5  // optional, default 5
    }
    """
    try:
        query = event.get('query', '')
        user_profile = event.get('userProfile', {})
        category = event.get('category')
        top_k = event.get('topK', 5)
        
        if not user_profile:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'userProfile is required'
                })
            }
        
        # Perform search
        if query:
            results = hybrid_search(query, user_profile, category, top_k)
        else:
            results = filter_schemes_by_criteria(user_profile, category, top_k=top_k)
        
        # Format response
        formatted_results = []
        for result in results:
            scheme = result['scheme']
            formatted_results.append({
                'schemeId': scheme.get('schemeId'),
                'name': scheme.get('name'),
                'description': scheme.get('description'),
                'category': scheme.get('category'),
                'benefits': scheme.get('benefits'),
                'requiredDocuments': scheme.get('requiredDocuments', []),
                'applicationProcess': scheme.get('applicationProcess'),
                'contactInfo': scheme.get('contactInfo'),
                'eligibilityScore': result.get('eligibilityScore', 0),
                'confidence': result.get('confidence', 0)
            })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'schemes': formatted_results,
                'count': len(formatted_results),
                'userProfile': user_profile
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

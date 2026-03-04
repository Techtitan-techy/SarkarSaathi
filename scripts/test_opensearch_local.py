#!/usr/bin/env python3
"""
Test OpenSearch indexing locally without AWS Lambda
Creates a local index simulation and validates scheme data
"""

import json
from pathlib import Path
from datetime import datetime

def load_schemes():
    """Load schemes from database"""
    schemes_file = Path(__file__).parent.parent / 'data' / 'schemes_database.json'
    
    with open(schemes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('schemes', [])

def validate_scheme_structure(scheme):
    """Validate that scheme has required fields for OpenSearch indexing"""
    required_fields = ['schemeId', 'name', 'description', 'category', 'eligibilityCriteria']
    missing_fields = [field for field in required_fields if field not in scheme]
    
    if missing_fields:
        return False, f"Missing fields: {', '.join(missing_fields)}"
    
    # Validate eligibility criteria structure
    if 'eligibilityCriteria' in scheme:
        criteria = scheme['eligibilityCriteria']
        required_criteria = ['ageRange', 'incomeRange', 'allowedStates']
        missing_criteria = [field for field in required_criteria if field not in criteria]
        
        if missing_criteria:
            return False, f"Missing eligibility criteria: {', '.join(missing_criteria)}"
    
    return True, "Valid"

def create_search_document(scheme):
    """Create OpenSearch document from scheme"""
    # Extract text for full-text search
    search_text = []
    
    # Add all name variations
    if 'name' in scheme:
        if isinstance(scheme['name'], dict):
            search_text.extend(scheme['name'].values())
        else:
            search_text.append(scheme['name'])
    
    # Add all description variations
    if 'description' in scheme:
        if isinstance(scheme['description'], dict):
            search_text.extend(scheme['description'].values())
        else:
            search_text.append(scheme['description'])
    
    # Add benefits
    if 'benefits' in scheme:
        if isinstance(scheme['benefits'], str):
            search_text.append(scheme['benefits'])
        elif isinstance(scheme['benefits'], list):
            search_text.extend(scheme['benefits'])
    
    # Create document
    document = {
        'schemeId': scheme['schemeId'],
        'name': scheme['name'],
        'description': scheme['description'],
        'category': scheme.get('category', 'General'),
        'state': scheme.get('state', 'All India'),
        'eligibilityCriteria': scheme.get('eligibilityCriteria', {}),
        'benefits': scheme.get('benefits', ''),
        'requiredDocuments': scheme.get('requiredDocuments', []),
        'applicationProcess': scheme.get('applicationProcess', ''),
        'searchText': ' '.join(search_text),
        'indexedAt': datetime.now().isoformat()
    }
    
    return document

def simulate_search_query(documents, query, user_profile=None):
    """Simulate a search query against indexed documents"""
    query_lower = query.lower()
    results = []
    
    for doc in documents:
        score = 0
        
        # Text matching
        if query_lower in doc['searchText'].lower():
            score += 10
        
        # Category matching
        if query_lower in doc['category'].lower():
            score += 5
        
        # Eligibility matching (if user profile provided)
        if user_profile and 'eligibilityCriteria' in doc:
            criteria = doc['eligibilityCriteria']
            
            # Age check
            if 'age' in user_profile and 'ageRange' in criteria:
                age = user_profile['age']
                if criteria['ageRange']['min'] <= age <= criteria['ageRange']['max']:
                    score += 3
            
            # Income check
            if 'income' in user_profile and 'incomeRange' in criteria:
                income = user_profile['income']
                if criteria['incomeRange']['min'] <= income <= criteria['incomeRange']['max']:
                    score += 3
            
            # State check
            if 'state' in user_profile and 'allowedStates' in criteria:
                if 'All India' in criteria['allowedStates'] or user_profile['state'] in criteria['allowedStates']:
                    score += 2
        
        if score > 0:
            results.append({
                'scheme': doc,
                'score': score
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:5]  # Top 5 results

def main():
    """Main function"""
    print("=" * 70)
    print("OpenSearch Local Testing - Scheme Indexing Validation")
    print("=" * 70)
    print()
    
    # Load schemes
    schemes = load_schemes()
    print(f"✓ Loaded {len(schemes)} schemes")
    print()
    
    # Validate schemes
    print("Validating scheme structures...")
    valid_count = 0
    invalid_schemes = []
    
    for scheme in schemes:
        is_valid, message = validate_scheme_structure(scheme)
        if is_valid:
            valid_count += 1
        else:
            invalid_schemes.append({
                'schemeId': scheme.get('schemeId', 'Unknown'),
                'error': message
            })
    
    print(f"✓ Valid schemes: {valid_count}/{len(schemes)}")
    
    if invalid_schemes:
        print(f"✗ Invalid schemes: {len(invalid_schemes)}")
        for invalid in invalid_schemes:
            print(f"  - {invalid['schemeId']}: {invalid['error']}")
        print()
    else:
        print("✓ All schemes have valid structure")
        print()
    
    # Create search documents
    print("Creating OpenSearch documents...")
    documents = []
    for scheme in schemes:
        try:
            doc = create_search_document(scheme)
            documents.append(doc)
        except Exception as e:
            print(f"✗ Error creating document for {scheme.get('schemeId', 'Unknown')}: {e}")
    
    print(f"✓ Created {len(documents)} search documents")
    print()
    
    # Save documents to file
    output_file = Path(__file__).parent.parent / 'data' / 'opensearch_documents.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved documents to: {output_file}")
    print()
    
    # Test sample queries
    print("Testing sample search queries...")
    print()
    
    test_queries = [
        {
            'query': 'agriculture',
            'profile': {'age': 35, 'income': 200000, 'state': 'Punjab'}
        },
        {
            'query': 'healthcare',
            'profile': {'age': 65, 'income': 150000, 'state': 'Maharashtra'}
        },
        {
            'query': 'housing',
            'profile': {'age': 30, 'income': 400000, 'state': 'Karnataka'}
        }
    ]
    
    for test in test_queries:
        print(f"Query: '{test['query']}' | Profile: Age={test['profile']['age']}, Income={test['profile']['income']}, State={test['profile']['state']}")
        results = simulate_search_query(documents, test['query'], test['profile'])
        
        if results:
            print(f"  Found {len(results)} matching schemes:")
            for i, result in enumerate(results, 1):
                scheme_name = result['scheme']['name']
                if isinstance(scheme_name, dict):
                    scheme_name = scheme_name.get('en', 'Unknown')
                print(f"    {i}. {scheme_name} (Score: {result['score']})")
        else:
            print("  No matching schemes found")
        print()
    
    print("=" * 70)
    print("✓ OpenSearch indexing validation completed!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - {len(schemes)} schemes loaded")
    print(f"  - {valid_count} schemes validated")
    print(f"  - {len(documents)} documents created")
    print(f"  - Documents saved to: {output_file}")
    print()
    print("Next steps:")
    print("  1. Deploy OpenSearch domain (if not already deployed)")
    print("  2. Run: python scripts/seed_opensearch.py")
    print("  3. Test eligibility matching service")
    print()

if __name__ == '__main__':
    main()

"""
Test Document Checklist Generator

Simple test to verify the document checklist generator functionality.
"""

import json
import sys
import os

# Add lambda directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from document_checklist_generator import (
    personalize_document_checklist,
    add_procurement_guidance,
    calculate_completion_percentage,
    generate_checklist_summary,
    update_upload_status
)


def test_personalize_checklist():
    """Test document checklist personalization based on user profile."""
    print("\n=== Testing Document Checklist Personalization ===\n")
    
    # Sample scheme documents
    required_documents = [
        {
            'documentId': 'aadhar_card',
            'name': {'en': 'Aadhaar Card', 'hi': 'आधार कार्ड'},
            'description': {'en': '12-digit unique identification', 'hi': '12 अंकों की विशिष्ट पहचान'},
            'isRequired': True,
            'alternatives': []
        },
        {
            'documentId': 'category_certificate',
            'name': {'en': 'Category Certificate', 'hi': 'श्रेणी प्रमाण पत्र'},
            'description': {'en': 'SC/ST/OBC certificate', 'hi': 'एससी/एसटी/ओबीसी प्रमाण पत्र'},
            'isRequired': True,
            'alternatives': []
        },
        {
            'documentId': 'income_certificate',
            'name': {'en': 'Income Certificate', 'hi': 'आय प्रमाण पत्र'},
            'description': {'en': 'Annual income proof', 'hi': 'वार्षिक आय प्रमाण'},
            'isRequired': True,
            'alternatives': []
        },
        {
            'documentId': 'land_ownership',
            'name': {'en': 'Land Ownership Documents', 'hi': 'भूमि स्वामित्व दस्तावेज'},
            'description': {'en': 'Land records', 'hi': 'भूमि रिकॉर्ड'},
            'isRequired': True,
            'alternatives': []
        }
    ]
    
    # Test Case 1: General category user (no category certificate needed)
    user_profile_general = {
        'userId': 'user_123',
        'demographics': {
            'category': 'General',
            'occupation': 'Teacher',
            'hasDisability': False
        }
    }
    
    scheme_general = {
        'category': 'Education',
        'eligibilityCriteria': {
            'allowedCategories': ['General', 'OBC', 'SC', 'ST'],
            'incomeRange': {'min': 0, 'max': 500000}
        }
    }
    
    personalized = personalize_document_checklist(
        required_documents,
        user_profile_general,
        scheme_general
    )
    
    print("Test Case 1: General Category User")
    print(f"Total documents: {len(personalized)}")
    applicable_docs = [doc for doc in personalized if doc['isApplicable']]
    not_applicable_docs = [doc for doc in personalized if not doc['isApplicable']]
    print(f"Applicable documents: {len(applicable_docs)}")
    print(f"Not applicable documents: {len(not_applicable_docs)}")
    
    for doc in not_applicable_docs:
        print(f"  - {doc['name']['en']}: {doc['reasonNotApplicable']['en']}")
    
    # Test Case 2: OBC category farmer (needs category certificate and land docs)
    user_profile_farmer = {
        'userId': 'user_456',
        'demographics': {
            'category': 'OBC',
            'occupation': 'Farmer',
            'hasDisability': False
        }
    }
    
    scheme_agriculture = {
        'category': 'Agriculture',
        'eligibilityCriteria': {
            'allowedCategories': ['General', 'OBC', 'SC', 'ST'],
            'incomeRange': {'min': 0, 'max': 999999999}
        }
    }
    
    personalized_farmer = personalize_document_checklist(
        required_documents,
        user_profile_farmer,
        scheme_agriculture
    )
    
    print("\nTest Case 2: OBC Category Farmer")
    print(f"Total documents: {len(personalized_farmer)}")
    applicable_docs_farmer = [doc for doc in personalized_farmer if doc['isApplicable']]
    print(f"Applicable documents: {len(applicable_docs_farmer)}")
    
    assert len(applicable_docs_farmer) > len(applicable_docs), "Farmer should have more applicable documents"
    print("✓ Personalization working correctly")


def test_procurement_guidance():
    """Test adding procurement guidance to documents."""
    print("\n=== Testing Procurement Guidance ===\n")
    
    documents = [
        {
            'documentId': 'aadhar_card',
            'name': {'en': 'Aadhaar Card', 'hi': 'आधार कार्ड'},
            'isRequired': True,
            'isApplicable': True
        },
        {
            'documentId': 'income_certificate',
            'name': {'en': 'Income Certificate', 'hi': 'आय प्रमाण पत्र'},
            'isRequired': True,
            'isApplicable': True
        }
    ]
    
    docs_with_guidance = add_procurement_guidance(documents, 'en')
    
    print("Documents with procurement guidance:")
    for doc in docs_with_guidance:
        print(f"\n{doc['name']['en']}:")
        print(f"  Guidance: {doc.get('howToObtain', {}).get('en', 'N/A')[:100]}...")
    
    assert all('howToObtain' in doc for doc in docs_with_guidance), "All documents should have guidance"
    print("\n✓ Procurement guidance added successfully")


def test_completion_tracking():
    """Test completion percentage calculation."""
    print("\n=== Testing Completion Tracking ===\n")
    
    documents = [
        {
            'documentId': 'doc1',
            'isRequired': True,
            'isApplicable': True,
            'uploadStatus': 'uploaded',
            'verified': True
        },
        {
            'documentId': 'doc2',
            'isRequired': True,
            'isApplicable': True,
            'uploadStatus': 'uploaded',
            'verified': False
        },
        {
            'documentId': 'doc3',
            'isRequired': True,
            'isApplicable': True,
            'uploadStatus': 'not_uploaded'
        },
        {
            'documentId': 'doc4',
            'isRequired': False,
            'isApplicable': True,
            'uploadStatus': 'not_uploaded'
        }
    ]
    
    stats = calculate_completion_percentage(documents)
    
    print("Completion Statistics:")
    print(f"  Total required: {stats['totalRequired']}")
    print(f"  Total uploaded: {stats['totalUploaded']}")
    print(f"  Total verified: {stats['totalVerified']}")
    print(f"  Completion: {stats['completionPercentage']}%")
    print(f"  Verification: {stats['verificationPercentage']}%")
    print(f"  Is complete: {stats['isComplete']}")
    
    assert stats['totalRequired'] == 3, "Should have 3 required documents"
    assert stats['totalUploaded'] == 2, "Should have 2 uploaded documents"
    assert stats['completionPercentage'] == 66.67, "Should be 66.67% complete"
    print("\n✓ Completion tracking working correctly")


def test_upload_status_update():
    """Test updating upload status from application data."""
    print("\n=== Testing Upload Status Update ===\n")
    
    documents = [
        {
            'documentId': 'doc1',
            'name': {'en': 'Document 1'},
            'isRequired': True,
            'uploadStatus': 'not_uploaded'
        },
        {
            'documentId': 'doc2',
            'name': {'en': 'Document 2'},
            'isRequired': True,
            'uploadStatus': 'not_uploaded'
        }
    ]
    
    application = {
        'applicationId': 'app_123',
        'documents': [
            {
                'documentId': 'doc1',
                's3Key': 'uploads/doc1.pdf',
                'uploadedAt': '2024-01-15T10:00:00Z',
                'verified': True
            }
        ]
    }
    
    updated_docs = update_upload_status(documents, application)
    
    print("Updated document statuses:")
    for doc in updated_docs:
        print(f"  {doc['name']['en']}: {doc['uploadStatus']}")
        if doc['uploadStatus'] == 'uploaded':
            print(f"    Uploaded at: {doc.get('uploadedAt')}")
            print(f"    Verified: {doc.get('verified')}")
    
    assert updated_docs[0]['uploadStatus'] == 'uploaded', "First document should be uploaded"
    assert updated_docs[1]['uploadStatus'] == 'not_uploaded', "Second document should not be uploaded"
    print("\n✓ Upload status update working correctly")


def test_checklist_summary():
    """Test checklist summary generation."""
    print("\n=== Testing Checklist Summary ===\n")
    
    documents = [
        {
            'documentId': 'doc1',
            'name': {'en': 'Required Doc 1', 'hi': 'आवश्यक दस्तावेज 1'},
            'isRequired': True,
            'isApplicable': True,
            'uploadStatus': 'not_uploaded'
        },
        {
            'documentId': 'doc2',
            'name': {'en': 'Required Doc 2', 'hi': 'आवश्यक दस्तावेज 2'},
            'isRequired': True,
            'isApplicable': True,
            'uploadStatus': 'uploaded'
        },
        {
            'documentId': 'doc3',
            'name': {'en': 'Optional Doc', 'hi': 'वैकल्पिक दस्तावेज'},
            'isRequired': False,
            'isApplicable': True,
            'uploadStatus': 'not_uploaded'
        },
        {
            'documentId': 'doc4',
            'name': {'en': 'Not Applicable Doc', 'hi': 'लागू नहीं दस्तावेज'},
            'isRequired': True,
            'isApplicable': False,
            'uploadStatus': 'not_uploaded'
        }
    ]
    
    summary = generate_checklist_summary(documents, 'en')
    
    print("Checklist Summary:")
    print(f"  Total documents: {summary['totalDocuments']}")
    print(f"  Required documents: {summary['requiredDocuments']}")
    print(f"  Optional documents: {summary['optionalDocuments']}")
    print(f"  Not applicable: {summary['notApplicableDocuments']}")
    print(f"  Pending documents: {summary['pendingDocuments']}")
    print(f"  Pending names: {summary['pendingDocumentNames']}")
    
    assert summary['totalDocuments'] == 4, "Should have 4 total documents"
    assert summary['requiredDocuments'] == 2, "Should have 2 required documents"
    assert summary['pendingDocuments'] == 1, "Should have 1 pending document"
    print("\n✓ Checklist summary working correctly")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Document Checklist Generator - Test Suite")
    print("="*60)
    
    try:
        test_personalize_checklist()
        test_procurement_guidance()
        test_completion_tracking()
        test_upload_status_update()
        test_checklist_summary()
        
        print("\n" + "="*60)
        print("✓ All tests passed successfully!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

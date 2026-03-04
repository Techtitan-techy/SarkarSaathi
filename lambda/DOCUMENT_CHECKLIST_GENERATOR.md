# Document Checklist Generator

## Overview

The Document Checklist Generator is a Lambda function that creates personalized document checklists for government scheme applications. It intelligently filters documents based on user profiles, provides procurement guidance, tracks upload status, and calculates completion percentages.

## Features

### 1. Personalized Checklist Generation

- Extracts required documents from scheme metadata
- Filters documents based on user demographics
- Identifies documents that may not be applicable to specific users
- Provides clear reasons when documents are not needed

### 2. Smart Document Filtering

The system automatically determines document applicability based on:

**Category Certificates**

- Not required for General category applicants when scheme accepts all categories
- Required for SC/ST/OBC applicants

**Income Certificates**

- Not required when scheme has no income limit
- Required when scheme has income restrictions

**Land Documents**

- Not required for non-agricultural applicants in non-agricultural schemes
- Required for farmers in agricultural schemes

**Disability Certificates**

- Only required when user has indicated a disability
- Automatically excluded for users without disabilities

### 3. Procurement Guidance

Provides detailed guidance for obtaining each document:

- **Aadhaar Card**: Visit enrollment center or download from UIDAI
- **Income Certificate**: Apply at Tehsil office, required documents, processing time
- **Category Certificate**: Apply at Tehsil/SDM office with caste proof
- **Bank Documents**: Get from bank branch or download from net banking
- **Land Records**: Obtain from Revenue Department or online portal
- **Ration Card**: Apply at Food & Civil Supplies office
- **Disability Certificate**: Medical board assessment at government hospital
- **Photographs**: Passport-size specifications and where to get them

### 4. Upload Status Tracking

- Tracks which documents have been uploaded
- Shows upload timestamps
- Indicates verification status
- Calculates completion percentage
- Identifies pending documents

### 5. Multilingual Support

All document names, descriptions, and guidance available in:

- English (en)
- Hindi (hi)
- And other supported Indian languages

## API Endpoints

### 1. Generate Checklist

**Endpoint**: `POST /applications/checklist/generate`

**Request Body**:

```json
{
  "userId": "user_123",
  "schemeId": "pm-kisan-2024",
  "applicationId": "app_456", // Optional
  "language": "en"
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "schemeId": "pm-kisan-2024",
    "schemeName": {
      "en": "PM-KISAN",
      "hi": "प्रधानमंत्री किसान सम्मान निधि"
    },
    "userId": "user_123",
    "applicationId": "app_456",
    "documents": [
      {
        "documentId": "aadhar_card",
        "name": {
          "en": "Aadhaar Card",
          "hi": "आधार कार्ड"
        },
        "description": {
          "en": "12-digit unique identification",
          "hi": "12 अंकों की विशिष्ट पहचान"
        },
        "isRequired": true,
        "isApplicable": true,
        "reasonNotApplicable": null,
        "alternatives": [],
        "howToObtain": {
          "en": "Visit nearest Aadhaar Enrollment Center...",
          "hi": "निकटतम आधार नामांकन केंद्र पर जाएं..."
        },
        "uploadStatus": "uploaded",
        "uploadedAt": "2024-01-15T10:00:00Z",
        "verified": true
      }
    ],
    "completionStats": {
      "totalRequired": 5,
      "totalUploaded": 3,
      "totalVerified": 2,
      "completionPercentage": 60.0,
      "verificationPercentage": 40.0,
      "isComplete": false
    },
    "summary": {
      "totalDocuments": 8,
      "requiredDocuments": 5,
      "optionalDocuments": 2,
      "notApplicableDocuments": 1,
      "pendingDocuments": 2,
      "pendingDocumentNames": ["Income Certificate", "Bank Account Details"]
    },
    "generatedAt": "2024-01-15T12:00:00Z"
  }
}
```

### 2. Get Checklist for Application

**Endpoint**: `GET /applications/{applicationId}/checklist`

**Query Parameters**:

- `language`: Language code (default: 'en')

**Response**: Same structure as generate checklist

### 3. Update Document Status

**Endpoint**: `POST /applications/{applicationId}/checklist/update`

**Request Body**:

```json
{
  "documentId": "aadhar_card",
  "uploadStatus": "uploaded",
  "s3Key": "uploads/user_123/aadhar_card.pdf"
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "applicationId": "app_456",
    "documentId": "aadhar_card",
    "uploadStatus": "uploaded",
    "message": "Document status updated successfully"
  }
}
```

## Implementation Details

### Personalization Logic

```python
def personalize_document_checklist(
    required_documents: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    scheme: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Personalizes document checklist based on user profile.

    Logic:
    1. Check user category against scheme requirements
    2. Evaluate income limits
    3. Match occupation with scheme category
    4. Check disability status
    5. Mark documents as applicable/not applicable
    6. Provide reasons for exclusions
    """
```

### Completion Tracking

```python
def calculate_completion_percentage(
    documents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculates completion statistics.

    Metrics:
    - Total required documents
    - Total uploaded documents
    - Total verified documents
    - Completion percentage (uploaded/required)
    - Verification percentage (verified/required)
    - Is complete flag
    """
```

## Integration with Application Flow

### Step 1: User Profile Collection

User provides demographic information during registration

### Step 2: Scheme Discovery

User discovers eligible schemes through eligibility engine

### Step 3: Checklist Generation

System generates personalized document checklist for selected scheme

### Step 4: Document Procurement

User obtains required documents using provided guidance

### Step 5: Document Upload

User uploads documents through the application

### Step 6: Status Tracking

System tracks upload status and calculates completion

### Step 7: Application Submission

Once all required documents are uploaded, user can submit application

## Testing

Run the test suite:

```bash
python lambda/test_document_checklist.py
```

Test coverage includes:

- ✓ Document personalization based on user profile
- ✓ Procurement guidance generation
- ✓ Completion percentage calculation
- ✓ Upload status tracking
- ✓ Checklist summary generation

## Requirements Validation

This implementation satisfies:

**Requirement 5.1**: Application Assistance

- ✓ Provides complete list of required documents
- ✓ Explains each document in simple terms
- ✓ Provides examples and guidance

**Requirement 5.3**: Document Guidance

- ✓ Explains how to obtain missing documents
- ✓ Provides alternative options where available
- ✓ Includes processing times and requirements

## Benefits

1. **Reduced Confusion**: Users know exactly what documents they need
2. **Time Savings**: Users don't waste time on unnecessary documents
3. **Clear Guidance**: Step-by-step instructions for obtaining each document
4. **Progress Tracking**: Visual feedback on application completion
5. **Multilingual**: Accessible to users in their preferred language
6. **Personalized**: Tailored to each user's specific situation

## Future Enhancements

1. **Document Verification**: Automated verification using OCR and AI
2. **Expiry Tracking**: Alert users when documents are about to expire
3. **Document Templates**: Provide downloadable templates for applications
4. **Alternative Documents**: Suggest alternative documents when primary is unavailable
5. **Offline Support**: Cache checklists for offline access
6. **SMS Notifications**: Send reminders for pending documents
7. **Document Sharing**: Allow users to reuse documents across applications

## Error Handling

The function handles:

- Missing scheme data
- Missing user profile
- Invalid application IDs
- OpenSearch connection errors
- DynamoDB access errors

All errors return appropriate HTTP status codes and user-friendly messages.

## Performance

- **Response Time**: < 500ms for checklist generation
- **Memory**: 512MB Lambda allocation
- **Timeout**: 30 seconds
- **Caching**: Scheme data cached in OpenSearch
- **Optimization**: Minimal database queries through efficient data fetching

## Security

- **Encryption**: All data encrypted at rest and in transit
- **Access Control**: IAM roles with least privilege
- **API Keys**: Required for all API endpoints
- **Data Privacy**: User data handled according to privacy requirements
- **Audit Logging**: All operations logged to CloudWatch

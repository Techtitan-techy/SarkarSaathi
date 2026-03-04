"""
SarkariSaathi - Core Data Models

This module contains all Python data models and types used across
the SarkariSaathi application.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import re


# ========================================
# Enums
# ========================================

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer-not-to-say"


class Category(str, Enum):
    GENERAL = "General"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    EWS = "EWS"


class SchemeCategory(str, Enum):
    AGRICULTURE = "agriculture"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    EMPLOYMENT = "employment"
    HOUSING = "housing"
    SOCIAL_WELFARE = "social-welfare"
    FINANCIAL_INCLUSION = "financial-inclusion"
    WOMEN_EMPOWERMENT = "women-empowerment"
    SENIOR_CITIZEN = "senior-citizen"
    DISABILITY = "disability"


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in-progress"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under-review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CLARIFICATION = "requires-clarification"


class ConversationState(str, Enum):
    WELCOME = "welcome"
    PROFILE_COLLECTION = "profile-collection"
    SCHEME_DISCOVERY = "scheme-discovery"
    ELIGIBILITY_CHECK = "eligibility-check"
    APPLICATION_GUIDANCE = "application-guidance"
    DOCUMENT_CHECKLIST = "document-checklist"
    APPLICATION_SUBMISSION = "application-submission"
    TRACKING = "tracking"
    ENDED = "ended"


class Channel(str, Enum):
    VOICE = "voice"
    SMS = "sms"
    IVR = "ivr"
    WEB = "web"


class ErrorType(str, Enum):
    VALIDATION_ERROR = "validation-error"
    AUTHENTICATION_ERROR = "authentication-error"
    AUTHORIZATION_ERROR = "authorization-error"
    NOT_FOUND = "not-found"
    SERVICE_UNAVAILABLE = "service-unavailable"
    RATE_LIMIT_EXCEEDED = "rate-limit-exceeded"
    INTERNAL_ERROR = "internal-error"


# ========================================
# User Profile Models
# ========================================

@dataclass
class Demographics:
    age: int
    gender: Gender
    state: str
    district: str
    income: int  # Annual income in INR
    category: Category
    occupation: str
    education: str
    family_size: int
    has_disability: bool
    disability_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'age': self.age,
            'gender': self.gender.value,
            'state': self.state,
            'district': self.district,
            'income': self.income,
            'category': self.category.value,
            'occupation': self.occupation,
            'education': self.education,
            'family_size': self.family_size,
            'has_disability': self.has_disability,
            'disability_type': self.disability_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Demographics':
        return cls(
            age=data['age'],
            gender=Gender(data['gender']),
            state=data['state'],
            district=data['district'],
            income=data['income'],
            category=Category(data['category']),
            occupation=data['occupation'],
            education=data['education'],
            family_size=data['family_size'],
            has_disability=data['has_disability'],
            disability_type=data.get('disability_type')
        )


@dataclass
class ApplicationSummary:
    application_id: str
    scheme_id: str
    scheme_name: str
    status: ApplicationStatus
    submitted_at: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'applicationId': self.application_id,
            'schemeId': self.scheme_id,
            'schemeName': self.scheme_name,
            'status': self.status.value,
            'submittedAt': self.submitted_at,
            'lastUpdated': self.last_updated
        }


@dataclass
class UserProfile:
    user_id: str
    phone_number: str
    preferred_language: str
    demographics: Demographics
    eligible_schemes: List[str] = field(default_factory=list)
    applications: List[ApplicationSummary] = field(default_factory=list)
    consent_given: bool = False
    consent_timestamp: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'userId': self.user_id,
            'phoneNumber': self.phone_number,
            'preferredLanguage': self.preferred_language,
            'demographics': self.demographics.to_dict(),
            'eligibleSchemes': self.eligible_schemes,
            'applications': [app.to_dict() for app in self.applications],
            'consentGiven': self.consent_given,
            'consentTimestamp': self.consent_timestamp,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }


# ========================================
# Government Scheme Models
# ========================================

@dataclass
class CriteriaRule:
    field: str
    operator: str  # 'equals', 'not-equals', 'greater-than', 'less-than', 'contains'
    value: Any
    description: Dict[str, str]  # Multi-language descriptions

    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value,
            'description': self.description
        }


@dataclass
class EligibilityCriteria:
    age_range: Dict[str, int]  # {'min': 18, 'max': 60}
    income_range: Dict[str, int]  # {'min': 0, 'max': 500000}
    allowed_states: List[str]
    allowed_categories: List[str]
    required_occupations: List[str]
    excluded_occupations: List[str]
    additional_criteria: List[CriteriaRule] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ageRange': self.age_range,
            'incomeRange': self.income_range,
            'allowedStates': self.allowed_states,
            'allowedCategories': self.allowed_categories,
            'requiredOccupations': self.required_occupations,
            'excludedOccupations': self.excluded_occupations,
            'additionalCriteria': [rule.to_dict() for rule in self.additional_criteria]
        }


@dataclass
class Benefit:
    type: str  # 'financial', 'subsidy', 'service', 'training', 'other'
    description: Dict[str, str]  # Multi-language
    amount: Optional[int] = None
    frequency: Optional[str] = None  # 'one-time', 'monthly', 'quarterly', 'annual'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'description': self.description,
            'amount': self.amount,
            'frequency': self.frequency
        }


@dataclass
class ApplicationStep:
    step_number: int
    title: Dict[str, str]  # Multi-language
    description: Dict[str, str]  # Multi-language
    estimated_time: str
    is_optional: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stepNumber': self.step_number,
            'title': self.title,
            'description': self.description,
            'estimatedTime': self.estimated_time,
            'isOptional': self.is_optional
        }


@dataclass
class Document:
    document_id: str
    name: Dict[str, str]  # Multi-language
    description: Dict[str, str]  # Multi-language
    is_required: bool
    alternatives: List[str] = field(default_factory=list)
    how_to_obtain: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'documentId': self.document_id,
            'name': self.name,
            'description': self.description,
            'isRequired': self.is_required,
            'alternatives': self.alternatives,
            'howToObtain': self.how_to_obtain
        }


@dataclass
class Deadline:
    type: str  # 'application', 'document-submission', 'verification'
    date: str  # ISO 8601 format
    description: Dict[str, str]  # Multi-language

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'date': self.date,
            'description': self.description
        }


@dataclass
class ContactInfo:
    helpline_number: str
    email: str
    website: str
    office_address: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'helplineNumber': self.helpline_number,
            'email': self.email,
            'website': self.website,
            'officeAddress': self.office_address
        }


@dataclass
class Scheme:
    scheme_id: str
    name: Dict[str, str]  # Multi-language names
    description: Dict[str, str]  # Multi-language descriptions
    eligibility_criteria: EligibilityCriteria
    benefits: List[Benefit]
    application_process: List[ApplicationStep]
    required_documents: List[Document]
    deadlines: List[Deadline]
    contact_info: ContactInfo
    category: SchemeCategory
    launching_authority: str
    state: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'schemeId': self.scheme_id,
            'name': self.name,
            'description': self.description,
            'eligibilityCriteria': self.eligibility_criteria.to_dict(),
            'benefits': [b.to_dict() for b in self.benefits],
            'applicationProcess': [step.to_dict() for step in self.application_process],
            'requiredDocuments': [doc.to_dict() for doc in self.required_documents],
            'deadlines': [d.to_dict() for d in self.deadlines],
            'contactInfo': self.contact_info.to_dict(),
            'category': self.category.value,
            'launchingAuthority': self.launching_authority,
            'state': self.state,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }


# ========================================
# Application Models
# ========================================

@dataclass
class DocumentReference:
    document_id: str
    document_name: str
    s3_key: str
    uploaded_at: str
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'documentId': self.document_id,
            'documentName': self.document_name,
            's3Key': self.s3_key,
            'uploadedAt': self.uploaded_at,
            'verified': self.verified
        }


@dataclass
class Application:
    application_id: str
    user_id: str
    scheme_id: str
    status: ApplicationStatus
    form_data: Dict[str, Any]
    documents: List[DocumentReference] = field(default_factory=list)
    submitted_at: Optional[str] = None
    tracking_number: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'applicationId': self.application_id,
            'userId': self.user_id,
            'schemeId': self.scheme_id,
            'status': self.status.value,
            'formData': self.form_data,
            'documents': [doc.to_dict() for doc in self.documents],
            'submittedAt': self.submitted_at,
            'trackingNumber': self.tracking_number,
            'lastUpdated': self.last_updated,
            'createdAt': self.created_at
        }


# ========================================
# Session Models
# ========================================

@dataclass
class ConversationTurn:
    timestamp: str
    user_input: str
    system_response: str
    intent: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'userInput': self.user_input,
            'systemResponse': self.system_response,
            'intent': self.intent,
            'confidence': self.confidence
        }


@dataclass
class ConversationContext:
    collected_data: Dict[str, Any] = field(default_factory=dict)
    current_scheme_id: Optional[str] = None
    current_application_id: Optional[str] = None
    pending_questions: List[str] = field(default_factory=list)
    last_intent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'collectedData': self.collected_data,
            'currentSchemeId': self.current_scheme_id,
            'currentApplicationId': self.current_application_id,
            'pendingQuestions': self.pending_questions,
            'lastIntent': self.last_intent
        }


@dataclass
class Session:
    session_id: str
    channel: Channel
    language: str
    current_state: ConversationState
    context: ConversationContext
    history: List[ConversationTurn] = field(default_factory=list)
    user_id: Optional[str] = None
    phone_number: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl: int = field(default_factory=lambda: int(datetime.utcnow().timestamp()) + 86400)  # 24 hours

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sessionId': self.session_id,
            'userId': self.user_id,
            'phoneNumber': self.phone_number,
            'channel': self.channel.value,
            'language': self.language,
            'currentState': self.current_state.value,
            'context': self.context.to_dict(),
            'history': [turn.to_dict() for turn in self.history],
            'createdAt': self.created_at,
            'lastActivity': self.last_activity,
            'ttl': self.ttl
        }


# ========================================
# Validation Functions
# ========================================

def is_valid_phone_number(phone: str) -> bool:
    """Validate Indian phone number format: +91 followed by 10 digits"""
    pattern = r'^\+91[6-9]\d{9}$'
    return bool(re.match(pattern, phone))


def is_valid_language_code(lang: str) -> bool:
    """Check if language code is supported"""
    supported_languages = ['en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa']
    return lang in supported_languages


def validate_demographics(demographics: Demographics) -> List[str]:
    """Validate demographics data and return list of errors"""
    errors = []
    
    if demographics.age < 0 or demographics.age > 150:
        errors.append('Invalid age')
    
    if demographics.income < 0:
        errors.append('Invalid income')
    
    if demographics.family_size < 1:
        errors.append('Invalid family size')
    
    if not demographics.state or demographics.state.strip() == '':
        errors.append('State is required')
    
    return errors


# ========================================
# API Response Models
# ========================================

@dataclass
class ErrorResponse:
    error_code: str
    error_message: str
    error_type: ErrorType
    retryable: bool
    suggested_action: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'errorCode': self.error_code,
            'errorMessage': self.error_message,
            'errorType': self.error_type.value,
            'retryable': self.retryable,
            'suggestedAction': self.suggested_action,
            'timestamp': self.timestamp
        }


@dataclass
class ApiResponse:
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorResponse] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'success': self.success,
            'data': self.data,
        }
        if self.error:
            result['error'] = self.error.to_dict()
        if self.metadata:
            result['metadata'] = self.metadata
        return result

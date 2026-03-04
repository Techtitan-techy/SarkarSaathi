/**
 * Core TypeScript interfaces and types for SarkariSaathi
 * Defines data models for users, schemes, applications, and sessions
 */

/**
 * Multi-language content support for scheme information
 */
export interface MultiLanguageContent {
  en: string;
  hi: string;
  ta?: string;
  te?: string;
  bn?: string;
  mr?: string;
  gu?: string;
  kn?: string;
  ml?: string;
  pa?: string;
}

/**
 * Supported languages in the system
 */
export type SupportedLanguage =
  | "en"
  | "hi"
  | "ta"
  | "te"
  | "bn"
  | "mr"
  | "gu"
  | "kn"
  | "ml"
  | "pa";

/**
 * User demographic categories
 */
export type UserCategory = "General" | "OBC" | "SC" | "ST" | "EWS";

/**
 * Gender options
 */
export type Gender = "Male" | "Female" | "Other" | "PreferNotToSay";

/**
 * Application status tracking
 */
export type ApplicationStatus =
  | "draft"
  | "in_progress"
  | "submitted"
  | "under_review"
  | "approved"
  | "rejected"
  | "completed";

/**
 * Scheme categories
 */
export type SchemeCategory =
  | "education"
  | "healthcare"
  | "employment"
  | "agriculture"
  | "housing"
  | "social_welfare"
  | "financial_assistance"
  | "skill_development"
  | "women_empowerment"
  | "senior_citizen"
  | "disability"
  | "other";

/**
 * User demographic information
 */
export interface Demographics {
  age: number;
  gender: Gender;
  state: string;
  district: string;
  income: number;
  category: UserCategory;
  occupation: string;
  education: string;
  familySize: number;
  hasDisability: boolean;
  isMinority?: boolean;
  isBPL?: boolean; // Below Poverty Line
}

/**
 * User profile entity
 */
export interface UserProfile {
  userId: string;
  phoneNumber: string;
  preferredLanguage: SupportedLanguage;
  demographics: Demographics;
  eligibleSchemes: string[];
  applications: ApplicationSummary[];
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
  consentGiven: boolean;
  dataRetentionConsent: boolean;
}

/**
 * Application summary for user profile
 */
export interface ApplicationSummary {
  applicationId: string;
  schemeId: string;
  schemeName: string;
  status: ApplicationStatus;
  submittedAt?: string;
  lastUpdatedAt: string;
}

/**
 * Eligibility criteria for schemes
 */
export interface EligibilityCriteria {
  ageRange: { min: number; max: number };
  incomeRange: { min: number; max: number };
  allowedStates: string[];
  allowedCategories: UserCategory[];
  requiredOccupations?: string[];
  excludedOccupations?: string[];
  genderRestriction?: Gender[];
  educationRequirement?: string[];
  disabilityRequired?: boolean;
  minorityRequired?: boolean;
  bplRequired?: boolean;
  additionalCriteria?: CriteriaRule[];
}

/**
 * Additional criteria rule for complex eligibility
 */
export interface CriteriaRule {
  field: string;
  operator:
    | "equals"
    | "not_equals"
    | "greater_than"
    | "less_than"
    | "contains"
    | "in";
  value: any;
  description: string;
}

/**
 * Benefit information
 */
export interface Benefit {
  type: "financial" | "subsidy" | "service" | "training" | "other";
  amount?: number;
  description: MultiLanguageContent;
  frequency?: "one_time" | "monthly" | "quarterly" | "yearly";
}

/**
 * Required document for application
 */
export interface Document {
  documentId: string;
  name: MultiLanguageContent;
  description: MultiLanguageContent;
  required: boolean;
  format: string[];
  maxSizeKB: number;
  alternativeDocuments?: string[];
}

/**
 * Application step
 */
export interface ApplicationStep {
  stepNumber: number;
  title: MultiLanguageContent;
  description: MultiLanguageContent;
  estimatedTimeMinutes: number;
  requiredDocuments: string[];
  formFields?: FormField[];
}

/**
 * Form field definition
 */
export interface FormField {
  fieldId: string;
  label: MultiLanguageContent;
  type: "text" | "number" | "date" | "select" | "file" | "boolean";
  required: boolean;
  validation?: ValidationRule;
  options?: string[];
  helpText?: MultiLanguageContent;
}

/**
 * Validation rule for form fields
 */
export interface ValidationRule {
  pattern?: string;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  customValidator?: string;
}

/**
 * Deadline information
 */
export interface Deadline {
  type: "application" | "document_submission" | "verification";
  date: string;
  description: MultiLanguageContent;
  isRecurring: boolean;
  recurringPattern?: string;
}

/**
 * Contact information
 */
export interface ContactInfo {
  department: string;
  phone: string[];
  email: string[];
  website: string;
  helplineNumber?: string;
  officeAddress?: string;
}

/**
 * Government scheme entity
 */
export interface Scheme {
  schemeId: string;
  name: MultiLanguageContent;
  description: MultiLanguageContent;
  eligibilityCriteria: EligibilityCriteria;
  benefits: Benefit[];
  applicationProcess: ApplicationStep[];
  requiredDocuments: Document[];
  deadlines: Deadline[];
  contactInfo: ContactInfo;
  category: SchemeCategory;
  state: string;
  launchingAuthority: string;
  officialUrl: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * Document reference in application
 */
export interface DocumentReference {
  documentId: string;
  fileName: string;
  s3Key: string;
  uploadedAt: string;
  fileSize: number;
  mimeType: string;
  verified: boolean;
}

/**
 * Application entity
 */
export interface Application {
  applicationId: string;
  userId: string;
  schemeId: string;
  status: ApplicationStatus;
  formData: Record<string, any>;
  documents: DocumentReference[];
  submittedAt?: string;
  trackingNumber?: string;
  statusHistory: StatusHistoryEntry[];
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Status history entry for application tracking
 */
export interface StatusHistoryEntry {
  status: ApplicationStatus;
  timestamp: string;
  notes?: string;
  updatedBy?: string;
}

/**
 * Session entity for conversation tracking
 */
export interface Session {
  sessionId: string;
  userId?: string;
  phoneNumber?: string;
  language: SupportedLanguage;
  context: SessionContext;
  startedAt: string;
  lastActivityAt: string;
  ttl: number; // Unix timestamp for DynamoDB TTL
  isActive: boolean;
}

/**
 * Session context for maintaining conversation state
 */
export interface SessionContext {
  currentIntent?: string;
  currentSchemeId?: string;
  currentApplicationId?: string;
  collectedData: Record<string, any>;
  conversationHistory: ConversationTurn[];
  eligibilityAssessmentInProgress?: boolean;
}

/**
 * Conversation turn in session
 */
export interface ConversationTurn {
  timestamp: string;
  userInput: string;
  systemResponse: string;
  intent?: string;
  confidence?: number;
}

/**
 * SarkariSaathi - Core Type Definitions
 *
 * This file contains all TypeScript interfaces and types used across
 * the SarkariSaathi application for type safety and consistency.
 */

// ========================================
// User Profile Types
// ========================================

export interface UserProfile {
  userId: string;
  phoneNumber: string;
  preferredLanguage: string;
  demographics: Demographics;
  eligibleSchemes: string[];
  applications: ApplicationSummary[];
  consentGiven: boolean;
  consentTimestamp?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Demographics {
  age: number;
  gender: "male" | "female" | "other" | "prefer-not-to-say";
  state: string;
  district: string;
  income: number; // Annual income in INR
  category: "General" | "OBC" | "SC" | "ST" | "EWS";
  occupation: string;
  education: string;
  familySize: number;
  hasDisability: boolean;
  disabilityType?: string;
}

// ========================================
// Government Scheme Types
// ========================================

export interface Scheme {
  schemeId: string;
  name: Record<string, string>; // Multi-language names: { en: "...", hi: "...", ta: "..." }
  description: Record<string, string>; // Multi-language descriptions
  eligibilityCriteria: EligibilityCriteria;
  benefits: Benefit[];
  applicationProcess: ApplicationStep[];
  requiredDocuments: Document[];
  deadlines: Deadline[];
  contactInfo: ContactInfo;
  category: SchemeCategory;
  launchingAuthority: string;
  state?: string; // Optional: for state-specific schemes
  createdAt: string;
  updatedAt: string;
}

export type SchemeCategory =
  | "agriculture"
  | "education"
  | "healthcare"
  | "employment"
  | "housing"
  | "social-welfare"
  | "financial-inclusion"
  | "women-empowerment"
  | "senior-citizen"
  | "disability";

export interface EligibilityCriteria {
  ageRange: { min: number; max: number };
  incomeRange: { min: number; max: number };
  allowedStates: string[];
  allowedCategories: string[];
  requiredOccupations: string[];
  excludedOccupations: string[];
  additionalCriteria: CriteriaRule[];
}

export interface CriteriaRule {
  field: string;
  operator: "equals" | "not-equals" | "greater-than" | "less-than" | "contains";
  value: any;
  description: Record<string, string>;
}

export interface Benefit {
  type: "financial" | "subsidy" | "service" | "training" | "other";
  amount?: number;
  description: Record<string, string>;
  frequency?: "one-time" | "monthly" | "quarterly" | "annual";
}

export interface ApplicationStep {
  stepNumber: number;
  title: Record<string, string>;
  description: Record<string, string>;
  estimatedTime: string; // e.g., "15 minutes"
  isOptional: boolean;
}

export interface Document {
  documentId: string;
  name: Record<string, string>;
  description: Record<string, string>;
  isRequired: boolean;
  alternatives?: string[]; // Alternative document IDs
  howToObtain?: Record<string, string>;
}

export interface Deadline {
  type: "application" | "document-submission" | "verification";
  date: string; // ISO 8601 format
  description: Record<string, string>;
}

export interface ContactInfo {
  helplineNumber: string;
  email: string;
  website: string;
  officeAddress?: Record<string, string>;
}

// ========================================
// Application Types
// ========================================

export interface Application {
  applicationId: string;
  userId: string;
  schemeId: string;
  status: ApplicationStatus;
  formData: Record<string, any>;
  documents: DocumentReference[];
  submittedAt?: string;
  trackingNumber?: string;
  lastUpdated: string;
  createdAt: string;
}

export type ApplicationStatus =
  | "draft"
  | "in-progress"
  | "submitted"
  | "under-review"
  | "approved"
  | "rejected"
  | "requires-clarification";

export interface ApplicationSummary {
  applicationId: string;
  schemeId: string;
  schemeName: string;
  status: ApplicationStatus;
  submittedAt?: string;
  lastUpdated: string;
}

export interface DocumentReference {
  documentId: string;
  documentName: string;
  s3Key: string;
  uploadedAt: string;
  verified: boolean;
}

// ========================================
// Session Types
// ========================================

export interface Session {
  sessionId: string;
  userId?: string;
  phoneNumber?: string;
  channel: "voice" | "sms" | "ivr" | "web";
  language: string;
  currentState: ConversationState;
  context: ConversationContext;
  history: ConversationTurn[];
  createdAt: string;
  lastActivity: string;
  ttl: number; // Unix timestamp for DynamoDB TTL
}

export type ConversationState =
  | "welcome"
  | "profile-collection"
  | "scheme-discovery"
  | "eligibility-check"
  | "application-guidance"
  | "document-checklist"
  | "application-submission"
  | "tracking"
  | "ended";

export interface ConversationContext {
  collectedData: Record<string, any>;
  currentSchemeId?: string;
  currentApplicationId?: string;
  pendingQuestions: string[];
  lastIntent?: string;
}

export interface ConversationTurn {
  timestamp: string;
  userInput: string;
  systemResponse: string;
  intent?: string;
  confidence?: number;
}

// ========================================
// Voice Processing Types
// ========================================

export interface VoiceProcessingRequest {
  audioData: Buffer | string; // Base64 encoded audio
  language?: string;
  userId?: string;
  sessionId: string;
}

export interface VoiceProcessingResponse {
  transcription: string;
  confidence: number;
  language: string;
  processingTime: number;
}

export interface TTSRequest {
  text: string;
  language: string;
  voice?: string;
  speed?: number;
}

export interface TTSResponse {
  audioUrl: string;
  duration: number;
  format: string;
  cacheKey: string;
}

// ========================================
// NLU Types
// ========================================

export interface NLURequest {
  text: string;
  context: ConversationContext;
  intent?: string;
  language: string;
}

export interface NLUResponse {
  intent: string;
  entities: Entity[];
  response: string;
  confidence: number;
  suggestedActions: Action[];
}

export interface Entity {
  type: string;
  value: any;
  confidence: number;
}

export interface Action {
  type: string;
  parameters: Record<string, any>;
}

// ========================================
// Eligibility Engine Types
// ========================================

export interface EligibilityQuery {
  userProfile: UserProfile;
  query?: string;
  filters?: SchemeFilter[];
}

export interface SchemeFilter {
  field: string;
  value: any;
  operator?: "equals" | "contains" | "greater-than" | "less-than";
}

export interface EligibilityResponse {
  schemes: SchemeMatch[];
  totalMatches: number;
}

export interface SchemeMatch {
  scheme: Scheme;
  eligibilityScore: number;
  matchReasons: string[];
  requiredDocuments: Document[];
  applicationSteps: ApplicationStep[];
  estimatedBenefit?: number;
}

// ========================================
// SMS/IVR Types
// ========================================

export interface SMSRequest {
  phoneNumber: string;
  message: string;
  language: string;
  userId?: string;
}

export interface SMSResponse {
  messageId: string;
  status: "sent" | "failed";
  timestamp: string;
}

export interface IVRSession {
  callId: string;
  phoneNumber: string;
  currentStep: string;
  userInputs: Record<string, any>;
  language: string;
  startTime: string;
}

// ========================================
// Error Types
// ========================================

export interface ErrorResponse {
  errorCode: string;
  errorMessage: string;
  errorType: ErrorType;
  retryable: boolean;
  suggestedAction?: string;
  timestamp: string;
}

export type ErrorType =
  | "validation-error"
  | "authentication-error"
  | "authorization-error"
  | "not-found"
  | "service-unavailable"
  | "rate-limit-exceeded"
  | "internal-error";

// ========================================
// API Response Types
// ========================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ErrorResponse;
  metadata?: {
    requestId: string;
    timestamp: string;
    processingTime: number;
  };
}

// ========================================
// Validation Functions
// ========================================

export function isValidPhoneNumber(phone: string): boolean {
  // Indian phone number validation: +91 followed by 10 digits
  const phoneRegex = /^\+91[6-9]\d{9}$/;
  return phoneRegex.test(phone);
}

export function isValidLanguageCode(lang: string): boolean {
  const supportedLanguages = [
    "en",
    "hi",
    "ta",
    "te",
    "bn",
    "mr",
    "gu",
    "kn",
    "ml",
    "pa",
  ];
  return supportedLanguages.includes(lang);
}

export function validateDemographics(demographics: Demographics): string[] {
  const errors: string[] = [];

  if (demographics.age < 0 || demographics.age > 150) {
    errors.push("Invalid age");
  }

  if (demographics.income < 0) {
    errors.push("Invalid income");
  }

  if (demographics.familySize < 1) {
    errors.push("Invalid family size");
  }

  if (!demographics.state || demographics.state.trim() === "") {
    errors.push("State is required");
  }

  return errors;
}

/**
 * Validation functions for core entities
 * Ensures data integrity and business rule compliance
 */

import {
  UserProfile,
  Demographics,
  Scheme,
  Application,
  Session,
  SupportedLanguage,
  UserCategory,
  Gender,
  ApplicationStatus,
  SchemeCategory,
} from "./types";

/**
 * Validation result
 */
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

/**
 * Validate phone number format (Indian mobile numbers)
 */
export function validatePhoneNumber(phoneNumber: string): boolean {
  const phoneRegex = /^[6-9]\d{9}$/;
  return phoneRegex.test(phoneNumber);
}

/**
 * Validate email format
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate supported language
 */
export function validateLanguage(
  language: string,
): language is SupportedLanguage {
  const supportedLanguages: SupportedLanguage[] = [
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
  return supportedLanguages.includes(language as SupportedLanguage);
}

/**
 * Validate demographics data
 */
export function validateDemographics(
  demographics: Demographics,
): ValidationResult {
  const errors: string[] = [];

  // Age validation
  if (demographics.age < 0 || demographics.age > 150) {
    errors.push("Age must be between 0 and 150");
  }

  // Income validation
  if (demographics.income < 0) {
    errors.push("Income cannot be negative");
  }

  // State validation (non-empty)
  if (!demographics.state || demographics.state.trim() === "") {
    errors.push("State is required");
  }

  // District validation (non-empty)
  if (!demographics.district || demographics.district.trim() === "") {
    errors.push("District is required");
  }

  // Category validation
  const validCategories: UserCategory[] = ["General", "OBC", "SC", "ST", "EWS"];
  if (!validCategories.includes(demographics.category)) {
    errors.push("Invalid user category");
  }

  // Gender validation
  const validGenders: Gender[] = ["Male", "Female", "Other", "PreferNotToSay"];
  if (!validGenders.includes(demographics.gender)) {
    errors.push("Invalid gender");
  }

  // Family size validation
  if (demographics.familySize < 1 || demographics.familySize > 50) {
    errors.push("Family size must be between 1 and 50");
  }

  // Occupation validation (non-empty)
  if (!demographics.occupation || demographics.occupation.trim() === "") {
    errors.push("Occupation is required");
  }

  // Education validation (non-empty)
  if (!demographics.education || demographics.education.trim() === "") {
    errors.push("Education is required");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate user profile
 */
export function validateUserProfile(profile: UserProfile): ValidationResult {
  const errors: string[] = [];

  // User ID validation
  if (!profile.userId || profile.userId.trim() === "") {
    errors.push("User ID is required");
  }

  // Phone number validation
  if (!validatePhoneNumber(profile.phoneNumber)) {
    errors.push("Invalid phone number format");
  }

  // Language validation
  if (!validateLanguage(profile.preferredLanguage)) {
    errors.push("Invalid preferred language");
  }

  // Demographics validation
  const demographicsValidation = validateDemographics(profile.demographics);
  if (!demographicsValidation.isValid) {
    errors.push(...demographicsValidation.errors);
  }

  // Consent validation
  if (!profile.consentGiven) {
    errors.push("User consent is required");
  }

  // Timestamps validation
  if (!profile.createdAt || !isValidISODate(profile.createdAt)) {
    errors.push("Invalid createdAt timestamp");
  }

  if (!profile.updatedAt || !isValidISODate(profile.updatedAt)) {
    errors.push("Invalid updatedAt timestamp");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate scheme data
 */
export function validateScheme(scheme: Scheme): ValidationResult {
  const errors: string[] = [];

  // Scheme ID validation
  if (!scheme.schemeId || scheme.schemeId.trim() === "") {
    errors.push("Scheme ID is required");
  }

  // Name validation (at least English and Hindi)
  if (!scheme.name.en || scheme.name.en.trim() === "") {
    errors.push("Scheme name in English is required");
  }
  if (!scheme.name.hi || scheme.name.hi.trim() === "") {
    errors.push("Scheme name in Hindi is required");
  }

  // Description validation
  if (!scheme.description.en || scheme.description.en.trim() === "") {
    errors.push("Scheme description in English is required");
  }

  // Category validation
  const validCategories: SchemeCategory[] = [
    "education",
    "healthcare",
    "employment",
    "agriculture",
    "housing",
    "social_welfare",
    "financial_assistance",
    "skill_development",
    "women_empowerment",
    "senior_citizen",
    "disability",
    "other",
  ];
  if (!validCategories.includes(scheme.category)) {
    errors.push("Invalid scheme category");
  }

  // Eligibility criteria validation
  if (!scheme.eligibilityCriteria) {
    errors.push("Eligibility criteria is required");
  } else {
    if (
      scheme.eligibilityCriteria.ageRange.min < 0 ||
      scheme.eligibilityCriteria.ageRange.max > 150 ||
      scheme.eligibilityCriteria.ageRange.min >
        scheme.eligibilityCriteria.ageRange.max
    ) {
      errors.push("Invalid age range in eligibility criteria");
    }

    if (
      scheme.eligibilityCriteria.incomeRange.min < 0 ||
      scheme.eligibilityCriteria.incomeRange.min >
        scheme.eligibilityCriteria.incomeRange.max
    ) {
      errors.push("Invalid income range in eligibility criteria");
    }

    if (
      !scheme.eligibilityCriteria.allowedStates ||
      scheme.eligibilityCriteria.allowedStates.length === 0
    ) {
      errors.push("At least one allowed state is required");
    }
  }

  // Benefits validation
  if (!scheme.benefits || scheme.benefits.length === 0) {
    errors.push("At least one benefit is required");
  }

  // Contact info validation
  if (!scheme.contactInfo || !scheme.contactInfo.department) {
    errors.push("Contact information is required");
  }

  // State validation
  if (!scheme.state || scheme.state.trim() === "") {
    errors.push("State is required");
  }

  // Launching authority validation
  if (!scheme.launchingAuthority || scheme.launchingAuthority.trim() === "") {
    errors.push("Launching authority is required");
  }

  // Official URL validation
  if (!scheme.officialUrl || !isValidUrl(scheme.officialUrl)) {
    errors.push("Valid official URL is required");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate application data
 */
export function validateApplication(
  application: Application,
): ValidationResult {
  const errors: string[] = [];

  // Application ID validation
  if (!application.applicationId || application.applicationId.trim() === "") {
    errors.push("Application ID is required");
  }

  // User ID validation
  if (!application.userId || application.userId.trim() === "") {
    errors.push("User ID is required");
  }

  // Scheme ID validation
  if (!application.schemeId || application.schemeId.trim() === "") {
    errors.push("Scheme ID is required");
  }

  // Status validation
  const validStatuses: ApplicationStatus[] = [
    "draft",
    "in_progress",
    "submitted",
    "under_review",
    "approved",
    "rejected",
    "completed",
  ];
  if (!validStatuses.includes(application.status)) {
    errors.push("Invalid application status");
  }

  // Form data validation
  if (!application.formData || typeof application.formData !== "object") {
    errors.push("Form data must be an object");
  }

  // Documents validation
  if (!Array.isArray(application.documents)) {
    errors.push("Documents must be an array");
  }

  // Status history validation
  if (
    !Array.isArray(application.statusHistory) ||
    application.statusHistory.length === 0
  ) {
    errors.push(
      "Status history is required and must contain at least one entry",
    );
  }

  // Timestamps validation
  if (!application.createdAt || !isValidISODate(application.createdAt)) {
    errors.push("Invalid createdAt timestamp");
  }

  if (!application.updatedAt || !isValidISODate(application.updatedAt)) {
    errors.push("Invalid updatedAt timestamp");
  }

  // Submitted applications must have submittedAt timestamp
  if (application.status !== "draft" && application.status !== "in_progress") {
    if (!application.submittedAt || !isValidISODate(application.submittedAt)) {
      errors.push(
        "Submitted applications must have a valid submittedAt timestamp",
      );
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate session data
 */
export function validateSession(session: Session): ValidationResult {
  const errors: string[] = [];

  // Session ID validation
  if (!session.sessionId || session.sessionId.trim() === "") {
    errors.push("Session ID is required");
  }

  // Either userId or phoneNumber must be present
  if (!session.userId && !session.phoneNumber) {
    errors.push("Either userId or phoneNumber is required");
  }

  // Phone number validation if present
  if (session.phoneNumber && !validatePhoneNumber(session.phoneNumber)) {
    errors.push("Invalid phone number format");
  }

  // Language validation
  if (!validateLanguage(session.language)) {
    errors.push("Invalid language");
  }

  // Context validation
  if (!session.context || typeof session.context !== "object") {
    errors.push("Session context is required");
  }

  // TTL validation
  if (!session.ttl || session.ttl <= 0) {
    errors.push("Valid TTL is required");
  }

  // Timestamps validation
  if (!session.startedAt || !isValidISODate(session.startedAt)) {
    errors.push("Invalid startedAt timestamp");
  }

  if (!session.lastActivityAt || !isValidISODate(session.lastActivityAt)) {
    errors.push("Invalid lastActivityAt timestamp");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Helper function to validate ISO date strings
 */
function isValidISODate(dateString: string): boolean {
  const date = new Date(dateString);
  return (
    date instanceof Date &&
    !isNaN(date.getTime()) &&
    dateString === date.toISOString()
  );
}

/**
 * Helper function to validate URLs
 */
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate eligibility match between user and scheme
 */
export function validateEligibility(
  demographics: Demographics,
  scheme: Scheme,
): ValidationResult {
  const errors: string[] = [];
  const criteria = scheme.eligibilityCriteria;

  // Age check
  if (
    demographics.age < criteria.ageRange.min ||
    demographics.age > criteria.ageRange.max
  ) {
    errors.push(
      `Age must be between ${criteria.ageRange.min} and ${criteria.ageRange.max}`,
    );
  }

  // Income check
  if (
    demographics.income < criteria.incomeRange.min ||
    demographics.income > criteria.incomeRange.max
  ) {
    errors.push(
      `Income must be between ${criteria.incomeRange.min} and ${criteria.incomeRange.max}`,
    );
  }

  // State check
  if (
    !criteria.allowedStates.includes(demographics.state) &&
    !criteria.allowedStates.includes("All")
  ) {
    errors.push(`Scheme not available in ${demographics.state}`);
  }

  // Category check
  if (!criteria.allowedCategories.includes(demographics.category)) {
    errors.push(`Scheme not available for ${demographics.category} category`);
  }

  // Gender restriction check
  if (
    criteria.genderRestriction &&
    !criteria.genderRestriction.includes(demographics.gender)
  ) {
    errors.push(`Scheme not available for ${demographics.gender}`);
  }

  // Disability requirement check
  if (criteria.disabilityRequired && !demographics.hasDisability) {
    errors.push("Scheme requires disability certificate");
  }

  // Minority requirement check
  if (criteria.minorityRequired && !demographics.isMinority) {
    errors.push("Scheme is only for minority communities");
  }

  // BPL requirement check
  if (criteria.bplRequired && !demographics.isBPL) {
    errors.push("Scheme requires BPL certificate");
  }

  // Occupation checks
  if (criteria.requiredOccupations && criteria.requiredOccupations.length > 0) {
    if (!criteria.requiredOccupations.includes(demographics.occupation)) {
      errors.push(
        `Scheme requires occupation to be one of: ${criteria.requiredOccupations.join(", ")}`,
      );
    }
  }

  if (criteria.excludedOccupations && criteria.excludedOccupations.length > 0) {
    if (criteria.excludedOccupations.includes(demographics.occupation)) {
      errors.push(`Scheme not available for ${demographics.occupation}`);
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

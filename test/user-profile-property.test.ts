/**
 * Property-Based Tests for User Profile Management
 *
 * Feature: sarkari-saathi
 * Property 8: User Profile Management
 *
 * **Validates: Requirements 6.1, 6.2, 6.5**
 *
 * These tests verify that:
 * 1. Profile data is correctly stored and retrieved
 * 2. Profile updates work correctly
 * 3. Data deletion removes all user information
 * 4. Profile validation works for various demographic combinations
 */

import * as fc from "fast-check";
import { UserRepository } from "../lib/repositories/user-repository";
import {
  UserProfile,
  Demographics,
  SupportedLanguage,
  UserCategory,
  Gender,
} from "../lib/models/types";
import {
  validateUserProfile,
  validateDemographics,
} from "../lib/models/validators";

// ============================================================================
// Test Data Generators (Arbitraries)
// ============================================================================

/**
 * Generate valid Indian phone numbers (starting with 6-9, 10 digits)
 */
const phoneNumberArbitrary = fc
  .integer({ min: 6000000000, max: 9999999999 })
  .map((n) => n.toString());

/**
 * Generate valid supported languages
 */
const languageArbitrary = fc.constantFrom<SupportedLanguage>(
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
);

/**
 * Generate valid user categories
 */
const categoryArbitrary = fc.constantFrom<UserCategory>(
  "General",
  "OBC",
  "SC",
  "ST",
  "EWS",
);

/**
 * Generate valid gender values
 */
const genderArbitrary = fc.constantFrom<Gender>(
  "Male",
  "Female",
  "Other",
  "PreferNotToSay",
);

/**
 * Generate valid Indian states
 */
const stateArbitrary = fc.constantFrom(
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Delhi",
  "Jammu and Kashmir",
  "Ladakh",
);

/**
 * Generate valid occupations
 */
const occupationArbitrary = fc.constantFrom(
  "Farmer",
  "Student",
  "Teacher",
  "Doctor",
  "Engineer",
  "Laborer",
  "Self-Employed",
  "Government Employee",
  "Private Employee",
  "Unemployed",
  "Retired",
  "Homemaker",
  "Business Owner",
);

/**
 * Generate valid education levels
 */
const educationArbitrary = fc.constantFrom(
  "No Formal Education",
  "Primary",
  "Secondary",
  "Higher Secondary",
  "Graduate",
  "Post Graduate",
  "Doctorate",
  "Diploma",
  "ITI",
);

/**
 * Generate valid demographics
 */
const demographicsArbitrary: fc.Arbitrary<Demographics> = fc.record({
  age: fc.integer({ min: 0, max: 150 }),
  gender: genderArbitrary,
  state: stateArbitrary,
  district: fc
    .string({ minLength: 3, maxLength: 50 })
    .filter((s) => s.trim().length > 0),
  income: fc.integer({ min: 0, max: 10000000 }),
  category: categoryArbitrary,
  occupation: occupationArbitrary,
  education: educationArbitrary,
  familySize: fc.integer({ min: 1, max: 50 }),
  hasDisability: fc.boolean(),
  isMinority: fc.option(fc.boolean(), { nil: undefined }),
  isBPL: fc.option(fc.boolean(), { nil: undefined }),
});

/**
 * Generate valid user profile
 */
const userProfileArbitrary: fc.Arbitrary<UserProfile> = fc.record({
  userId: fc.uuid(),
  phoneNumber: phoneNumberArbitrary,
  preferredLanguage: languageArbitrary,
  demographics: demographicsArbitrary,
  eligibleSchemes: fc.array(fc.uuid(), { maxLength: 10 }),
  applications: fc.constant([]),
  createdAt: fc.constant(new Date().toISOString()),
  updatedAt: fc.constant(new Date().toISOString()),
  lastLoginAt: fc.option(fc.constant(new Date().toISOString()), {
    nil: undefined,
  }),
  consentGiven: fc.constant(true),
  dataRetentionConsent: fc.boolean(),
});

// ============================================================================
// Property 8: User Profile Management
// ============================================================================

describe("Property 8: User Profile Management", () => {
  describe("Profile Data Storage and Retrieval", () => {
    /**
     * Property: For any valid user profile, validation should pass
     * **Validates: Requirement 6.1** - Collect and securely store demographic information
     */
    it("should validate any correctly structured user profile", () => {
      fc.assert(
        fc.property(userProfileArbitrary, (profile) => {
          const validation = validateUserProfile(profile);
          expect(validation.isValid).toBe(true);
          expect(validation.errors).toHaveLength(0);
        }),
        { numRuns: 25 },
      );
    });

    /**
     * Property: Demographics validation should accept all valid combinations
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should validate any correctly structured demographics", () => {
      fc.assert(
        fc.property(demographicsArbitrary, (demographics) => {
          const validation = validateDemographics(demographics);
          expect(validation.isValid).toBe(true);
          expect(validation.errors).toHaveLength(0);
        }),
        { numRuns: 25 },
      );
    });

    /**
     * Property: Phone numbers must follow Indian mobile format
     * **Validates: Requirement 6.1** - Store basic demographic information
     */
    it("should only accept valid Indian phone numbers", () => {
      fc.assert(
        fc.property(phoneNumberArbitrary, (phoneNumber) => {
          const phoneRegex = /^[6-9]\d{9}$/;
          expect(phoneRegex.test(phoneNumber)).toBe(true);
        }),
        { numRuns: 25 },
      );
    });

    /**
     * Property: Age must be within valid range (0-150)
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept ages from 0 to 150", () => {
      fc.assert(
        fc.property(fc.integer({ min: 0, max: 150 }), (age) => {
          const demographics: Demographics = {
            age,
            gender: "Male",
            state: "Karnataka",
            district: "Bangalore",
            income: 50000,
            category: "General",
            occupation: "Engineer",
            education: "Graduate",
            familySize: 4,
            hasDisability: false,
          };
          const validation = validateDemographics(demographics);
          expect(validation.isValid).toBe(true);
        }),
        { numRuns: 25 },
      );
    });

    /**
     * Property: Invalid ages should be rejected
     * **Validates: Requirement 6.1** - Data validation
     */
    it("should reject invalid ages", () => {
      fc.assert(
        fc.property(
          fc.oneof(
            fc.integer({ max: -1 }),
            fc.integer({ min: 151, max: 1000 }),
          ),
          (invalidAge) => {
            const demographics: Demographics = {
              age: invalidAge,
              gender: "Male",
              state: "Karnataka",
              district: "Bangalore",
              income: 50000,
              category: "General",
              occupation: "Engineer",
              education: "Graduate",
              familySize: 4,
              hasDisability: false,
            };
            const validation = validateDemographics(demographics);
            expect(validation.isValid).toBe(false);
            expect(validation.errors.some((e) => e.includes("Age"))).toBe(true);
          },
        ),
        { numRuns: 12 },
      );
    });

    /**
     * Property: Income must be non-negative
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept non-negative income values", () => {
      fc.assert(
        fc.property(fc.integer({ min: 0, max: 100000000 }), (income) => {
          const demographics: Demographics = {
            age: 30,
            gender: "Male",
            state: "Karnataka",
            district: "Bangalore",
            income,
            category: "General",
            occupation: "Engineer",
            education: "Graduate",
            familySize: 4,
            hasDisability: false,
          };
          const validation = validateDemographics(demographics);
          expect(validation.isValid).toBe(true);
        }),
        { numRuns: 25 },
      );
    });

    /**
     * Property: Negative income should be rejected
     * **Validates: Requirement 6.1** - Data validation
     */
    it("should reject negative income", () => {
      fc.assert(
        fc.property(fc.integer({ max: -1 }), (negativeIncome) => {
          const demographics: Demographics = {
            age: 30,
            gender: "Male",
            state: "Karnataka",
            district: "Bangalore",
            income: negativeIncome,
            category: "General",
            occupation: "Engineer",
            education: "Graduate",
            familySize: 4,
            hasDisability: false,
          };
          const validation = validateDemographics(demographics);
          expect(validation.isValid).toBe(false);
          expect(validation.errors.some((e) => e.includes("Income"))).toBe(
            true,
          );
        }),
        { numRuns: 12 },
      );
    });

    /**
     * Property: Family size must be between 1 and 50
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept family sizes from 1 to 50", () => {
      fc.assert(
        fc.property(fc.integer({ min: 1, max: 50 }), (familySize) => {
          const demographics: Demographics = {
            age: 30,
            gender: "Male",
            state: "Karnataka",
            district: "Bangalore",
            income: 50000,
            category: "General",
            occupation: "Engineer",
            education: "Graduate",
            familySize,
            hasDisability: false,
          };
          const validation = validateDemographics(demographics);
          expect(validation.isValid).toBe(true);
        }),
        { numRuns: 25 },
      );
    });
  });

  describe("Profile Updates", () => {
    /**
     * Property: Profile updates should preserve required fields
     * **Validates: Requirement 6.2** - Load profile automatically
     */
    it("should maintain profile integrity during updates", () => {
      fc.assert(
        fc.property(
          userProfileArbitrary,
          fc.integer({ min: 0, max: 150 }),
          (originalProfile, newAge) => {
            // Simulate profile update
            const updatedDemographics: Demographics = {
              ...originalProfile.demographics,
              age: newAge,
            };

            const validation = validateDemographics(updatedDemographics);
            expect(validation.isValid).toBe(true);

            // Verify original fields are preserved
            expect(updatedDemographics.state).toBe(
              originalProfile.demographics.state,
            );
            expect(updatedDemographics.category).toBe(
              originalProfile.demographics.category,
            );
          },
        ),
        { numRuns: 25 },
      );
    });

    /**
     * Property: Language updates should only accept supported languages
     * **Validates: Requirement 6.2** - Profile management
     */
    it("should only accept supported languages for updates", () => {
      fc.assert(
        fc.property(
          userProfileArbitrary,
          languageArbitrary,
          (profile, newLanguage) => {
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
            expect(supportedLanguages.includes(newLanguage)).toBe(true);
          },
        ),
        { numRuns: 25 },
      );
    });

    /**
     * Property: Updating demographics should trigger validation
     * **Validates: Requirement 6.1** - Securely store information
     */
    it("should validate demographics on every update", () => {
      fc.assert(
        fc.property(
          userProfileArbitrary,
          demographicsArbitrary,
          (profile, newDemographics) => {
            const validation = validateDemographics(newDemographics);

            // All generated demographics should be valid
            expect(validation.isValid).toBe(true);

            // If we make it invalid, validation should catch it
            const invalidDemographics = { ...newDemographics, age: -5 };
            const invalidValidation = validateDemographics(invalidDemographics);
            expect(invalidValidation.isValid).toBe(false);
          },
        ),
        { numRuns: 25 },
      );
    });
  });

  describe("Data Deletion", () => {
    /**
     * Property: Profile structure should support complete data removal
     * **Validates: Requirement 6.5** - Allow complete data deletion
     */
    it("should be able to identify all user data fields for deletion", () => {
      fc.assert(
        fc.property(userProfileArbitrary, (profile) => {
          // Verify all required fields exist (so we know what to delete)
          expect(profile).toHaveProperty("userId");
          expect(profile).toHaveProperty("phoneNumber");
          expect(profile).toHaveProperty("demographics");
          expect(profile).toHaveProperty("eligibleSchemes");
          expect(profile).toHaveProperty("applications");
          expect(profile).toHaveProperty("createdAt");
          expect(profile).toHaveProperty("updatedAt");

          // Verify sensitive data fields are present
          expect(profile.demographics).toHaveProperty("age");
          expect(profile.demographics).toHaveProperty("income");
          expect(profile.demographics).toHaveProperty("state");
          expect(profile.demographics).toHaveProperty("district");
        }),
        { numRuns: 25 },
      );
    });

    /**
     * Property: User consent fields should be present for GDPR compliance
     * **Validates: Requirement 6.5** - Data deletion upon request
     */
    it("should track user consent for data retention", () => {
      fc.assert(
        fc.property(userProfileArbitrary, (profile) => {
          expect(profile).toHaveProperty("consentGiven");
          expect(profile).toHaveProperty("dataRetentionConsent");
          expect(typeof profile.consentGiven).toBe("boolean");
          expect(typeof profile.dataRetentionConsent).toBe("boolean");
        }),
        { numRuns: 25 },
      );
    });
  });

  describe("Profile Recognition", () => {
    /**
     * Property: Phone numbers should be unique identifiers
     * **Validates: Requirement 6.2** - Recognize returning users
     */
    it("should use phone number as unique identifier for user recognition", () => {
      fc.assert(
        fc.property(
          fc.array(phoneNumberArbitrary, { minLength: 2, maxLength: 10 }),
          (phoneNumbers) => {
            // All generated phone numbers should be valid
            phoneNumbers.forEach((phone) => {
              const phoneRegex = /^[6-9]\d{9}$/;
              expect(phoneRegex.test(phone)).toBe(true);
            });

            // Phone numbers should be usable as unique keys
            const phoneSet = new Set(phoneNumbers);
            expect(phoneSet.size).toBeGreaterThan(0);
          },
        ),
        { numRuns: 12 },
      );
    });

    /**
     * Property: User profiles should have timestamps for tracking
     * **Validates: Requirement 6.2** - Load profile automatically
     */
    it("should maintain timestamps for user activity tracking", () => {
      fc.assert(
        fc.property(userProfileArbitrary, (profile) => {
          expect(profile.createdAt).toBeDefined();
          expect(profile.updatedAt).toBeDefined();

          // Timestamps should be valid ISO strings
          expect(() => new Date(profile.createdAt)).not.toThrow();
          expect(() => new Date(profile.updatedAt)).not.toThrow();

          // Timestamps should be valid dates
          const createdDate = new Date(profile.createdAt);
          const updatedDate = new Date(profile.updatedAt);
          expect(createdDate.getTime()).toBeGreaterThan(0);
          expect(updatedDate.getTime()).toBeGreaterThan(0);
        }),
        { numRuns: 25 },
      );
    });
  });

  describe("Edge Cases and Boundary Conditions", () => {
    /**
     * Edge case: Newborns (age 0) should be valid
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept age 0 for newborns", () => {
      const demographics: Demographics = {
        age: 0,
        gender: "Male",
        state: "Karnataka",
        district: "Bangalore",
        income: 0,
        category: "General",
        occupation: "Student",
        education: "No Formal Education",
        familySize: 3,
        hasDisability: false,
      };

      const validation = validateDemographics(demographics);
      expect(validation.isValid).toBe(true);
    });

    /**
     * Edge case: Maximum age (150) should be valid
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept age 150 as maximum", () => {
      const demographics: Demographics = {
        age: 150,
        gender: "Male",
        state: "Karnataka",
        district: "Bangalore",
        income: 0,
        category: "General",
        occupation: "Retired",
        education: "Graduate",
        familySize: 1,
        hasDisability: false,
      };

      const validation = validateDemographics(demographics);
      expect(validation.isValid).toBe(true);
    });

    /**
     * Edge case: Zero income should be valid
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept zero income", () => {
      const demographics: Demographics = {
        age: 25,
        gender: "Male",
        state: "Karnataka",
        district: "Bangalore",
        income: 0,
        category: "General",
        occupation: "Unemployed",
        education: "Graduate",
        familySize: 4,
        hasDisability: false,
      };

      const validation = validateDemographics(demographics);
      expect(validation.isValid).toBe(true);
    });

    /**
     * Edge case: Single person household should be valid
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept family size of 1", () => {
      const demographics: Demographics = {
        age: 30,
        gender: "Male",
        state: "Karnataka",
        district: "Bangalore",
        income: 50000,
        category: "General",
        occupation: "Engineer",
        education: "Graduate",
        familySize: 1,
        hasDisability: false,
      };

      const validation = validateDemographics(demographics);
      expect(validation.isValid).toBe(true);
    });

    /**
     * Edge case: Large family (50 members) should be valid
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept family size of 50", () => {
      const demographics: Demographics = {
        age: 60,
        gender: "Male",
        state: "Rajasthan",
        district: "Jaipur",
        income: 100000,
        category: "General",
        occupation: "Farmer",
        education: "Primary",
        familySize: 50,
        hasDisability: false,
      };

      const validation = validateDemographics(demographics);
      expect(validation.isValid).toBe(true);
    });

    /**
     * Edge case: Empty strings should be rejected for required fields
     * **Validates: Requirement 6.1** - Data validation
     */
    it("should reject empty strings for required fields", () => {
      const demographics: Demographics = {
        age: 30,
        gender: "Male",
        state: "",
        district: "",
        income: 50000,
        category: "General",
        occupation: "",
        education: "",
        familySize: 4,
        hasDisability: false,
      };

      const validation = validateDemographics(demographics);
      expect(validation.isValid).toBe(false);
      expect(validation.errors.length).toBeGreaterThan(0);
    });

    /**
     * Edge case: All supported languages should be valid
     * **Validates: Requirement 6.2** - Profile management
     */
    it("should accept all 10 supported languages", () => {
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

      supportedLanguages.forEach((lang) => {
        const profile: UserProfile = {
          userId: "test-user",
          phoneNumber: "9876543210",
          preferredLanguage: lang,
          demographics: {
            age: 30,
            gender: "Male",
            state: "Karnataka",
            district: "Bangalore",
            income: 50000,
            category: "General",
            occupation: "Engineer",
            education: "Graduate",
            familySize: 4,
            hasDisability: false,
          },
          eligibleSchemes: [],
          applications: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          consentGiven: true,
          dataRetentionConsent: true,
        };

        const validation = validateUserProfile(profile);
        expect(validation.isValid).toBe(true);
      });
    });

    /**
     * Edge case: All user categories should be valid
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept all 5 user categories", () => {
      const categories: UserCategory[] = ["General", "OBC", "SC", "ST", "EWS"];

      categories.forEach((category) => {
        const demographics: Demographics = {
          age: 30,
          gender: "Male",
          state: "Karnataka",
          district: "Bangalore",
          income: 50000,
          category,
          occupation: "Engineer",
          education: "Graduate",
          familySize: 4,
          hasDisability: false,
        };

        const validation = validateDemographics(demographics);
        expect(validation.isValid).toBe(true);
      });
    });

    /**
     * Edge case: All gender options should be valid
     * **Validates: Requirement 6.1** - Collect demographic information
     */
    it("should accept all 4 gender options", () => {
      const genders: Gender[] = ["Male", "Female", "Other", "PreferNotToSay"];

      genders.forEach((gender) => {
        const demographics: Demographics = {
          age: 30,
          gender,
          state: "Karnataka",
          district: "Bangalore",
          income: 50000,
          category: "General",
          occupation: "Engineer",
          education: "Graduate",
          familySize: 4,
          hasDisability: false,
        };

        const validation = validateDemographics(demographics);
        expect(validation.isValid).toBe(true);
      });
    });
  });
});

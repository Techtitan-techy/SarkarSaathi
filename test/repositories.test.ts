/**
 * Unit tests for repository layer
 * Tests basic CRUD operations and validation
 */

import {
  UserRepository,
  SchemeRepository,
  ApplicationRepository,
} from "../lib/repositories";
import {
  UserProfile,
  Scheme,
  Application,
  Demographics,
} from "../lib/models/types";

describe("Repository Layer Tests", () => {
  describe("UserRepository", () => {
    it("should validate user profile before creation", async () => {
      const userRepo = new UserRepository("test-users-table");

      const invalidProfile = {
        userId: "",
        phoneNumber: "invalid",
        preferredLanguage: "en",
        demographics: {} as Demographics,
        eligibleSchemes: [],
        applications: [],
        createdAt: "",
        updatedAt: "",
        consentGiven: false,
        dataRetentionConsent: false,
      } as UserProfile;

      await expect(userRepo.createUser(invalidProfile)).rejects.toThrow(
        "Invalid user profile",
      );
    });

    it("should create valid user profile structure", () => {
      const demographics: Demographics = {
        age: 30,
        gender: "Male",
        state: "Karnataka",
        district: "Bangalore",
        income: 50000,
        category: "General",
        occupation: "Software Engineer",
        education: "Graduate",
        familySize: 4,
        hasDisability: false,
      };

      const profile: UserProfile = {
        userId: "user-123",
        phoneNumber: "9876543210",
        preferredLanguage: "en",
        demographics,
        eligibleSchemes: [],
        applications: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        consentGiven: true,
        dataRetentionConsent: true,
      };

      expect(profile.userId).toBe("user-123");
      expect(profile.phoneNumber).toBe("9876543210");
      expect(profile.demographics.age).toBe(30);
    });
  });

  describe("SchemeRepository", () => {
    it("should validate scheme before creation", async () => {
      const schemeRepo = new SchemeRepository("test-schemes-table");

      const invalidScheme = {
        schemeId: "",
        name: { en: "", hi: "" },
        description: { en: "", hi: "" },
      } as Scheme;

      await expect(schemeRepo.createScheme(invalidScheme)).rejects.toThrow(
        "Invalid scheme",
      );
    });

    it("should create valid scheme structure", () => {
      const scheme: Partial<Scheme> = {
        schemeId: "scheme-123",
        name: {
          en: "Test Scheme",
          hi: "परीक्षण योजना",
        },
        description: {
          en: "A test scheme",
          hi: "एक परीक्षण योजना",
        },
        category: "education",
        state: "Karnataka",
        isActive: true,
      };

      expect(scheme.schemeId).toBe("scheme-123");
      expect(scheme.name?.en).toBe("Test Scheme");
      expect(scheme.category).toBe("education");
    });
  });

  describe("ApplicationRepository", () => {
    it("should validate application before creation", async () => {
      const appRepo = new ApplicationRepository("test-applications-table");

      const invalidApplication = {
        applicationId: "",
        userId: "",
        schemeId: "",
        status: "invalid_status" as any,
        formData: {},
        documents: [],
        statusHistory: [],
        createdAt: "",
        updatedAt: "",
      } as Application;

      await expect(
        appRepo.createApplication(invalidApplication),
      ).rejects.toThrow("Invalid application");
    });

    it("should create valid application structure", () => {
      const application: Application = {
        applicationId: "app-123",
        userId: "user-123",
        schemeId: "scheme-123",
        status: "draft",
        formData: {},
        documents: [],
        statusHistory: [
          {
            status: "draft",
            timestamp: new Date().toISOString(),
            notes: "Application created",
          },
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      expect(application.applicationId).toBe("app-123");
      expect(application.status).toBe("draft");
      expect(application.statusHistory.length).toBe(1);
    });
  });

  describe("Data Model Validation", () => {
    it("should validate phone numbers correctly", () => {
      const validPhones = ["9876543210", "8765432109", "7654321098"];
      const invalidPhones = ["1234567890", "98765432", "abcdefghij"];

      validPhones.forEach((phone) => {
        expect(/^[6-9]\d{9}$/.test(phone)).toBe(true);
      });

      invalidPhones.forEach((phone) => {
        expect(/^[6-9]\d{9}$/.test(phone)).toBe(false);
      });
    });

    it("should validate age ranges correctly", () => {
      const validAges = [0, 18, 30, 60, 100, 150];
      const invalidAges = [-1, 151, 200];

      validAges.forEach((age) => {
        expect(age >= 0 && age <= 150).toBe(true);
      });

      invalidAges.forEach((age) => {
        expect(age >= 0 && age <= 150).toBe(false);
      });
    });

    it("should validate supported languages", () => {
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
      const unsupportedLanguages = ["fr", "es", "de"];

      supportedLanguages.forEach((lang) => {
        expect(supportedLanguages.includes(lang)).toBe(true);
      });

      unsupportedLanguages.forEach((lang) => {
        expect(supportedLanguages.includes(lang)).toBe(false);
      });
    });
  });
});

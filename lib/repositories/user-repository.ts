/**
 * User repository for managing user profiles
 * Provides CRUD operations and profile updates
 */

import { BaseRepository } from "./base-repository";
import { UserProfile, Demographics } from "../models/types";
import { validateUserProfile } from "../models/validators";

export class UserRepository extends BaseRepository {
  constructor(tableName: string, region?: string) {
    super(tableName, region);
  }

  /**
   * Create a new user profile
   */
  async createUser(profile: UserProfile): Promise<UserProfile> {
    // Validate profile
    const validation = validateUserProfile(profile);
    if (!validation.isValid) {
      throw new Error(`Invalid user profile: ${validation.errors.join(", ")}`);
    }

    // Set timestamps
    const now = new Date().toISOString();
    const userWithTimestamps: UserProfile = {
      ...profile,
      createdAt: now,
      updatedAt: now,
      lastLoginAt: now,
    };

    await this.putItem(userWithTimestamps);
    return userWithTimestamps;
  }

  /**
   * Get user by ID
   */
  async getUserById(userId: string): Promise<UserProfile | null> {
    return this.getItem<UserProfile>({ userId });
  }

  /**
   * Get user by phone number
   */
  async getUserByPhoneNumber(phoneNumber: string): Promise<UserProfile | null> {
    const results = await this.queryItems<UserProfile>(
      "#phoneNumber = :phoneNumber",
      { "#phoneNumber": "phoneNumber" },
      { ":phoneNumber": phoneNumber },
      "phoneNumber-index",
      undefined,
      1,
    );

    return results.length > 0 ? results[0] : null;
  }

  /**
   * Update user profile
   */
  async updateUser(
    userId: string,
    updates: Partial<UserProfile>,
  ): Promise<void> {
    // Don't allow updating userId, createdAt, or phoneNumber
    const {
      userId: _,
      createdAt: __,
      phoneNumber: ___,
      ...allowedUpdates
    } = updates as any;

    // Build update expression
    const updateExpressions: string[] = [];
    const expressionAttributeNames: Record<string, string> = {};
    const expressionAttributeValues: Record<string, any> = {};

    // Always update the updatedAt timestamp
    updateExpressions.push("#updatedAt = :updatedAt");
    expressionAttributeNames["#updatedAt"] = "updatedAt";
    expressionAttributeValues[":updatedAt"] = new Date().toISOString();

    // Add other updates
    Object.keys(allowedUpdates).forEach((key, index) => {
      const attrName = `#attr${index}`;
      const attrValue = `:val${index}`;
      updateExpressions.push(`${attrName} = ${attrValue}`);
      expressionAttributeNames[attrName] = key;
      expressionAttributeValues[attrValue] = (allowedUpdates as any)[key];
    });

    if (updateExpressions.length === 0) {
      return; // Nothing to update
    }

    await this.updateItem(
      { userId },
      `SET ${updateExpressions.join(", ")}`,
      expressionAttributeNames,
      expressionAttributeValues,
    );
  }

  /**
   * Update user demographics
   */
  async updateDemographics(
    userId: string,
    demographics: Demographics,
  ): Promise<void> {
    await this.updateUser(userId, { demographics });
  }

  /**
   * Update preferred language
   */
  async updatePreferredLanguage(
    userId: string,
    language: string,
  ): Promise<void> {
    await this.updateItem(
      { userId },
      "SET #preferredLanguage = :language, #updatedAt = :updatedAt",
      {
        "#preferredLanguage": "preferredLanguage",
        "#updatedAt": "updatedAt",
      },
      {
        ":language": language,
        ":updatedAt": new Date().toISOString(),
      },
    );
  }

  /**
   * Add eligible scheme to user profile
   */
  async addEligibleScheme(userId: string, schemeId: string): Promise<void> {
    // Get current user to update eligibleSchemes array
    const user = await this.getUserById(userId);
    if (!user) {
      throw new Error(`User ${userId} not found`);
    }

    const updatedSchemes = [...user.eligibleSchemes, schemeId];

    await this.updateItem(
      { userId },
      "SET #eligibleSchemes = :schemes, #updatedAt = :updatedAt",
      {
        "#eligibleSchemes": "eligibleSchemes",
        "#updatedAt": "updatedAt",
      },
      {
        ":schemes": updatedSchemes,
        ":updatedAt": new Date().toISOString(),
      },
    );
  }

  /**
   * Update last login timestamp
   */
  async updateLastLogin(userId: string): Promise<void> {
    const now = new Date().toISOString();
    await this.updateItem(
      { userId },
      "SET #lastLoginAt = :now, #updatedAt = :now",
      {
        "#lastLoginAt": "lastLoginAt",
        "#updatedAt": "updatedAt",
      },
      {
        ":now": now,
      },
    );
  }

  /**
   * Delete user profile (for GDPR compliance)
   */
  async deleteUser(userId: string): Promise<void> {
    await this.deleteItem({ userId });
  }

  /**
   * Check if user exists
   */
  async userExists(userId: string): Promise<boolean> {
    const user = await this.getUserById(userId);
    return user !== null;
  }

  /**
   * Check if phone number is already registered
   */
  async phoneNumberExists(phoneNumber: string): Promise<boolean> {
    const user = await this.getUserByPhoneNumber(phoneNumber);
    return user !== null;
  }
}

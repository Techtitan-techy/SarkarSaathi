/**
 * Scheme repository for managing government schemes
 * Provides filtering and search capabilities
 */

import { BaseRepository } from "./base-repository";
import { Scheme, SchemeCategory, Demographics } from "../models/types";
import { validateScheme, validateEligibility } from "../models/validators";

/**
 * Scheme filter options
 */
export interface SchemeFilter {
  category?: SchemeCategory;
  state?: string;
  isActive?: boolean;
  minBenefitAmount?: number;
  maxBenefitAmount?: number;
}

export class SchemeRepository extends BaseRepository {
  constructor(tableName: string, region?: string) {
    super(tableName, region);
  }

  /**
   * Create a new scheme
   */
  async createScheme(scheme: Scheme): Promise<Scheme> {
    // Validate scheme
    const validation = validateScheme(scheme);
    if (!validation.isValid) {
      throw new Error(`Invalid scheme: ${validation.errors.join(", ")}`);
    }

    // Set timestamps
    const now = new Date().toISOString();
    const schemeWithTimestamps: Scheme = {
      ...scheme,
      createdAt: now,
      updatedAt: now,
    };

    await this.putItem(schemeWithTimestamps);
    return schemeWithTimestamps;
  }

  /**
   * Get scheme by ID
   */
  async getSchemeById(schemeId: string): Promise<Scheme | null> {
    return this.getItem<Scheme>({ schemeId });
  }

  /**
   * Get schemes by category
   */
  async getSchemesByCategory(
    category: SchemeCategory,
    limit?: number,
  ): Promise<Scheme[]> {
    return this.queryItems<Scheme>(
      "#category = :category",
      { "#category": "category" },
      { ":category": category },
      "category-index",
      undefined,
      limit,
    );
  }

  /**
   * Get schemes by state
   */
  async getSchemesByState(state: string, limit?: number): Promise<Scheme[]> {
    return this.queryItems<Scheme>(
      "#state = :state",
      { "#state": "state" },
      { ":state": state },
      "state-index",
      undefined,
      limit,
    );
  }

  /**
   * Get active schemes
   */
  async getActiveSchemes(limit?: number): Promise<Scheme[]> {
    return this.scanItems<Scheme>(
      "#isActive = :isActive",
      { "#isActive": "isActive" },
      { ":isActive": true },
      limit,
    );
  }

  /**
   * Search schemes with filters
   */
  async searchSchemes(filter: SchemeFilter, limit?: number): Promise<Scheme[]> {
    let schemes: Scheme[] = [];

    // Use appropriate index based on filter
    if (filter.category) {
      schemes = await this.getSchemesByCategory(filter.category, limit);
    } else if (filter.state) {
      schemes = await this.getSchemesByState(filter.state, limit);
    } else {
      schemes = await this.getActiveSchemes(limit);
    }

    // Apply additional filters in memory
    return schemes.filter((scheme) => {
      // Active filter
      if (
        filter.isActive !== undefined &&
        scheme.isActive !== filter.isActive
      ) {
        return false;
      }

      // State filter (if not already filtered by index)
      if (filter.state && !filter.state && scheme.state !== filter.state) {
        return false;
      }

      // Category filter (if not already filtered by index)
      if (
        filter.category &&
        !filter.category &&
        scheme.category !== filter.category
      ) {
        return false;
      }

      // Benefit amount filters
      if (
        filter.minBenefitAmount !== undefined ||
        filter.maxBenefitAmount !== undefined
      ) {
        const financialBenefits = scheme.benefits.filter(
          (b) => b.type === "financial" && b.amount,
        );
        if (financialBenefits.length === 0) {
          return false;
        }

        const maxBenefit = Math.max(
          ...financialBenefits.map((b) => b.amount || 0),
        );

        if (
          filter.minBenefitAmount !== undefined &&
          maxBenefit < filter.minBenefitAmount
        ) {
          return false;
        }

        if (
          filter.maxBenefitAmount !== undefined &&
          maxBenefit > filter.maxBenefitAmount
        ) {
          return false;
        }
      }

      return true;
    });
  }

  /**
   * Find eligible schemes for user demographics
   */
  async findEligibleSchemes(
    demographics: Demographics,
    limit?: number,
  ): Promise<Scheme[]> {
    // Get schemes for user's state
    const schemes = await this.getSchemesByState(demographics.state, limit);

    // Filter by eligibility
    const eligibleSchemes: Scheme[] = [];

    for (const scheme of schemes) {
      if (!scheme.isActive) {
        continue;
      }

      const eligibilityCheck = validateEligibility(demographics, scheme);
      if (eligibilityCheck.isValid) {
        eligibleSchemes.push(scheme);
      }
    }

    // Sort by benefit amount (descending)
    return eligibleSchemes.sort((a, b) => {
      const aMaxBenefit = this.getMaxBenefitAmount(a);
      const bMaxBenefit = this.getMaxBenefitAmount(b);
      return bMaxBenefit - aMaxBenefit;
    });
  }

  /**
   * Get maximum benefit amount from scheme
   */
  private getMaxBenefitAmount(scheme: Scheme): number {
    const financialBenefits = scheme.benefits.filter(
      (b) => b.type === "financial" && b.amount,
    );

    if (financialBenefits.length === 0) {
      return 0;
    }

    return Math.max(...financialBenefits.map((b) => b.amount || 0));
  }

  /**
   * Update scheme
   */
  async updateScheme(
    schemeId: string,
    updates: Partial<Scheme>,
  ): Promise<void> {
    // Don't allow updating schemeId or createdAt
    const { schemeId: _, createdAt: __, ...allowedUpdates } = updates as any;

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
      { schemeId },
      `SET ${updateExpressions.join(", ")}`,
      expressionAttributeNames,
      expressionAttributeValues,
    );
  }

  /**
   * Deactivate scheme
   */
  async deactivateScheme(schemeId: string): Promise<void> {
    await this.updateItem(
      { schemeId },
      "SET #isActive = :isActive, #updatedAt = :updatedAt",
      {
        "#isActive": "isActive",
        "#updatedAt": "updatedAt",
      },
      {
        ":isActive": false,
        ":updatedAt": new Date().toISOString(),
      },
    );
  }

  /**
   * Activate scheme
   */
  async activateScheme(schemeId: string): Promise<void> {
    await this.updateItem(
      { schemeId },
      "SET #isActive = :isActive, #updatedAt = :updatedAt",
      {
        "#isActive": "isActive",
        "#updatedAt": "updatedAt",
      },
      {
        ":isActive": true,
        ":updatedAt": new Date().toISOString(),
      },
    );
  }

  /**
   * Delete scheme
   */
  async deleteScheme(schemeId: string): Promise<void> {
    await this.deleteItem({ schemeId });
  }

  /**
   * Check if scheme exists
   */
  async schemeExists(schemeId: string): Promise<boolean> {
    const scheme = await this.getSchemeById(schemeId);
    return scheme !== null;
  }

  /**
   * Get all categories with scheme counts
   */
  async getCategoryCounts(): Promise<Record<SchemeCategory, number>> {
    const schemes = await this.getActiveSchemes();

    const counts: Record<string, number> = {};
    schemes.forEach((scheme) => {
      counts[scheme.category] = (counts[scheme.category] || 0) + 1;
    });

    return counts as Record<SchemeCategory, number>;
  }
}

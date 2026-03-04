/**
 * Application repository for managing scheme applications
 * Provides status tracking and application management
 */

import { BaseRepository } from "./base-repository";
import {
  Application,
  ApplicationStatus,
  StatusHistoryEntry,
} from "../models/types";
import { validateApplication } from "../models/validators";

export class ApplicationRepository extends BaseRepository {
  constructor(tableName: string, region?: string) {
    super(tableName, region);
  }

  /**
   * Create a new application
   */
  async createApplication(application: Application): Promise<Application> {
    // Validate application
    const validation = validateApplication(application);
    if (!validation.isValid) {
      throw new Error(`Invalid application: ${validation.errors.join(", ")}`);
    }

    // Set timestamps
    const now = new Date().toISOString();
    const applicationWithTimestamps: Application = {
      ...application,
      createdAt: now,
      updatedAt: now,
      statusHistory: [
        {
          status: application.status,
          timestamp: now,
          notes: "Application created",
        },
      ],
    };

    await this.putItem(applicationWithTimestamps);
    return applicationWithTimestamps;
  }

  /**
   * Get application by ID
   */
  async getApplicationById(applicationId: string): Promise<Application | null> {
    return this.getItem<Application>({ applicationId });
  }

  /**
   * Get applications by user ID
   */
  async getApplicationsByUserId(
    userId: string,
    limit?: number,
  ): Promise<Application[]> {
    return this.queryItems<Application>(
      "#userId = :userId",
      { "#userId": "userId" },
      { ":userId": userId },
      "userId-index",
      undefined,
      limit,
    );
  }

  /**
   * Get applications by status
   */
  async getApplicationsByStatus(
    status: ApplicationStatus,
    limit?: number,
  ): Promise<Application[]> {
    return this.queryItems<Application>(
      "#status = :status",
      { "#status": "status" },
      { ":status": status },
      "status-index",
      undefined,
      limit,
    );
  }

  /**
   * Get user's applications for a specific scheme
   */
  async getUserSchemeApplications(
    userId: string,
    schemeId: string,
  ): Promise<Application[]> {
    const applications = await this.getApplicationsByUserId(userId);
    return applications.filter((app) => app.schemeId === schemeId);
  }

  /**
   * Update application status
   */
  async updateApplicationStatus(
    applicationId: string,
    newStatus: ApplicationStatus,
    notes?: string,
    updatedBy?: string,
  ): Promise<void> {
    const now = new Date().toISOString();

    // Create status history entry
    const historyEntry: StatusHistoryEntry = {
      status: newStatus,
      timestamp: now,
      notes,
      updatedBy,
    };

    // Update status and add to history
    await this.updateItem(
      { applicationId },
      "SET #status = :status, #updatedAt = :updatedAt, #statusHistory = list_append(#statusHistory, :historyEntry)",
      {
        "#status": "status",
        "#updatedAt": "updatedAt",
        "#statusHistory": "statusHistory",
      },
      {
        ":status": newStatus,
        ":updatedAt": now,
        ":historyEntry": [historyEntry],
      },
    );
  }

  /**
   * Update application form data
   */
  async updateFormData(
    applicationId: string,
    formData: Record<string, any>,
  ): Promise<void> {
    await this.updateItem(
      { applicationId },
      "SET #formData = :formData, #updatedAt = :updatedAt",
      {
        "#formData": "formData",
        "#updatedAt": "updatedAt",
      },
      {
        ":formData": formData,
        ":updatedAt": new Date().toISOString(),
      },
    );
  }

  /**
   * Add document to application
   */
  async addDocument(
    applicationId: string,
    document: {
      documentId: string;
      fileName: string;
      s3Key: string;
      fileSize: number;
      mimeType: string;
    },
  ): Promise<void> {
    const now = new Date().toISOString();
    const documentReference = {
      ...document,
      uploadedAt: now,
      verified: false,
    };

    await this.updateItem(
      { applicationId },
      "SET #documents = list_append(if_not_exists(#documents, :emptyList), :document), #updatedAt = :updatedAt",
      {
        "#documents": "documents",
        "#updatedAt": "updatedAt",
      },
      {
        ":document": [documentReference],
        ":emptyList": [],
        ":updatedAt": now,
      },
    );
  }

  /**
   * Submit application
   */
  async submitApplication(
    applicationId: string,
    trackingNumber?: string,
  ): Promise<void> {
    const now = new Date().toISOString();

    const updateExpression = trackingNumber
      ? "SET #status = :status, #submittedAt = :submittedAt, #trackingNumber = :trackingNumber, #updatedAt = :updatedAt, #statusHistory = list_append(#statusHistory, :historyEntry)"
      : "SET #status = :status, #submittedAt = :submittedAt, #updatedAt = :updatedAt, #statusHistory = list_append(#statusHistory, :historyEntry)";

    const expressionAttributeNames: Record<string, string> = {
      "#status": "status",
      "#submittedAt": "submittedAt",
      "#updatedAt": "updatedAt",
      "#statusHistory": "statusHistory",
    };

    const expressionAttributeValues: Record<string, any> = {
      ":status": "submitted",
      ":submittedAt": now,
      ":updatedAt": now,
      ":historyEntry": [
        {
          status: "submitted",
          timestamp: now,
          notes: "Application submitted",
        },
      ],
    };

    if (trackingNumber) {
      expressionAttributeNames["#trackingNumber"] = "trackingNumber";
      expressionAttributeValues[":trackingNumber"] = trackingNumber;
    }

    await this.updateItem(
      { applicationId },
      updateExpression,
      expressionAttributeNames,
      expressionAttributeValues,
    );
  }

  /**
   * Add notes to application
   */
  async addNotes(applicationId: string, notes: string): Promise<void> {
    await this.updateItem(
      { applicationId },
      "SET #notes = :notes, #updatedAt = :updatedAt",
      {
        "#notes": "notes",
        "#updatedAt": "updatedAt",
      },
      {
        ":notes": notes,
        ":updatedAt": new Date().toISOString(),
      },
    );
  }

  /**
   * Delete application
   */
  async deleteApplication(applicationId: string): Promise<void> {
    await this.deleteItem({ applicationId });
  }

  /**
   * Check if application exists
   */
  async applicationExists(applicationId: string): Promise<boolean> {
    const application = await this.getApplicationById(applicationId);
    return application !== null;
  }

  /**
   * Get application statistics for a user
   */
  async getUserApplicationStats(userId: string): Promise<{
    total: number;
    byStatus: Record<ApplicationStatus, number>;
  }> {
    const applications = await this.getApplicationsByUserId(userId);

    const stats = {
      total: applications.length,
      byStatus: {} as Record<ApplicationStatus, number>,
    };

    applications.forEach((app) => {
      stats.byStatus[app.status] = (stats.byStatus[app.status] || 0) + 1;
    });

    return stats;
  }

  /**
   * Check if user has pending application for scheme
   */
  async hasPendingApplication(
    userId: string,
    schemeId: string,
  ): Promise<boolean> {
    const applications = await this.getUserSchemeApplications(userId, schemeId);

    return applications.some(
      (app) =>
        app.status === "draft" ||
        app.status === "in_progress" ||
        app.status === "submitted" ||
        app.status === "under_review",
    );
  }
}

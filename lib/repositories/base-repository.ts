/**
 * Base repository class with common DynamoDB operations
 * Provides error handling and retry logic with exponential backoff
 */

import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  GetCommand,
  PutCommand,
  UpdateCommand,
  DeleteCommand,
  QueryCommand,
  ScanCommand,
} from "@aws-sdk/lib-dynamodb";

/**
 * Retry configuration
 */
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

/**
 * Default retry configuration with exponential backoff
 */
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 100,
  maxDelayMs: 5000,
};

/**
 * Base repository class
 */
export abstract class BaseRepository {
  protected readonly docClient: DynamoDBDocumentClient;
  protected readonly tableName: string;
  protected readonly retryConfig: RetryConfig;

  constructor(tableName: string, region: string = "ap-south-1") {
    const client = new DynamoDBClient({ region });
    this.docClient = DynamoDBDocumentClient.from(client, {
      marshallOptions: {
        removeUndefinedValues: true,
        convertClassInstanceToMap: true,
      },
    });
    this.tableName = tableName;
    this.retryConfig = DEFAULT_RETRY_CONFIG;
  }

  /**
   * Execute operation with retry logic and exponential backoff
   */
  protected async executeWithRetry<T>(
    operation: () => Promise<T>,
    operationName: string,
  ): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;

        // Check if error is retryable
        if (!this.isRetryableError(error)) {
          throw this.wrapError(error, operationName);
        }

        // Don't retry on last attempt
        if (attempt === this.retryConfig.maxRetries) {
          break;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
          this.retryConfig.baseDelayMs * Math.pow(2, attempt),
          this.retryConfig.maxDelayMs,
        );

        console.warn(
          `Retry attempt ${attempt + 1}/${this.retryConfig.maxRetries} for ${operationName} after ${delay}ms`,
          { error: (error as Error).message },
        );

        await this.sleep(delay);
      }
    }

    throw this.wrapError(lastError!, operationName);
  }

  /**
   * Check if error is retryable
   */
  protected isRetryableError(error: any): boolean {
    const retryableErrors = [
      "ProvisionedThroughputExceededException",
      "ThrottlingException",
      "RequestLimitExceeded",
      "InternalServerError",
      "ServiceUnavailable",
    ];

    return retryableErrors.some(
      (retryableError) =>
        error.name === retryableError || error.code === retryableError,
    );
  }

  /**
   * Wrap error with context
   */
  protected wrapError(error: any, operation: string): Error {
    const message = `DynamoDB ${operation} failed: ${error.message || error}`;
    const wrappedError = new Error(message);
    wrappedError.name = error.name || "DynamoDBError";
    (wrappedError as any).originalError = error;
    return wrappedError;
  }

  /**
   * Sleep utility for retry delays
   */
  protected sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get item by primary key
   */
  protected async getItem<T>(key: Record<string, any>): Promise<T | null> {
    return this.executeWithRetry(async () => {
      const result = await this.docClient.send(
        new GetCommand({
          TableName: this.tableName,
          Key: key,
        }),
      );
      return (result.Item as T) || null;
    }, "GetItem");
  }

  /**
   * Put item (create or replace)
   */
  protected async putItem<T>(item: T): Promise<void> {
    return this.executeWithRetry(async () => {
      await this.docClient.send(
        new PutCommand({
          TableName: this.tableName,
          Item: item as Record<string, any>,
        }),
      );
    }, "PutItem");
  }

  /**
   * Update item with expression
   */
  protected async updateItem(
    key: Record<string, any>,
    updateExpression: string,
    expressionAttributeNames: Record<string, string>,
    expressionAttributeValues: Record<string, any>,
  ): Promise<void> {
    return this.executeWithRetry(async () => {
      await this.docClient.send(
        new UpdateCommand({
          TableName: this.tableName,
          Key: key,
          UpdateExpression: updateExpression,
          ExpressionAttributeNames: expressionAttributeNames,
          ExpressionAttributeValues: expressionAttributeValues,
        }),
      );
    }, "UpdateItem");
  }

  /**
   * Delete item by primary key
   */
  protected async deleteItem(key: Record<string, any>): Promise<void> {
    return this.executeWithRetry(async () => {
      await this.docClient.send(
        new DeleteCommand({
          TableName: this.tableName,
          Key: key,
        }),
      );
    }, "DeleteItem");
  }

  /**
   * Query items with optional filters
   */
  protected async queryItems<T>(
    keyConditionExpression: string,
    expressionAttributeNames: Record<string, string>,
    expressionAttributeValues: Record<string, any>,
    indexName?: string,
    filterExpression?: string,
    limit?: number,
  ): Promise<T[]> {
    return this.executeWithRetry(async () => {
      const result = await this.docClient.send(
        new QueryCommand({
          TableName: this.tableName,
          IndexName: indexName,
          KeyConditionExpression: keyConditionExpression,
          ExpressionAttributeNames: expressionAttributeNames,
          ExpressionAttributeValues: expressionAttributeValues,
          FilterExpression: filterExpression,
          Limit: limit,
        }),
      );
      return (result.Items as T[]) || [];
    }, "Query");
  }

  /**
   * Scan table with optional filters (use sparingly)
   */
  protected async scanItems<T>(
    filterExpression?: string,
    expressionAttributeNames?: Record<string, string>,
    expressionAttributeValues?: Record<string, any>,
    limit?: number,
  ): Promise<T[]> {
    return this.executeWithRetry(async () => {
      const result = await this.docClient.send(
        new ScanCommand({
          TableName: this.tableName,
          FilterExpression: filterExpression,
          ExpressionAttributeNames: expressionAttributeNames,
          ExpressionAttributeValues: expressionAttributeValues,
          Limit: limit,
        }),
      );
      return (result.Items as T[]) || [];
    }, "Scan");
  }
}

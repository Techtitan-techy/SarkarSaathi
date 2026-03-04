/**
 * Configuration management for SarkariSaathi
 * Handles environment variables and AWS Systems Manager Parameter Store integration
 */

export interface SarkariSaathiConfig {
  // AWS Configuration
  region: string;
  account: string;

  // DynamoDB Tables
  usersTable: string;
  applicationsTable: string;
  schemesTable: string;
  sessionsTable: string;

  // S3 Buckets
  audioBucket: string;
  schemeDocsBucket: string;
  ttsCacheBucket: string;

  // KMS
  kmsKeyId: string;

  // API Configuration
  bhashiniApiKey?: string;
  bhashiniApiUrl?: string;

  // Feature Flags
  enableBhashini: boolean;
  enableOfflineMode: boolean;
  enableDebugLogging: boolean;

  // Performance Settings
  maxConcurrentRequests: number;
  requestTimeoutMs: number;
  cacheExpirationSeconds: number;
}

/**
 * Load configuration from environment variables
 */
export function loadConfig(): SarkariSaathiConfig {
  return {
    region: process.env.AWS_REGION || "ap-south-1",
    account: process.env.CDK_DEFAULT_ACCOUNT || "",

    usersTable: process.env.USERS_TABLE || "",
    applicationsTable: process.env.APPLICATIONS_TABLE || "",
    schemesTable: process.env.SCHEMES_TABLE || "",
    sessionsTable: process.env.SESSIONS_TABLE || "",

    audioBucket: process.env.AUDIO_BUCKET || "",
    schemeDocsBucket: process.env.SCHEME_DOCS_BUCKET || "",
    ttsCacheBucket: process.env.TTS_CACHE_BUCKET || "",

    kmsKeyId: process.env.KMS_KEY_ID || "",

    bhashiniApiKey: process.env.BHASHINI_API_KEY,
    bhashiniApiUrl:
      process.env.BHASHINI_API_URL || "https://dhruva-api.bhashini.gov.in",

    enableBhashini: process.env.ENABLE_BHASHINI === "true",
    enableOfflineMode: process.env.ENABLE_OFFLINE_MODE === "true",
    enableDebugLogging: process.env.ENABLE_DEBUG_LOGGING === "true",

    maxConcurrentRequests: parseInt(
      process.env.MAX_CONCURRENT_REQUESTS || "100",
      10,
    ),
    requestTimeoutMs: parseInt(process.env.REQUEST_TIMEOUT_MS || "30000", 10),
    cacheExpirationSeconds: parseInt(
      process.env.CACHE_EXPIRATION_SECONDS || "3600",
      10,
    ),
  };
}

/**
 * Validate configuration to ensure all required values are present
 */
export function validateConfig(config: SarkariSaathiConfig): void {
  const requiredFields: (keyof SarkariSaathiConfig)[] = [
    "region",
    "usersTable",
    "applicationsTable",
    "schemesTable",
    "sessionsTable",
    "audioBucket",
    "schemeDocsBucket",
    "ttsCacheBucket",
    "kmsKeyId",
  ];

  const missingFields = requiredFields.filter(
    (field) => !config[field] || config[field] === "",
  );

  if (missingFields.length > 0) {
    throw new Error(
      `Missing required configuration fields: ${missingFields.join(", ")}`,
    );
  }
}

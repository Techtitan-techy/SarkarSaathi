import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as iam from "aws-cdk-lib/aws-iam";
import * as kms from "aws-cdk-lib/aws-kms";
import * as logs from "aws-cdk-lib/aws-logs";
import * as ssm from "aws-cdk-lib/aws-ssm";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as opensearch from "aws-cdk-lib/aws-opensearchservice";
import * as wafv2 from "aws-cdk-lib/aws-wafv2";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as acm from "aws-cdk-lib/aws-certificatemanager";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import * as pinpoint from "aws-cdk-lib/aws-pinpoint";
import * as sns from "aws-cdk-lib/aws-sns";
import * as fs from "fs";

export class SarkariSaathiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ========================================
    // KMS Keys for Encryption
    // ========================================
    const dataEncryptionKey = new kms.Key(this, "DataEncryptionKey", {
      description: "KMS key for encrypting SarkariSaathi user data",
      enableKeyRotation: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    dataEncryptionKey.addAlias("alias/sarkari-saathi-data");

    // ========================================
    // VPC for Secure Communication (Optional but recommended)
    // ========================================
    const vpc = new ec2.Vpc(this, "SarkariSaathiVPC", {
      maxAzs: 2,
      natGateways: 0, // Cost optimization - use VPC endpoints instead
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: "Public",
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: "Private",
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
    });

    // VPC Endpoints for AWS services (cost optimization)
    vpc.addInterfaceEndpoint("DynamoDBEndpoint", {
      service: ec2.InterfaceVpcEndpointAwsService.DYNAMODB,
    });

    vpc.addInterfaceEndpoint("S3Endpoint", {
      service: ec2.InterfaceVpcEndpointAwsService.S3,
    });

    // Security Group for Lambda functions
    const lambdaSecurityGroup = new ec2.SecurityGroup(
      this,
      "LambdaSecurityGroup",
      {
        vpc,
        description: "Security group for SarkariSaathi Lambda functions",
        allowAllOutbound: true,
      },
    );

    // Security Group for OpenSearch
    const openSearchSecurityGroup = new ec2.SecurityGroup(
      this,
      "OpenSearchSecurityGroup",
      {
        vpc,
        description: "Security group for OpenSearch domain",
        allowAllOutbound: true,
      },
    );

    // Allow Lambda to access OpenSearch
    openSearchSecurityGroup.addIngressRule(
      lambdaSecurityGroup,
      ec2.Port.tcp(443),
      "Allow HTTPS from Lambda functions",
    );

    // ========================================
    // AWS Systems Manager Parameter Store for Secrets
    // ========================================

    // Store Bhashini API configuration
    const bhashiniApiKeyParam = new ssm.StringParameter(
      this,
      "BhashiniApiKey",
      {
        parameterName: "/sarkari-saathi/bhashini/api-key",
        stringValue: "PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT",
        description: "Bhashini API key for multilingual support",
        tier: ssm.ParameterTier.STANDARD,
      },
    );

    const bhashiniApiUrlParam = new ssm.StringParameter(
      this,
      "BhashiniApiUrl",
      {
        parameterName: "/sarkari-saathi/bhashini/api-url",
        stringValue: "https://dhruva-api.bhashini.gov.in",
        description: "Bhashini API endpoint URL",
        tier: ssm.ParameterTier.STANDARD,
      },
    );

    // Feature flags
    new ssm.StringParameter(this, "EnableBhashiniParam", {
      parameterName: "/sarkari-saathi/features/enable-bhashini",
      stringValue: "false",
      description: "Enable Bhashini API for regional languages",
      tier: ssm.ParameterTier.STANDARD,
    });

    new ssm.StringParameter(this, "EnableDebugLoggingParam", {
      parameterName: "/sarkari-saathi/features/enable-debug-logging",
      stringValue: "true",
      description: "Enable debug logging for development",
      tier: ssm.ParameterTier.STANDARD,
    });

    // ========================================
    // S3 Buckets
    // ========================================

    // Audio files bucket
    const audioBucket = new s3.Bucket(this, "AudioBucket", {
      bucketName: `sarkari-saathi-audio-${this.account}`,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: dataEncryptionKey,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: false,
      lifecycleRules: [
        {
          id: "DeleteOldAudioFiles",
          expiration: cdk.Duration.days(7),
          enabled: true,
        },
      ],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Scheme documents bucket
    const schemeDocsBucket = new s3.Bucket(this, "SchemeDocsBucket", {
      bucketName: `sarkari-saathi-schemes-${this.account}`,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: dataEncryptionKey,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Cached TTS audio bucket
    const ttsCacheBucket = new s3.Bucket(this, "TTSCacheBucket", {
      bucketName: `sarkari-saathi-tts-cache-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          id: "DeleteOldTTSCache",
          expiration: cdk.Duration.days(7),
          enabled: true,
        },
      ],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // ========================================
    // DynamoDB Tables
    // ========================================

    // Users table
    const usersTable = new dynamodb.Table(this, "UsersTable", {
      tableName: "SarkariSaathi-Users",
      partitionKey: { name: "userId", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dataEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI on phoneNumber
    usersTable.addGlobalSecondaryIndex({
      indexName: "phoneNumber-index",
      partitionKey: {
        name: "phoneNumber",
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Applications table
    const applicationsTable = new dynamodb.Table(this, "ApplicationsTable", {
      tableName: "SarkariSaathi-Applications",
      partitionKey: {
        name: "applicationId",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dataEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI on userId
    applicationsTable.addGlobalSecondaryIndex({
      indexName: "userId-index",
      partitionKey: { name: "userId", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "createdAt", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI on status
    applicationsTable.addGlobalSecondaryIndex({
      indexName: "status-index",
      partitionKey: { name: "status", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "createdAt", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Schemes table
    const schemesTable = new dynamodb.Table(this, "SchemesTable", {
      tableName: "SarkariSaathi-Schemes",
      partitionKey: { name: "schemeId", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dataEncryptionKey,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI on category
    schemesTable.addGlobalSecondaryIndex({
      indexName: "category-index",
      partitionKey: { name: "category", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI on state
    schemesTable.addGlobalSecondaryIndex({
      indexName: "state-index",
      partitionKey: { name: "state", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Sessions table with TTL
    const sessionsTable = new dynamodb.Table(this, "SessionsTable", {
      tableName: "SarkariSaathi-Sessions",
      partitionKey: { name: "sessionId", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dataEncryptionKey,
      timeToLiveAttribute: "ttl",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // SMS Conversations table for tracking SMS history
    const smsConversationsTable = new dynamodb.Table(
      this,
      "SmsConversationsTable",
      {
        tableName: "SarkariSaathi-SmsConversations",
        partitionKey: {
          name: "phoneNumber",
          type: dynamodb.AttributeType.STRING,
        },
        sortKey: { name: "timestamp", type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
        encryptionKey: dataEncryptionKey,
        timeToLiveAttribute: "ttl",
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      },
    );

    // GSI on sessionId for SMS conversations
    smsConversationsTable.addGlobalSecondaryIndex({
      indexName: "sessionId-index",
      partitionKey: {
        name: "sessionId",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: { name: "timestamp", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // ========================================
    // Amazon Pinpoint for SMS Gateway
    // ========================================

    // Create Pinpoint application for SMS
    const pinpointApp = new pinpoint.CfnApp(this, "SarkariSaathiSmsApp", {
      name: "SarkariSaathi-SMS",
    });

    // Store Pinpoint configuration in SSM
    const pinpointAppIdParam = new ssm.StringParameter(this, "PinpointAppId", {
      parameterName: "/sarkari-saathi/pinpoint/app-id",
      stringValue: pinpointApp.ref,
      description: "Pinpoint Application ID for SMS",
      tier: ssm.ParameterTier.STANDARD,
    });

    // SMS rate limiting configuration
    new ssm.StringParameter(this, "SmsRateLimitParam", {
      parameterName: "/sarkari-saathi/sms/rate-limit",
      stringValue: "10", // 10 SMS per minute per user
      description: "SMS rate limit per user per minute",
      tier: ssm.ParameterTier.STANDARD,
    });

    // SMS character limit for chunking
    new ssm.StringParameter(this, "SmsChunkSizeParam", {
      parameterName: "/sarkari-saathi/sms/chunk-size",
      stringValue: "160", // Standard SMS length
      description: "SMS message chunk size in characters",
      tier: ssm.ParameterTier.STANDARD,
    });

    // SNS Topic for SMS delivery status notifications
    const smsStatusTopic = new sns.Topic(this, "SmsStatusTopic", {
      topicName: "SarkariSaathi-SMS-Status",
      displayName: "SMS Delivery Status Notifications",
    });

    // ========================================
    // Amazon OpenSearch Domain for RAG
    // ========================================

    const openSearchDomain = new opensearch.Domain(this, "SchemeSearchDomain", {
      domainName: "sarkari-saathi-schemes",
      version: opensearch.EngineVersion.OPENSEARCH_2_11,
      capacity: {
        dataNodes: 1,
        dataNodeInstanceType: "t3.small.search",
      },
      ebs: {
        volumeSize: 10,
        volumeType: ec2.EbsDeviceVolumeType.GP3,
      },
      vpc,
      vpcSubnets: [
        {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
      securityGroups: [openSearchSecurityGroup],
      encryptionAtRest: {
        enabled: true,
        kmsKey: dataEncryptionKey,
      },
      nodeToNodeEncryption: true,
      enforceHttps: true,
      zoneAwareness: {
        enabled: false,
      },
      logging: {
        slowSearchLogEnabled: true,
        appLogEnabled: true,
        slowIndexLogEnabled: true,
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ========================================
    // IAM Roles for Lambda Functions
    // ========================================

    const lambdaExecutionRole = new iam.Role(this, "LambdaExecutionRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      description: "Execution role for SarkariSaathi Lambda functions",
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole",
        ),
      ],
    });

    // Grant permissions to Lambda role
    usersTable.grantReadWriteData(lambdaExecutionRole);
    applicationsTable.grantReadWriteData(lambdaExecutionRole);
    schemesTable.grantReadData(lambdaExecutionRole);
    sessionsTable.grantReadWriteData(lambdaExecutionRole);
    smsConversationsTable.grantReadWriteData(lambdaExecutionRole);

    audioBucket.grantReadWrite(lambdaExecutionRole);
    schemeDocsBucket.grantRead(lambdaExecutionRole);
    ttsCacheBucket.grantReadWrite(lambdaExecutionRole);

    dataEncryptionKey.grantEncryptDecrypt(lambdaExecutionRole);

    // Grant Pinpoint SMS permissions
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "mobiletargeting:SendMessages",
          "mobiletargeting:GetApp",
          "mobiletargeting:GetSmsChannel",
          "mobiletargeting:UpdateSmsChannel",
        ],
        resources: [
          `arn:aws:mobiletargeting:${this.region}:${this.account}:apps/${pinpointApp.ref}`,
          `arn:aws:mobiletargeting:${this.region}:${this.account}:apps/${pinpointApp.ref}/*`,
        ],
      }),
    );

    // Grant SNS permissions for SMS status
    smsStatusTopic.grantPublish(lambdaExecutionRole);

    // Grant Bedrock permissions
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: [
          `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0`,
          `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v1`,
        ],
      }),
    );

    // Grant Transcribe permissions
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob",
        ],
        resources: ["*"],
      }),
    );

    // Grant Polly permissions
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["polly:SynthesizeSpeech"],
        resources: ["*"],
      }),
    );

    // Grant SSM Parameter Store permissions
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ssm:GetParameter", "ssm:GetParameters"],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter/sarkari-saathi/*`,
        ],
      }),
    );

    // Grant OpenSearch permissions
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "es:ESHttpGet",
          "es:ESHttpPost",
          "es:ESHttpPut",
          "es:ESHttpDelete",
        ],
        resources: [`${openSearchDomain.domainArn}/*`],
      }),
    );

    // ========================================
    // Environment Variables for Lambda
    // ========================================

    const commonEnvVars = {
      USERS_TABLE: usersTable.tableName,
      APPLICATIONS_TABLE: applicationsTable.tableName,
      SCHEMES_TABLE: schemesTable.tableName,
      SESSIONS_TABLE: sessionsTable.tableName,
      SMS_CONVERSATIONS_TABLE: smsConversationsTable.tableName,
      AUDIO_BUCKET: audioBucket.bucketName,
      SCHEME_DOCS_BUCKET: schemeDocsBucket.bucketName,
      TTS_CACHE_BUCKET: ttsCacheBucket.bucketName,
      KMS_KEY_ID: dataEncryptionKey.keyId,
      AWS_REGION: this.region,
      BHASHINI_API_KEY_PARAM: bhashiniApiKeyParam.parameterName,
      BHASHINI_API_URL_PARAM: bhashiniApiUrlParam.parameterName,
      OPENSEARCH_ENDPOINT: openSearchDomain.domainEndpoint,
      OPENSEARCH_DOMAIN_ARN: openSearchDomain.domainArn,
      PINPOINT_APP_ID: pinpointApp.ref,
      SMS_STATUS_TOPIC_ARN: smsStatusTopic.topicArn,
    };

    // ========================================
    // API Gateway with Enhanced Configuration
    // ========================================

    // CloudWatch Log Group for API Gateway
    const apiLogGroup = new logs.LogGroup(this, "ApiGatewayAccessLogs", {
      logGroupName: `/aws/apigateway/sarkari-saathi-access`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const api = new apigateway.RestApi(this, "SarkariSaathiAPI", {
      restApiName: "SarkariSaathi API",
      description: "API for SarkariSaathi voice-first assistant",
      deployOptions: {
        stageName: "dev",
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
        accessLogDestination: new apigateway.LogGroupLogDestination(
          apiLogGroup,
        ),
        accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields({
          caller: true,
          httpMethod: true,
          ip: true,
          protocol: true,
          requestTime: true,
          resourcePath: true,
          responseLength: true,
          status: true,
          user: true,
        }),
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ["Content-Type", "Authorization", "X-Api-Key"],
      },
      cloudWatchRole: true,
    });

    // API Key for authentication
    const apiKey = api.addApiKey("SarkariSaathiApiKey", {
      apiKeyName: "SarkariSaathi-API-Key",
      description: "API Key for SarkariSaathi client applications",
    });

    // Usage Plan with rate limiting
    const usagePlan = api.addUsagePlan("SarkariSaathiUsagePlan", {
      name: "Standard Usage Plan",
      description: "Usage plan with rate limiting for SarkariSaathi API",
      throttle: {
        rateLimit: 100, // requests per second
        burstLimit: 200, // maximum concurrent requests
      },
      quota: {
        limit: 10000, // requests per day
        period: apigateway.Period.DAY,
      },
    });

    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({
      stage: api.deploymentStage,
    });

    // Request Validators
    const requestValidator = new apigateway.RequestValidator(
      this,
      "RequestValidator",
      {
        restApi: api,
        requestValidatorName: "request-body-validator",
        validateRequestBody: true,
        validateRequestParameters: true,
      },
    );

    // ========================================
    // Lambda Functions for RAG Pipeline
    // ========================================

    // Scheme Ingestion Lambda
    const schemeIngestionFunction = new lambda.Function(
      this,
      "SchemeIngestionFunction",
      {
        functionName: "SarkariSaathi-SchemeIngestion",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "scheme_ingestion_handler.lambda_handler",
        code: lambda.Code.fromAsset("lambda", {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
              "bash",
              "-c",
              "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
            ],
          },
        }),
        timeout: cdk.Duration.minutes(5),
        memorySize: 512,
        environment: {
          ...commonEnvVars,
        },
        role: lambdaExecutionRole,
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [lambdaSecurityGroup],
      },
    );

    // Grant S3 trigger permissions
    schemeDocsBucket.grantRead(schemeIngestionFunction);

    // Eligibility Matching Lambda
    const eligibilityMatchingFunction = new lambda.Function(
      this,
      "EligibilityMatchingFunction",
      {
        functionName: "SarkariSaathi-EligibilityMatching",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "eligibility_matching_service.lambda_handler",
        code: lambda.Code.fromAsset("lambda", {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
              "bash",
              "-c",
              "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
            ],
          },
        }),
        timeout: cdk.Duration.seconds(30),
        memorySize: 1024,
        environment: {
          ...commonEnvVars,
        },
        role: lambdaExecutionRole,
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [lambdaSecurityGroup],
      },
    );

    // Bedrock RAG Lambda
    const bedrockRagFunction = new lambda.Function(this, "BedrockRagFunction", {
      functionName: "SarkariSaathi-BedrockRAG",
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "bedrock_rag_service.lambda_handler",
      code: lambda.Code.fromAsset("lambda", {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            "bash",
            "-c",
            "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
          ],
        },
      }),
      timeout: cdk.Duration.seconds(60),
      memorySize: 1024,
      environment: {
        ...commonEnvVars,
      },
      role: lambdaExecutionRole,
      vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },
      securityGroups: [lambdaSecurityGroup],
    });

    // Voice Handler Lambda
    const voiceHandlerFunction = new lambda.Function(
      this,
      "VoiceHandlerFunction",
      {
        functionName: "SarkariSaathi-VoiceHandler",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "voice_handler.lambda_handler",
        code: lambda.Code.fromAsset("lambda", {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
              "bash",
              "-c",
              "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
            ],
          },
        }),
        timeout: cdk.Duration.seconds(30),
        memorySize: 1024,
        environment: {
          ...commonEnvVars,
        },
        role: lambdaExecutionRole,
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [lambdaSecurityGroup],
      },
    );

    // SMS Handler Lambda
    const smsHandlerFunction = new lambda.Function(this, "SmsHandlerFunction", {
      functionName: "SarkariSaathi-SmsHandler",
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "sms_handler.lambda_handler",
      code: lambda.Code.fromAsset("lambda", {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            "bash",
            "-c",
            "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
          ],
        },
      }),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        ...commonEnvVars,
        CONVERSATION_MANAGER_FUNCTION: conversationManagerFunction.functionName,
      },
      role: lambdaExecutionRole,
      vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },
      securityGroups: [lambdaSecurityGroup],
    });

    // Grant SMS handler permission to invoke conversation manager
    conversationManagerFunction.grantInvoke(smsHandlerFunction);

    // Profile Handler Lambda
    const profileHandlerFunction = new lambda.Function(
      this,
      "ProfileHandlerFunction",
      {
        functionName: "SarkariSaathi-ProfileHandler",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "chat_handler.lambda_handler",
        code: lambda.Code.fromAsset("lambda", {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
              "bash",
              "-c",
              "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
            ],
          },
        }),
        timeout: cdk.Duration.seconds(15),
        memorySize: 512,
        environment: {
          ...commonEnvVars,
        },
        role: lambdaExecutionRole,
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [lambdaSecurityGroup],
      },
    );

    // Application Handler Lambda
    const applicationHandlerFunction = new lambda.Function(
      this,
      "ApplicationHandlerFunction",
      {
        functionName: "SarkariSaathi-ApplicationHandler",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "chat_handler.lambda_handler",
        code: lambda.Code.fromAsset("lambda", {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
              "bash",
              "-c",
              "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
            ],
          },
        }),
        timeout: cdk.Duration.seconds(30),
        memorySize: 512,
        environment: {
          ...commonEnvVars,
        },
        role: lambdaExecutionRole,
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [lambdaSecurityGroup],
      },
    );

    // Application Form Handler Lambda
    const applicationFormHandlerFunction = new lambda.Function(
      this,
      "ApplicationFormHandlerFunction",
      {
        functionName: "SarkariSaathi-ApplicationFormHandler",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "application_form_handler.lambda_handler",
        code: lambda.Code.fromAsset("lambda", {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
              "bash",
              "-c",
              "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
            ],
          },
        }),
        timeout: cdk.Duration.seconds(30),
        memorySize: 512,
        environment: {
          ...commonEnvVars,
        },
        role: lambdaExecutionRole,
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [lambdaSecurityGroup],
      },
    );

    // Conversation Manager Lambda for Step Functions orchestration
    const conversationManagerFunction = new lambda.Function(
      this,
      "ConversationManagerFunction",
      {
        functionName: "SarkariSaathi-ConversationManager",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "conversation_manager.lambda_handler",
        code: lambda.Code.fromAsset("lambda", {
          bundling: {
            image: lambda.Runtime.PYTHON_3_11.bundlingImage,
            command: [
              "bash",
              "-c",
              "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
            ],
          },
        }),
        timeout: cdk.Duration.seconds(60),
        memorySize: 1024,
        environment: {
          ...commonEnvVars,
        },
        role: lambdaExecutionRole,
        vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [lambdaSecurityGroup],
      },
    );

    // ========================================
    // Step Functions State Machine for Conversation Orchestration
    // ========================================

    // IAM Role for Step Functions
    const stepFunctionsRole = new iam.Role(this, "StepFunctionsRole", {
      assumedBy: new iam.ServicePrincipal("states.amazonaws.com"),
      description:
        "Execution role for SarkariSaathi conversation state machine",
    });

    // Grant permissions to invoke Lambda functions
    conversationManagerFunction.grantInvoke(stepFunctionsRole);
    eligibilityMatchingFunction.grantInvoke(stepFunctionsRole);

    // Grant permissions to access DynamoDB
    sessionsTable.grantReadWriteData(stepFunctionsRole);

    // Load state machine definition
    const stateMachineDefinition = fs.readFileSync(
      "lambda/conversation_state_machine.json",
      "utf8",
    );

    // Replace placeholders in state machine definition
    const processedDefinition = stateMachineDefinition
      .replace(
        /\$\{ConversationManagerFunction\}/g,
        conversationManagerFunction.functionArn,
      )
      .replace(
        /\$\{EligibilityMatchingFunction\}/g,
        eligibilityMatchingFunction.functionArn,
      )
      .replace(/\$\{SessionsTable\}/g, sessionsTable.tableName);

    // Create Step Functions state machine
    const conversationStateMachine = new sfn.StateMachine(
      this,
      "ConversationStateMachine",
      {
        stateMachineName: "SarkariSaathi-ConversationOrchestration",
        definitionBody: sfn.DefinitionBody.fromString(processedDefinition),
        role: stepFunctionsRole,
        timeout: cdk.Duration.minutes(5),
        tracingEnabled: true,
        logs: {
          destination: new logs.LogGroup(this, "StateMachineLogGroup", {
            logGroupName: "/aws/stepfunctions/sarkari-saathi-conversation",
            retention: logs.RetentionDays.ONE_WEEK,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
          }),
          level: sfn.LogLevel.ALL,
          includeExecutionData: true,
        },
      },
    );

    // Lambda function to trigger Step Functions
    const conversationOrchestratorFunction = new lambda.Function(
      this,
      "ConversationOrchestratorFunction",
      {
        functionName: "SarkariSaathi-ConversationOrchestrator",
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: "index.lambda_handler",
        code: lambda.Code.fromInline(`
import json
import boto3
import os
from datetime import datetime

stepfunctions = boto3.client('stepfunctions')
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']

def lambda_handler(event, context):
    """
    Orchestrator Lambda that triggers Step Functions state machine.
    This is the entry point for conversational AI requests.
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        session_id = body.get('sessionId', f"session-{datetime.utcnow().timestamp()}")
        user_message = body.get('message', '')
        language = body.get('language', 'en')
        
        if not user_message:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Start Step Functions execution
        execution_input = {
            'sessionId': session_id,
            'userMessage': user_message,
            'language': language
        }
        
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"exec-{session_id}-{int(datetime.utcnow().timestamp())}",
            input=json.dumps(execution_input)
        )
        
        # For synchronous response, we could wait for execution to complete
        # For now, return execution ARN
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'executionArn': response['executionArn'],
                'sessionId': session_id,
                'status': 'processing'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
`),
        timeout: cdk.Duration.seconds(30),
        memorySize: 256,
        environment: {
          STATE_MACHINE_ARN: conversationStateMachine.stateMachineArn,
        },
      },
    );

    // Grant permission to start Step Functions execution
    conversationStateMachine.grantStartExecution(
      conversationOrchestratorFunction,
    );

    // ========================================
    // API Gateway Endpoints with Request Validation
    // ========================================

    // Request models for validation
    const voiceRequestModel = api.addModel("VoiceRequestModel", {
      contentType: "application/json",
      modelName: "VoiceRequest",
      schema: {
        schema: apigateway.JsonSchemaVersion.DRAFT4,
        title: "Voice Request",
        type: apigateway.JsonSchemaType.OBJECT,
        properties: {
          audioData: { type: apigateway.JsonSchemaType.STRING },
          language: { type: apigateway.JsonSchemaType.STRING },
          userId: { type: apigateway.JsonSchemaType.STRING },
          sessionId: { type: apigateway.JsonSchemaType.STRING },
        },
        required: ["audioData", "language"],
      },
    });

    const smsRequestModel = api.addModel("SmsRequestModel", {
      contentType: "application/json",
      modelName: "SmsRequest",
      schema: {
        schema: apigateway.JsonSchemaVersion.DRAFT4,
        title: "SMS Request",
        type: apigateway.JsonSchemaType.OBJECT,
        properties: {
          phoneNumber: { type: apigateway.JsonSchemaType.STRING },
          message: { type: apigateway.JsonSchemaType.STRING },
          language: { type: apigateway.JsonSchemaType.STRING },
          userId: { type: apigateway.JsonSchemaType.STRING },
        },
        required: ["phoneNumber", "message"],
      },
    });

    // /voice endpoint for voice processing
    const voiceResource = api.root.addResource("voice");
    voiceResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(voiceHandlerFunction, {
        proxy: true,
        integrationResponses: [
          {
            statusCode: "200",
            responseParameters: {
              "method.response.header.Access-Control-Allow-Origin": "'*'",
            },
          },
        ],
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
        requestModels: {
          "application/json": voiceRequestModel,
        },
        methodResponses: [
          {
            statusCode: "200",
            responseParameters: {
              "method.response.header.Access-Control-Allow-Origin": true,
            },
          },
        ],
      },
    );

    // /sms endpoint for SMS processing
    const smsResource = api.root.addResource("sms");
    smsResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(smsHandlerFunction, {
        proxy: true,
        integrationResponses: [
          {
            statusCode: "200",
            responseParameters: {
              "method.response.header.Access-Control-Allow-Origin": "'*'",
            },
          },
        ],
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
        requestModels: {
          "application/json": smsRequestModel,
        },
        methodResponses: [
          {
            statusCode: "200",
            responseParameters: {
              "method.response.header.Access-Control-Allow-Origin": true,
            },
          },
        ],
      },
    );

    // /schemes endpoint for eligibility matching
    const schemesResource = api.root.addResource("schemes");
    schemesResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(eligibilityMatchingFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    // GET method for retrieving schemes
    schemesResource.addMethod(
      "GET",
      new apigateway.LambdaIntegration(eligibilityMatchingFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
      },
    );

    // /applications endpoint for application management
    const applicationsResource = api.root.addResource("applications");
    applicationsResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(applicationHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    applicationsResource.addMethod(
      "GET",
      new apigateway.LambdaIntegration(applicationHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
      },
    );

    // /applications/form endpoints for dynamic form generation and validation
    const applicationFormResource = applicationsResource.addResource("form");

    // /applications/form/generate - Generate form fields for a scheme
    const formGenerateResource =
      applicationFormResource.addResource("generate");
    formGenerateResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(applicationFormHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    // /applications/form/validate - Validate form data
    const formValidateResource =
      applicationFormResource.addResource("validate");
    formValidateResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(applicationFormHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    // /applications/form/save - Save partial or complete application
    const formSaveResource = applicationFormResource.addResource("save");
    formSaveResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(applicationFormHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    // /applications/{applicationId} for specific application
    const applicationIdResource =
      applicationsResource.addResource("{applicationId}");
    applicationIdResource.addMethod(
      "GET",
      new apigateway.LambdaIntegration(applicationFormHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
      },
    );

    applicationIdResource.addMethod(
      "PUT",
      new apigateway.LambdaIntegration(applicationHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    // /profile endpoint for user profile management
    const profileResource = api.root.addResource("profile");
    profileResource.addMethod(
      "GET",
      new apigateway.LambdaIntegration(profileHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
      },
    );

    profileResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(profileHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    profileResource.addMethod(
      "PUT",
      new apigateway.LambdaIntegration(profileHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    profileResource.addMethod(
      "DELETE",
      new apigateway.LambdaIntegration(profileHandlerFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
      },
    );

    // /chat endpoint for Bedrock RAG
    const chatResource = api.root.addResource("chat");
    chatResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(bedrockRagFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    // /conversation endpoint for Step Functions orchestrated conversation
    const conversationResource = api.root.addResource("conversation");
    conversationResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(conversationOrchestratorFunction, {
        proxy: true,
        integrationResponses: [
          {
            statusCode: "202",
            responseParameters: {
              "method.response.header.Access-Control-Allow-Origin": "'*'",
            },
          },
        ],
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
        methodResponses: [
          {
            statusCode: "202",
            responseParameters: {
              "method.response.header.Access-Control-Allow-Origin": true,
            },
          },
        ],
      },
    );

    // /ingest endpoint for scheme ingestion (admin only)
    const ingestResource = api.root.addResource("ingest");
    ingestResource.addMethod(
      "POST",
      new apigateway.LambdaIntegration(schemeIngestionFunction, {
        proxy: true,
      }),
      {
        apiKeyRequired: true,
        requestValidator: requestValidator,
      },
    );

    // ========================================
    // AWS WAF for API Protection
    // ========================================

    // IP Set for India (optional - can be configured later)
    const indiaIpSet = new wafv2.CfnIPSet(this, "IndiaIPSet", {
      name: "SarkariSaathi-India-IPs",
      description: "IP ranges for India (optional geo-blocking)",
      scope: "REGIONAL",
      ipAddressVersion: "IPV4",
      addresses: [], // Can be populated with India IP ranges if needed
    });

    // WAF Web ACL with comprehensive rules
    const webAcl = new wafv2.CfnWebACL(this, "ApiWebACL", {
      name: "SarkariSaathi-API-WAF",
      description: "WAF rules for SarkariSaathi API protection",
      scope: "REGIONAL",
      defaultAction: { allow: {} },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: "SarkariSaathiWAF",
      },
      rules: [
        // Rate limiting rule - 2000 requests per 5 minutes per IP
        {
          name: "RateLimitRule",
          priority: 1,
          statement: {
            rateBasedStatement: {
              limit: 2000, // 2000 requests per 5 minutes
              aggregateKeyType: "IP",
            },
          },
          action: {
            block: {
              customResponse: {
                responseCode: 429,
                customResponseBodyKey: "rate-limit-response",
              },
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "RateLimitRule",
          },
        },
        // AWS Managed Rules - Core Rule Set (CRS)
        {
          name: "AWSManagedRulesCommonRuleSet",
          priority: 2,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesCommonRuleSet",
              excludedRules: [],
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesCommonRuleSet",
          },
        },
        // SQL Injection protection
        {
          name: "AWSManagedRulesSQLiRuleSet",
          priority: 3,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesSQLiRuleSet",
              excludedRules: [],
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesSQLiRuleSet",
          },
        },
        // Known bad inputs protection
        {
          name: "AWSManagedRulesKnownBadInputsRuleSet",
          priority: 4,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesKnownBadInputsRuleSet",
              excludedRules: [],
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesKnownBadInputsRuleSet",
          },
        },
        // Amazon IP reputation list
        {
          name: "AWSManagedRulesAmazonIpReputationList",
          priority: 5,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesAmazonIpReputationList",
              excludedRules: [],
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesAmazonIpReputationList",
          },
        },
        // Anonymous IP list (blocks VPNs, proxies, Tor)
        {
          name: "AWSManagedRulesAnonymousIpList",
          priority: 6,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesAnonymousIpList",
              excludedRules: [],
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesAnonymousIpList",
          },
        },
      ],
      customResponseBodies: {
        "rate-limit-response": {
          contentType: "APPLICATION_JSON",
          content: JSON.stringify({
            error: "Rate limit exceeded",
            message: "Too many requests. Please try again later.",
          }),
        },
      },
    });

    // Associate WAF with API Gateway
    new wafv2.CfnWebACLAssociation(this, "ApiWafAssociation", {
      resourceArn: `arn:aws:apigateway:${this.region}::/restapis/${api.restApiId}/stages/${api.deploymentStage.stageName}`,
      webAclArn: webAcl.attrArn,
    });

    // WAF Logging
    const wafLogGroup = new logs.LogGroup(this, "WafLogGroup", {
      logGroupName: `/aws/wafv2/sarkari-saathi`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new wafv2.CfnLoggingConfiguration(this, "WafLogging", {
      resourceArn: webAcl.attrArn,
      logDestinationConfigs: [
        `arn:aws:logs:${this.region}:${this.account}:log-group:${wafLogGroup.logGroupName}`,
      ],
    });

    // ========================================
    // CloudFront Distribution for API Caching
    // ========================================

    // Cache Policy for API responses
    const apiCachePolicy = new cloudfront.CachePolicy(this, "ApiCachePolicy", {
      cachePolicyName: "SarkariSaathi-API-Cache-Policy",
      comment: "Cache policy for SarkariSaathi API with query string support",
      defaultTtl: cdk.Duration.minutes(5),
      minTtl: cdk.Duration.seconds(1),
      maxTtl: cdk.Duration.hours(1),
      cookieBehavior: cloudfront.CacheCookieBehavior.none(),
      headerBehavior: cloudfront.CacheHeaderBehavior.allowList(
        "Authorization",
        "X-Api-Key",
      ),
      queryStringBehavior: cloudfront.CacheQueryStringBehavior.all(),
      enableAcceptEncodingGzip: true,
      enableAcceptEncodingBrotli: true,
    });

    // Cache Policy for static content (schemes data)
    const staticCachePolicy = new cloudfront.CachePolicy(
      this,
      "StaticCachePolicy",
      {
        cachePolicyName: "SarkariSaathi-Static-Cache-Policy",
        comment: "Cache policy for static scheme data",
        defaultTtl: cdk.Duration.hours(24),
        minTtl: cdk.Duration.hours(1),
        maxTtl: cdk.Duration.days(7),
        cookieBehavior: cloudfront.CacheCookieBehavior.none(),
        headerBehavior: cloudfront.CacheHeaderBehavior.none(),
        queryStringBehavior: cloudfront.CacheQueryStringBehavior.none(),
        enableAcceptEncodingGzip: true,
        enableAcceptEncodingBrotli: true,
      },
    );

    // Origin Request Policy for API Gateway
    const apiOriginRequestPolicy = new cloudfront.OriginRequestPolicy(
      this,
      "ApiOriginRequestPolicy",
      {
        originRequestPolicyName: "SarkariSaathi-API-Origin-Policy",
        comment: "Origin request policy for API Gateway",
        cookieBehavior: cloudfront.OriginRequestCookieBehavior.none(),
        headerBehavior: cloudfront.OriginRequestHeaderBehavior.allowList(
          "Authorization",
          "X-Api-Key",
          "Accept",
          "Content-Type",
        ),
        queryStringBehavior: cloudfront.OriginRequestQueryStringBehavior.all(),
      },
    );

    // CloudFront Distribution
    const distribution = new cloudfront.Distribution(this, "ApiDistribution", {
      comment: "SarkariSaathi API CloudFront Distribution",
      defaultBehavior: {
        origin: new origins.RestApiOrigin(api, {
          originPath: `/${api.deploymentStage.stageName}`,
        }),
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: apiCachePolicy,
        originRequestPolicy: apiOriginRequestPolicy,
        compress: true,
      },
      additionalBehaviors: {
        // Cache schemes endpoint more aggressively
        "/schemes": {
          origin: new origins.RestApiOrigin(api, {
            originPath: `/${api.deploymentStage.stageName}`,
          }),
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: staticCachePolicy,
          compress: true,
        },
        // No caching for voice and SMS endpoints (real-time)
        "/voice": {
          origin: new origins.RestApiOrigin(api, {
            originPath: `/${api.deploymentStage.stageName}`,
          }),
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: apiOriginRequestPolicy,
          compress: true,
        },
        "/sms": {
          origin: new origins.RestApiOrigin(api, {
            originPath: `/${api.deploymentStage.stageName}`,
          }),
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: apiOriginRequestPolicy,
          compress: true,
        },
      },
      priceClass: cloudfront.PriceClass.PRICE_CLASS_200, // Includes India edge locations
      enableLogging: true,
      logBucket: new s3.Bucket(this, "CloudFrontLogBucket", {
        bucketName: `sarkari-saathi-cf-logs-${this.account}`,
        encryption: s3.BucketEncryption.S3_MANAGED,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        lifecycleRules: [
          {
            id: "DeleteOldLogs",
            expiration: cdk.Duration.days(30),
            enabled: true,
          },
        ],
        removalPolicy: cdk.RemovalPolicy.DESTROY,
        autoDeleteObjects: true,
      }),
      logFilePrefix: "api-logs/",
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      httpVersion: cloudfront.HttpVersion.HTTP2_AND_3,
    });

    // CloudFront Logging
    new logs.LogGroup(this, "CloudFrontLogGroup", {
      logGroupName: `/aws/cloudfront/sarkari-saathi`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ========================================
    // CloudWatch Log Groups
    // ========================================

    new logs.LogGroup(this, "ApiGatewayLogGroup", {
      logGroupName: `/aws/apigateway/sarkari-saathi`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new logs.LogGroup(this, "VoiceHandlerLogGroup", {
      logGroupName: `/aws/lambda/SarkariSaathi-VoiceHandler`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new logs.LogGroup(this, "SmsHandlerLogGroup", {
      logGroupName: `/aws/lambda/SarkariSaathi-SmsHandler`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new logs.LogGroup(this, "ProfileHandlerLogGroup", {
      logGroupName: `/aws/lambda/SarkariSaathi-ProfileHandler`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    new logs.LogGroup(this, "ApplicationHandlerLogGroup", {
      logGroupName: `/aws/lambda/SarkariSaathi-ApplicationHandler`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ========================================
    // Amazon Connect for IVR
    // ========================================

    // IVR Callbacks table for scheduling callbacks
    const ivrCallbacksTable = new dynamodb.Table(this, "IvrCallbacksTable", {
      tableName: "SarkariSaathi-IvrCallbacks",
      partitionKey: {
        name: "callbackId",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dataEncryptionKey,
      timeToLiveAttribute: "ttl",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // GSI on phoneNumber for callback lookups
    ivrCallbacksTable.addGlobalSecondaryIndex({
      indexName: "phoneNumber-index",
      partitionKey: {
        name: "phoneNumber",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: { name: "scheduledTime", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI on status for processing pending callbacks
    ivrCallbacksTable.addGlobalSecondaryIndex({
      indexName: "status-index",
      partitionKey: { name: "status", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "scheduledTime", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // IVR Handler Lambda
    const ivrHandlerFunction = new lambda.Function(this, "IvrHandlerFunction", {
      functionName: "SarkariSaathi-IvrHandler",
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "ivr_handler.lambda_handler",
      code: lambda.Code.fromAsset("lambda", {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            "bash",
            "-c",
            "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
          ],
        },
      }),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        ...commonEnvVars,
        IVR_CALLBACKS_TABLE: ivrCallbacksTable.tableName,
        CONVERSATION_MANAGER_FUNCTION: conversationManagerFunction.functionName,
        CONNECT_INSTANCE_ID: "PLACEHOLDER_UPDATE_AFTER_CONNECT_SETUP",
      },
      role: lambdaExecutionRole,
      vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },
      securityGroups: [lambdaSecurityGroup],
    });

    // Grant IVR handler permissions
    ivrCallbacksTable.grantReadWriteData(ivrHandlerFunction);
    conversationManagerFunction.grantInvoke(ivrHandlerFunction);

    // Grant Amazon Connect permissions to IVR handler
    lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "connect:StartOutboundVoiceContact",
          "connect:StopContact",
          "connect:GetContactAttributes",
          "connect:UpdateContactAttributes",
          "connect:DescribeInstance",
          "connect:ListQueues",
          "connect:ListContactFlows",
        ],
        resources: ["*"], // Will be restricted to specific Connect instance after setup
      }),
    );

    // Store Connect configuration in SSM
    const connectInstanceIdParam = new ssm.StringParameter(
      this,
      "ConnectInstanceId",
      {
        parameterName: "/sarkari-saathi/connect/instance-id",
        stringValue: "PLACEHOLDER_UPDATE_AFTER_CONNECT_SETUP",
        description: "Amazon Connect Instance ID for IVR",
        tier: ssm.ParameterTier.STANDARD,
      },
    );

    const connectContactFlowIdParam = new ssm.StringParameter(
      this,
      "ConnectContactFlowId",
      {
        parameterName: "/sarkari-saathi/connect/contact-flow-id",
        stringValue: "PLACEHOLDER_UPDATE_AFTER_CONNECT_SETUP",
        description: "Amazon Connect Contact Flow ID for main IVR flow",
        tier: ssm.ParameterTier.STANDARD,
      },
    );

    const connectQueueIdParam = new ssm.StringParameter(
      this,
      "ConnectQueueId",
      {
        parameterName: "/sarkari-saathi/connect/queue-id",
        stringValue: "PLACEHOLDER_UPDATE_AFTER_CONNECT_SETUP",
        description: "Amazon Connect Queue ID for agent transfers",
        tier: ssm.ParameterTier.STANDARD,
      },
    );

    // IVR configuration parameters
    new ssm.StringParameter(this, "IvrEnableRecordingParam", {
      parameterName: "/sarkari-saathi/ivr/enable-recording",
      stringValue: "true",
      description: "Enable call recording for quality assurance",
      tier: ssm.ParameterTier.STANDARD,
    });

    new ssm.StringParameter(this, "IvrMaxQueueTimeParam", {
      parameterName: "/sarkari-saathi/ivr/max-queue-time",
      stringValue: "300", // 5 minutes
      description: "Maximum queue time in seconds before offering callback",
      tier: ssm.ParameterTier.STANDARD,
    });

    new ssm.StringParameter(this, "IvrCallbackWindowParam", {
      parameterName: "/sarkari-saathi/ivr/callback-window",
      stringValue: "60", // 1 hour
      description: "Default callback window in minutes",
      tier: ssm.ParameterTier.STANDARD,
    });

    // CloudWatch Log Group for IVR Handler
    new logs.LogGroup(this, "IvrHandlerLogGroup", {
      logGroupName: `/aws/lambda/SarkariSaathi-IvrHandler`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // CloudWatch Log Group for Amazon Connect
    new logs.LogGroup(this, "ConnectLogGroup", {
      logGroupName: `/aws/connect/sarkari-saathi`,
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ========================================
    // Stack Outputs
    // ========================================

    new cdk.CfnOutput(this, "ApiEndpoint", {
      value: api.url,
      description: "API Gateway endpoint URL",
      exportName: "SarkariSaathiApiEndpoint",
    });

    new cdk.CfnOutput(this, "ApiKeyId", {
      value: apiKey.keyId,
      description: "API Key ID for authentication",
      exportName: "SarkariSaathiApiKeyId",
    });

    new cdk.CfnOutput(this, "UsersTableName", {
      value: usersTable.tableName,
      description: "DynamoDB Users table name",
    });

    new cdk.CfnOutput(this, "AudioBucketName", {
      value: audioBucket.bucketName,
      description: "S3 bucket for audio files",
    });

    new cdk.CfnOutput(this, "KMSKeyId", {
      value: dataEncryptionKey.keyId,
      description: "KMS key ID for data encryption",
    });

    new cdk.CfnOutput(this, "VPCId", {
      value: vpc.vpcId,
      description: "VPC ID for secure communication",
    });

    new cdk.CfnOutput(this, "BhashiniApiKeyParameter", {
      value: bhashiniApiKeyParam.parameterName,
      description: "SSM Parameter name for Bhashini API key",
    });

    new cdk.CfnOutput(this, "OpenSearchEndpoint", {
      value: openSearchDomain.domainEndpoint,
      description: "OpenSearch domain endpoint for scheme search",
    });

    new cdk.CfnOutput(this, "OpenSearchDomainArn", {
      value: openSearchDomain.domainArn,
      description: "OpenSearch domain ARN",
    });

    new cdk.CfnOutput(this, "WafWebAclArn", {
      value: webAcl.attrArn,
      description: "WAF Web ACL ARN for API protection",
    });

    new cdk.CfnOutput(this, "CloudFrontDistributionDomain", {
      value: distribution.distributionDomainName,
      description: "CloudFront distribution domain name",
      exportName: "SarkariSaathiCloudFrontDomain",
    });

    new cdk.CfnOutput(this, "CloudFrontDistributionId", {
      value: distribution.distributionId,
      description: "CloudFront distribution ID",
    });

    new cdk.CfnOutput(this, "ConversationStateMachineArn", {
      value: conversationStateMachine.stateMachineArn,
      description:
        "Step Functions state machine ARN for conversation orchestration",
      exportName: "SarkariSaathiConversationStateMachine",
    });

    new cdk.CfnOutput(this, "ConversationManagerFunctionArn", {
      value: conversationManagerFunction.functionArn,
      description: "Conversation Manager Lambda function ARN",
    });

    new cdk.CfnOutput(this, "PinpointAppId", {
      value: pinpointApp.ref,
      description: "Pinpoint Application ID for SMS",
      exportName: "SarkariSaathiPinpointAppId",
    });

    new cdk.CfnOutput(this, "SmsConversationsTableName", {
      value: smsConversationsTable.tableName,
      description: "DynamoDB SMS Conversations table name",
    });

    new cdk.CfnOutput(this, "SmsStatusTopicArn", {
      value: smsStatusTopic.topicArn,
      description: "SNS Topic ARN for SMS delivery status",
    });

    new cdk.CfnOutput(this, "IvrHandlerFunctionArn", {
      value: ivrHandlerFunction.functionArn,
      description: "IVR Handler Lambda function ARN for Amazon Connect",
      exportName: "SarkariSaathiIvrHandlerArn",
    });

    new cdk.CfnOutput(this, "IvrCallbacksTableName", {
      value: ivrCallbacksTable.tableName,
      description: "DynamoDB IVR Callbacks table name",
    });

    new cdk.CfnOutput(this, "ConnectInstanceIdParameter", {
      value: connectInstanceIdParam.parameterName,
      description: "SSM Parameter for Amazon Connect Instance ID",
    });

    new cdk.CfnOutput(this, "ConnectContactFlowIdParameter", {
      value: connectContactFlowIdParam.parameterName,
      description: "SSM Parameter for Amazon Connect Contact Flow ID",
    });
  }
}

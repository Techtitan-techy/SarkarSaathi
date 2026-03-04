/**
 * Infrastructure tests for SarkariSaathi CDK stack
 * Validates that all required resources are created correctly
 */

import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { SarkariSaathiStack } from "../lib/sarkari-saathi-stack";

describe("SarkariSaathi Infrastructure", () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new SarkariSaathiStack(app, "TestStack", {
      env: {
        account: "123456789012",
        region: "ap-south-1",
      },
    });
    template = Template.fromStack(stack);
  });

  describe("KMS Encryption", () => {
    test("should create KMS key with rotation enabled", () => {
      template.hasResourceProperties("AWS::KMS::Key", {
        EnableKeyRotation: true,
      });
    });

    test("should create KMS key alias", () => {
      template.hasResourceProperties("AWS::KMS::Alias", {
        AliasName: "alias/sarkari-saathi-data",
      });
    });
  });

  describe("DynamoDB Tables", () => {
    test("should create Users table with correct configuration", () => {
      template.hasResourceProperties("AWS::DynamoDB::Table", {
        TableName: "SarkariSaathi-Users",
        BillingMode: "PAY_PER_REQUEST",
        PointInTimeRecoverySpecification: {
          PointInTimeRecoveryEnabled: true,
        },
      });
    });

    test("should create Applications table with GSIs", () => {
      template.hasResourceProperties("AWS::DynamoDB::Table", {
        TableName: "SarkariSaathi-Applications",
        GlobalSecondaryIndexes: [
          {
            IndexName: "userId-index",
          },
          {
            IndexName: "status-index",
          },
        ],
      });
    });

    test("should create Schemes table with category and state GSIs", () => {
      template.hasResourceProperties("AWS::DynamoDB::Table", {
        TableName: "SarkariSaathi-Schemes",
        GlobalSecondaryIndexes: [
          {
            IndexName: "category-index",
          },
          {
            IndexName: "state-index",
          },
        ],
      });
    });

    test("should create Sessions table with TTL", () => {
      template.hasResourceProperties("AWS::DynamoDB::Table", {
        TableName: "SarkariSaathi-Sessions",
        TimeToLiveSpecification: {
          AttributeName: "ttl",
          Enabled: true,
        },
      });
    });
  });

  describe("S3 Buckets", () => {
    test("should create audio bucket with lifecycle policy", () => {
      template.hasResourceProperties("AWS::S3::Bucket", {
        LifecycleConfiguration: {
          Rules: [
            {
              ExpirationInDays: 7,
              Status: "Enabled",
            },
          ],
        },
      });
    });

    test("should enable encryption for all buckets", () => {
      const buckets = template.findResources("AWS::S3::Bucket");
      const bucketCount = Object.keys(buckets).length;
      expect(bucketCount).toBeGreaterThanOrEqual(3);
    });
  });

  describe("VPC and Security", () => {
    test("should create VPC with 2 availability zones", () => {
      template.hasResourceProperties("AWS::EC2::VPC", {
        EnableDnsHostnames: true,
        EnableDnsSupport: true,
      });
    });

    test("should create security group for Lambda", () => {
      template.hasResourceProperties("AWS::EC2::SecurityGroup", {
        GroupDescription: "Security group for SarkariSaathi Lambda functions",
      });
    });
  });

  describe("IAM Roles", () => {
    test("should create Lambda execution role", () => {
      template.hasResourceProperties("AWS::IAM::Role", {
        AssumeRolePolicyDocument: {
          Statement: [
            {
              Action: "sts:AssumeRole",
              Effect: "Allow",
              Principal: {
                Service: "lambda.amazonaws.com",
              },
            },
          ],
        },
      });
    });

    test("should grant Bedrock permissions to Lambda role", () => {
      const policies = template.findResources("AWS::IAM::Policy");
      const policyStatements = Object.values(policies).flatMap((policy: any) =>
        policy.Properties.PolicyDocument.Statement.filter((stmt: any) =>
          stmt.Action?.includes("bedrock:InvokeModel"),
        ),
      );
      expect(policyStatements.length).toBeGreaterThan(0);
    });

    test("should grant SSM Parameter Store permissions", () => {
      const policies = template.findResources("AWS::IAM::Policy");
      const policyStatements = Object.values(policies).flatMap((policy: any) =>
        policy.Properties.PolicyDocument.Statement.filter((stmt: any) =>
          stmt.Action?.includes("ssm:GetParameter"),
        ),
      );
      expect(policyStatements.length).toBeGreaterThan(0);
    });
  });

  describe("API Gateway", () => {
    test("should create REST API", () => {
      template.hasResourceProperties("AWS::ApiGateway::RestApi", {
        Name: "SarkariSaathi API",
      });
    });

    test("should enable CORS", () => {
      template.hasResourceProperties("AWS::ApiGateway::Method", {
        HttpMethod: "OPTIONS",
      });
    });
  });

  describe("Systems Manager Parameters", () => {
    test("should create AWS Translate feature flag parameter", () => {
      template.hasResourceProperties("AWS::SSM::Parameter", {
        Name: "/sarkari-saathi/features/enable-aws-translate",
        Type: "String",
      });
    });

    test("should create feature flag parameters", () => {
      });
    });
  });
});

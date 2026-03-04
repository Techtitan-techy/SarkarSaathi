#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { SarkariSaathiStack } from "../lib/sarkari-saathi-stack";

const app = new cdk.App();

new SarkariSaathiStack(app, "SarkariSaathiStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "ap-south-1", // Mumbai region
  },
  description:
    "SarkariSaathi - Voice-first AI assistant for Indian government schemes",
  tags: {
    Project: "SarkariSaathi",
    Environment: "Development",
    Hackathon: "AWS-AI-for-Bharat",
  },
});

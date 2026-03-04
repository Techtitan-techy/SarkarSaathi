# SarkariSaathi Monitoring Guide

## Overview

This guide covers the monitoring, logging, and alerting setup for SarkariSaathi. The system uses AWS CloudWatch for comprehensive observability across all components.

## CloudWatch Dashboards

### 1. System Health Dashboard

**Dashboard Name**: `SarkariSaathi-SystemHealth`

**Purpose**: Monitor technical health and performance of all AWS services

**Widgets**:
- Lambda Errors: Track error rates across all Lambda functions
- Lambda Duration: Monitor average execution time
- Lambda Invocations: Track request volume
- Lambda Throttles: Detect capacity issues
- API Requests: Monitor API Gateway traffic
- API Latency: Track response times
- API 4XX Errors: Client-side errors
- API 5XX Errors: Server-side errors
- DynamoDB Read Capacity: Monitor read throughput
- DynamoDB Write Capacity: Monitor write throughput

**Access**: AWS Console → CloudWatch → Dashboards → SarkariSaathi-SystemHealth

### 2. Business Metrics Dashboard

**Dashboard Name**: `SarkariSaathi-BusinessMetrics`

**Purpose**: Track business KPIs and user engagement

**Widgets**:
- User Engagement: Active users, new registrations
- Scheme Discoveries: Searches and matches
- Applications: Submitted and approved applications
- Channel Usage: Voice, SMS, IVR interaction counts

**Custom Metrics**:
```python
from metrics_publisher import publish_user_engagement, publish_scheme_discovery

# Publish user metrics
publish_user_engagement(active_users=150, new_users=25)

# Publish scheme discovery metrics
publish_scheme_discovery(searches=200, matches=180)
```

### 3. Cost Monitoring Dashboard

**Dashboard Name**: `SarkariSaathi-CostMonitoring`

**Purpose**: Track cost indicators and optimize spending

**Widgets**:
- Lambda Invocations: Primary cost driver
- DynamoDB Capacity Units: Read/write costs
- API Requests: API Gateway costs

**Cost Optimization Tips**:
- Monitor Lambda invocations to identify optimization opportunities
- Track DynamoDB capacity to ensure on-demand billing is cost-effective
- Review API request patterns for caching opportunities

## CloudWatch Alarms

### Lambda Alarms

#### 1. Error Rate
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as sns from "aws-cdk-lib/aws-sns";
import * as subscriptions from "aws-cdk-lib/aws-sns-subscriptions";
import * as actions from "aws-cdk-lib/aws-cloudwatch-actions";

export interface MonitoringStackProps extends cdk.StackProps {
  lambdaFunctions: lambda.IFunction[];
  dynamodbTables: dynamodb.ITable[];
  apiGateway: apigateway.RestApi;
  alertEmail: string;
}

export class MonitoringStack extends cdk.Stack {
  public readonly dashboard: cloudwatch.Dashboard;
  public readonly alarmTopic: sns.Topic;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    // SNS Topic for alarms
    this.alarmTopic = new sns.Topic(this, "AlarmTopic", {
      displayName: "SarkariSaathi Alarms",
      topicName: "SarkariSaathi-Alarms",
    });

    // Subscribe email to alarm topic
    this.alarmTopic.addSubscription(
      new subscriptions.EmailSubscription(props.alertEmail),
    );

    // Create dashboards
    this.createSystemHealthDashboard(props);
    this.createBusinessMetricsDashboard(props);
    this.createCostMonitoringDashboard(props);

    // Create alarms
    this.createLambdaAlarms(props.lambdaFunctions);
    this.createApiGatewayAlarms(props.apiGateway);
    this.createDynamoDBAlarms(props.dynamodbTables);
  }

  private createSystemHealthDashboard(props: MonitoringStackProps) {
    const dashboard = new cloudwatch.Dashboard(this, "SystemHealthDashboard", {
      dashboardName: "SarkariSaathi-SystemHealth",
    });

    // Lambda metrics
    const lambdaErrorsWidget = new cloudwatch.GraphWidget({
      title: "Lambda Errors",
      left: props.lambdaFunctions.map((fn) =>
        fn.metricErrors({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ),
      width: 12,
      height: 6,
    });

    const lambdaDurationWidget = new cloudwatch.GraphWidget({
      title: "Lambda Duration (ms)",
      left: props.lambdaFunctions.map((fn) =>
        fn.metricDuration({
          statistic: "Average",
          period: cdk.Duration.minutes(5),
        }),
      ),
      width: 12,
      height: 6,
    });

    const lambdaInvocationsWidget = new cloudwatch.GraphWidget({
      title: "Lambda Invocations",
      left: props.lambdaFunctions.map((fn) =>
        fn.metricInvocations({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ),
      width: 12,
      height: 6,
    });

    const lambdaThrottlesWidget = new cloudwatch.GraphWidget({
      title: "Lambda Throttles",
      left: props.lambdaFunctions.map((fn) =>
        fn.metricThrottles({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ),
      width: 12,
      height: 6,
    });

    // API Gateway metrics
    const apiRequestsWidget = new cloudwatch.GraphWidget({
      title: "API Requests",
      left: [
        props.apiGateway.metricCount({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
      height: 6,
    });

    const apiLatencyWidget = new cloudwatch.GraphWidget({
      title: "API Latency (ms)",
      left: [
        props.apiGateway.metricLatency({
          statistic: "Average",
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
      height: 6,
    });

    const api4xxErrorsWidget = new cloudwatch.GraphWidget({
      title: "API 4XX Errors",
      left: [
        props.apiGateway.metricClientError({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
      height: 6,
    });

    const api5xxErrorsWidget = new cloudwatch.GraphWidget({
      title: "API 5XX Errors",
      left: [
        props.apiGateway.metricServerError({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ],
      width: 12,
      height: 6,
    });

    // DynamoDB metrics
    const dynamoReadCapacityWidget = new cloudwatch.GraphWidget({
      title: "DynamoDB Read Capacity",
      left: props.dynamodbTables.map((table) =>
        table.metricConsumedReadCapacityUnits({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ),
      width: 12,
      height: 6,
    });

    const dynamoWriteCapacityWidget = new cloudwatch.GraphWidget({
      title: "DynamoDB Write Capacity",
      left: props.dynamodbTables.map((table) =>
        table.metricConsumedWriteCapacityUnits({
          statistic: "Sum",
          period: cdk.Duration.minutes(5),
        }),
      ),
      width: 12,
      height: 6,
    });

    dashboard.addWidgets(
      lambdaErrorsWidget,
      lambdaDurationWidget,
      lambdaInvocationsWidget,
      lambdaThrottlesWidget,
      apiRequestsWidget,
      apiLatencyWidget,
      api4xxErrorsWidget,
      api5xxErrorsWidget,
      dynamoReadCapacityWidget,
      dynamoWriteCapacityWidget,
    );

    this.dashboard = dashboard;
  }

  private createBusinessMetricsDashboard(props: MonitoringStackProps) {
    const dashboard = new cloudwatch.Dashboard(
      this,
      "BusinessMetricsDashboard",
      {
        dashboardName: "SarkariSaathi-BusinessMetrics",
      },
    );

    // Custom metrics for business KPIs
    const userEngagementWidget = new cloudwatch.GraphWidget({
      title: "User Engagement",
      left: [
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "ActiveUsers",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "NewUsers",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
      ],
      width: 12,
      height: 6,
    });

    const schemeDiscoveriesWidget = new cloudwatch.GraphWidget({
      title: "Scheme Discoveries",
      left: [
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "SchemeSearches",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "SchemeMatches",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
      ],
      width: 12,
      height: 6,
    });

    const applicationsWidget = new cloudwatch.GraphWidget({
      title: "Applications",
      left: [
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "ApplicationsSubmitted",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "ApplicationsApproved",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
      ],
      width: 12,
      height: 6,
    });

    const channelUsageWidget = new cloudwatch.GraphWidget({
      title: "Channel Usage",
      left: [
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "VoiceInteractions",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "SMSInteractions",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
        new cloudwatch.Metric({
          namespace: "SarkariSaathi",
          metricName: "IVRInteractions",
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
      ],
      width: 12,
      height: 6,
    });

    dashboard.addWidgets(
      userEngagementWidget,
      schemeDiscoveriesWidget,
      applicationsWidget,
      channelUsageWidget,
    );
  }

  private createCostMonitoringDashboard(props: MonitoringStackProps) {
    const dashboard = new cloudwatch.Dashboard(
      this,
      "CostMonitoringDashboard",
      {
        dashboardName: "SarkariSaathi-CostMonitoring",
      },
    );

    // Lambda invocations (cost proxy)
    const lambdaCostWidget = new cloudwatch.GraphWidget({
      title: "Lambda Invocations (Cost Indicator)",
      left: props.lambdaFunctions.map((fn) =>
        fn.metricInvocations({
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
      ),
      width: 12,
      height: 6,
    });

    // DynamoDB capacity (cost proxy)
    const dynamoCostWidget = new cloudwatch.GraphWidget({
      title: "DynamoDB Capacity Units (Cost Indicator)",
      left: props.dynamodbTables.flatMap((table) => [
        table.metricConsumedReadCapacityUnits({
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
        table.metricConsumedWriteCapacityUnits({
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
      ]),
      width: 12,
      height: 6,
    });

    // API requests (cost proxy)
    const apiCostWidget = new cloudwatch.GraphWidget({
      title: "API Requests (Cost Indicator)",
      left: [
        props.apiGateway.metricCount({
          statistic: "Sum",
          period: cdk.Duration.hours(1),
        }),
      ],
      width: 12,
      height: 6,
    });

    dashboard.addWidgets(lambdaCostWidget, dynamoCostWidget, apiCostWidget);
  }

  private createLambdaAlarms(functions: lambda.IFunction[]) {
    functions.forEach((fn, index) => {
      // Error rate alarm
      const errorAlarm = new cloudwatch.Alarm(
        this,
        `LambdaErrorAlarm${index}`,
        {
          metric: fn.metricErrors({
            statistic: "Sum",
            period: cdk.Duration.minutes(5),
          }),
          threshold: 10,
          evaluationPeriods: 2,
          comparisonOperator:
            cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
          alarmDescription: `High error rate for ${fn.functionName}`,
          alarmName: `SarkariSaathi-${fn.functionName}-Errors`,
          treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        },
      );

      errorAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

      // Duration alarm (performance degradation)
      const durationAlarm = new cloudwatch.Alarm(
        this,
        `LambdaDurationAlarm${index}`,
        {
          metric: fn.metricDuration({
            statistic: "Average",
            period: cdk.Duration.minutes(5),
          }),
          threshold: 3000, // 3 seconds
          evaluationPeriods: 3,
          comparisonOperator:
            cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
          alarmDescription: `High duration for ${fn.functionName}`,
          alarmName: `SarkariSaathi-${fn.functionName}-Duration`,
          treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        },
      );

      durationAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

      // Throttle alarm
      const throttleAlarm = new cloudwatch.Alarm(
        this,
        `LambdaThrottleAlarm${index}`,
        {
          metric: fn.metricThrottles({
            statistic: "Sum",
            period: cdk.Duration.minutes(5),
          }),
          threshold: 5,
          evaluationPeriods: 1,
          comparisonOperator:
            cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
          alarmDescription: `Throttling detected for ${fn.functionName}`,
          alarmName: `SarkariSaathi-${fn.functionName}-Throttles`,
          treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        },
      );

      throttleAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));
    });
  }

  private createApiGatewayAlarms(api: apigateway.RestApi) {
    // 5XX error alarm
    const api5xxAlarm = new cloudwatch.Alarm(this, "Api5xxAlarm", {
      metric: api.metricServerError({
        statistic: "Sum",
        period: cdk.Duration.minutes(5),
      }),
      threshold: 10,
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: "High 5XX error rate on API Gateway",
      alarmName: "SarkariSaathi-API-5XX-Errors",
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    api5xxAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));

    // Latency alarm
    const apiLatencyAlarm = new cloudwatch.Alarm(this, "ApiLatencyAlarm", {
      metric: api.metricLatency({
        statistic: "Average",
        period: cdk.Duration.minutes(5),
      }),
      threshold: 3000, // 3 seconds
      evaluationPeriods: 3,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      alarmDescription: "High API latency",
      alarmName: "SarkariSaathi-API-Latency",
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });

    apiLatencyAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));
  }

  private createDynamoDBAlarms(tables: dynamodb.ITable[]) {
    tables.forEach((table, index) => {
      // Throttled requests alarm
      const throttleAlarm = new cloudwatch.Alarm(
        this,
        `DynamoThrottleAlarm${index}`,
        {
          metric: table.metricUserErrors({
            statistic: "Sum",
            period: cdk.Duration.minutes(5),
          }),
          threshold: 10,
          evaluationPeriods: 2,
          comparisonOperator:
            cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
          alarmDescription: `Throttled requests on ${table.tableName}`,
          alarmName: `SarkariSaathi-${table.tableName}-Throttles`,
          treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
        },
      );

      throttleAlarm.addAlarmAction(new actions.SnsAction(this.alarmTopic));
    });
  }
}

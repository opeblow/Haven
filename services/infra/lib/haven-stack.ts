import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/dynamodb";
import * as s3 from "aws-cdk-lib/s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as iam from "aws-cdk-lib/aws-iam";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

export class HavenStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // === DynamoDB Tables ===
    const donationsTable = new dynamodb.Table(this, "DonationsTable", {
      tableName: "haven-donations",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "ttl",
      pointInTimeRecovery: true,
    });

    const volunteersTable = new dynamodb.Table(this, "VolunteersTable", {
      tableName: "haven-volunteers",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
    });

    const recipientsTable = new dynamodb.Table(this, "RecipientsTable", {
      tableName: "haven-recipients",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
    });

    const shiftsTable = new dynamodb.Table(this, "ShiftsTable", {
      tableName: "haven-shifts",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
    });

    const eventsTable = new dynamodb.Table(this, "EventsTable", {
      tableName: "haven-events",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "createdAt", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "ttl",
      pointInTimeRecovery: true,
    });

    const auditTable = new dynamodb.Table(this, "AuditTable", {
      tableName: "haven-audit",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "timestamp", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
    });

    // === S3 Bucket ===
    const documentsBucket = new s3.Bucket(this, "DocumentsBucket", {
      bucketName: `haven-documents-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      lifecycleRules: [
        {
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(90),
            },
          ],
        },
      ],
    });

    // === Cognito ===
    const userPool = new cognito.UserPool(this, "UserPool", {
      userPoolName: "haven-users",
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      standardAttributes: {
        email: { required: true, mutable: true },
        fullname: { required: true, mutable: true },
      },
      mfa: cognito.Mfa.OPTIONAL,
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const userPoolClient = new cognito.UserPoolClient(this, "UserPoolClient", {
      userPool,
      authFlows: {
        userSrp: true,
      },
    });

    // === API Gateway ===
    const api = new apigateway.RestApi(this, "HavenApi", {
      restApiName: "Haven API",
      description: "Autonomous operations for community aid",
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    const health = api.root.addResource("api").addResource("health");
    health.addMethod("GET");

    const donations = api.root.addResource("api").addResource("donations");
    donations.addResource("offer").addMethod("POST");

    const recipients = api.root.addResource("api").addResource("recipients");
    recipients.addResource("request").addMethod("POST");

    const volunteers = api.root.addResource("api").addResource("volunteers");
    volunteers.addResource("inquiry").addMethod("POST");

    const eventsFeed = api.root.addResource("api").addResource("events");
    eventsFeed.addResource("feed").addMethod("GET");

    const stats = api.root.addResource("api").addResource("stats");
    stats.addMethod("GET");

    // === EventBridge ===
    const eventBus = new events.EventBus(this, "HavenEventBus", {
      eventBusName: "haven-events",
    });

    // === CloudWatch ===
    const logGroup = new logs.LogGroup(this, "HavenLogs", {
      logGroupName: "/haven/agents",
      retention: logs.RetentionDays.TWO_WEEKS,
    });

    // === Outputs ===
    new cdk.CfnOutput(this, "ApiUrl", { value: api.url });
    new cdk.CfnOutput(this, "UserPoolId", { value: userPool.userPoolId });
    new cdk.CfnOutput(this, "UserPoolClientId", { value: userPoolClient.userPoolClientId });
    new cdk.CfnOutput(this, "DocumentsBucketName", { value: documentsBucket.bucketName });
    new cdk.CfnOutput(this, "EventBusName", { value: eventBus.eventBusName });
  }
}

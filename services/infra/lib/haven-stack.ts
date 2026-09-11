import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as events from "aws-cdk-lib/aws-events";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

/**
 * Shared mock integration for API methods that are not yet wired to a real
 * backend. The FastAPI agent service is not deployed by this stack yet; wire
 * these methods to a Lambda proxy / HTTP integration once the service exists.
 */
const pendingBackendIntegration = {
  integration: new apigateway.MockIntegration({
    integrationResponses: [{ statusCode: "200" }],
    passthroughBehavior: apigateway.PassthroughBehavior.NEVER,
    requestTemplates: {
      "application/json": "{ \"statusCode\": 200 }",
    },
  }),
};

export class HavenStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // === DynamoDB Tables ===
    // NOTE: the events table uses `created_at` as its sort key to match the
    // Haven DB layer (`haven/db.py`). Keep the two in sync if you rename it.
    const donationsTable = new dynamodb.Table(this, "DonationsTable", {
      tableName: "haven-donations",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "ttl",
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
    });
    donationsTable.addGlobalSecondaryIndex({
      indexName: "status-index",
      partitionKey: { name: "status", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    const volunteersTable = new dynamodb.Table(this, "VolunteersTable", {
      tableName: "haven-volunteers",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
    });
    volunteersTable.addGlobalSecondaryIndex({
      indexName: "status-index",
      partitionKey: { name: "status", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    const recipientsTable = new dynamodb.Table(this, "RecipientsTable", {
      tableName: "haven-recipients",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
    });

    const shiftsTable = new dynamodb.Table(this, "ShiftsTable", {
      tableName: "haven-shifts",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
    });
    shiftsTable.addGlobalSecondaryIndex({
      indexName: "status-index",
      partitionKey: { name: "status", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    const eventsTable = new dynamodb.Table(this, "EventsTable", {
      tableName: "haven-events",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "created_at", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "ttl",
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
    });

    const auditTable = new dynamodb.Table(this, "AuditTable", {
      tableName: "haven-audit",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "timestamp", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
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

    // Create the shared "/api" resource once; re-adding it under the same
    // construct parent for each route caused a CDK "name already exists" error.
    const apiResource = api.root.addResource("api");

    const health = apiResource.addResource("health");
    health.addMethod("GET", pendingBackendIntegration.integration);

    const donations = apiResource.addResource("donations");
    donations.addMethod("GET", pendingBackendIntegration.integration);
    donations.addResource("offer").addMethod("POST", pendingBackendIntegration.integration);

    const recipients = apiResource.addResource("recipients");
    recipients.addMethod("GET", pendingBackendIntegration.integration);
    recipients.addResource("request").addMethod("POST", pendingBackendIntegration.integration);

    const volunteers = apiResource.addResource("volunteers");
    volunteers.addMethod("GET", pendingBackendIntegration.integration);
    volunteers.addResource("inquiry").addMethod("POST", pendingBackendIntegration.integration);

    const eventsFeed = apiResource.addResource("events");
    eventsFeed.addResource("feed").addMethod("GET", pendingBackendIntegration.integration);

    const stats = apiResource.addResource("stats");
    stats.addMethod("GET", pendingBackendIntegration.integration);

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
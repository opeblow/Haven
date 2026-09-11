import * as cdk from "aws-cdk-lib";
import { HavenStack } from "./haven-stack";

const app = new cdk.App();
new HavenStack(app, "HavenStack", {
  description: "Haven — autonomous operations for community aid organizations",
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
});

app.synth();
import { Stack, StackProps, Duration } from "aws-cdk-lib";
import { Construct } from "constructs";
import { ManagedPolicy, Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import {
  Function,
  Code,
  Runtime,
  FunctionUrlAuthType,
} from "aws-cdk-lib/aws-lambda";
import { RetentionDays, FilterPattern } from "aws-cdk-lib/aws-logs";
import { Rule, Schedule } from "aws-cdk-lib/aws-events";
import { LambdaFunction } from "aws-cdk-lib/aws-events-targets";
import { Bucket } from "aws-cdk-lib/aws-s3";
import { Asset } from "aws-cdk-lib/aws-s3-assets";
import { StringParameter } from "aws-cdk-lib/aws-ssm";
import { Topic } from "aws-cdk-lib/aws-sns";
import { EmailSubscription } from "aws-cdk-lib/aws-sns-subscriptions";
import { Alarm, ComparisonOperator } from "aws-cdk-lib/aws-cloudwatch";
import { SnsAction } from "aws-cdk-lib/aws-cloudwatch-actions";
import { join } from "path";

export class CdkStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const iamRoleForLambda = new Role(this, "IamRoleForLambda", {
      roleName: "lambda-role",
      assumedBy: new ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [
        ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole",
        ),
        ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMReadOnlyAccess"),
      ],
    });

    const s3BucketName = StringParameter.valueForStringParameter(
      this,
      "S3_BUCKET_NAME",
    );
    const s3KeyName = StringParameter.valueForStringParameter(
      this,
      "S3_KEY_NAME",
    );

    const lambdaEnv = {
      ENV_NAME: "prod",
      S3_BUCKET_NAME: s3BucketName,
      S3_KEY_NAME: s3KeyName,
    };

    const bundlingAssetLambdaCode = new Asset(this, "BundlingAssetLambdaCode", {
      path: join(__dirname, "../../app"),
      bundling: {
        image: Runtime.PYTHON_3_9.bundlingImage,
        command: [
          "bash",
          "-c",
          [
            "curl -sSL https://install.python-poetry.org | python3 -",
            "/root/.local/bin/poetry export -f requirements.txt --output /asset-output/requirements.txt",
            "pip install -r /asset-output/requirements.txt -t /asset-output",
            "cp -au src /asset-output",
          ].join(" && "),
        ],
        user: "root",
      },
    });

    const webhookHandlerStack = new Function(this, "WebhookHandlerFunction", {
      code: Code.fromBucket(
        bundlingAssetLambdaCode.bucket,
        bundlingAssetLambdaCode.s3ObjectKey,
      ),
      runtime: Runtime.PYTHON_3_9,
      handler: "src/lambda_webhook_handler.lambda_handler",
      environment: lambdaEnv,
      role: iamRoleForLambda,
      timeout: Duration.minutes(5),
      logRetention: RetentionDays.TWO_MONTHS,
    });

    webhookHandlerStack.addFunctionUrl({
      authType: FunctionUrlAuthType.NONE,
    });

    const batchStack = new Function(this, "BatchFunction", {
      code: Code.fromBucket(
        bundlingAssetLambdaCode.bucket,
        bundlingAssetLambdaCode.s3ObjectKey,
      ),
      runtime: Runtime.PYTHON_3_9,
      handler: "src/lambda_batch.lambda_handler",
      environment: lambdaEnv,
      role: iamRoleForLambda,
      timeout: Duration.minutes(5),
      logRetention: RetentionDays.TWO_MONTHS,
    });

    new Rule(this, "DBDBotRule", {
      // cron: 毎日9:30, 21:30(JST) rule: 30 0,12 * * ? *
      schedule: Schedule.cron({
        minute: "30",
        hour: "0,12",
        day: "*",
        month: "*",
        year: "*",
      }),
      targets: [new LambdaFunction(batchStack)],
    });

    const lineIdBucket = Bucket.fromBucketName(
      this,
      s3BucketName,
      s3BucketName,
    );
    lineIdBucket.grantReadWrite(batchStack);
    lineIdBucket.grantReadWrite(webhookHandlerStack);

    const toNotification = StringParameter.valueForStringParameter(
      this,
      "TO_NOTIFICATION",
    );

    const topic = new Topic(this, "DbdTopic");
    topic.addSubscription(new EmailSubscription(toNotification));

    const webhookMetric = webhookHandlerStack.logGroup.addMetricFilter(
      "[ERROR]webhookFilter",
      {
        metricName: "[ERROR]WebhookHandler",
        metricNamespace: "LogMetrics",
        filterPattern: FilterPattern.literal("ERROR"),
      },
    );

    const webhookAlarm = new Alarm(this, "ErrorWebhookHandlerAlarm", {
      comparisonOperator: ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      threshold: 1,
      evaluationPeriods: 1,
      metric: webhookMetric.metric(),
    });
    webhookAlarm.addAlarmAction(new SnsAction(topic));

    const batchMetric = batchStack.logGroup.addMetricFilter(
      "[ERROR]batchFilter",
      {
        metricName: "[ERROR]Batch",
        metricNamespace: "LogMetrics",
        filterPattern: FilterPattern.literal("ERROR"),
      },
    );

    const batchAlarm = new Alarm(this, "ErrorBatchAlarm", {
      comparisonOperator: ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      threshold: 1,
      evaluationPeriods: 1,
      metric: batchMetric.metric(),
    });
    batchAlarm.addAlarmAction(new SnsAction(topic));
  }
}

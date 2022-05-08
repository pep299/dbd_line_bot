import { Stack, StackProps, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Function, Code, Runtime, FunctionUrlAuthType } from 'aws-cdk-lib/aws-lambda';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { Rule, Schedule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { Bucket } from 'aws-cdk-lib/aws-s3';

export class CdkStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const iamRoleForLambda = new Role(this, 'IamRoleForLambda', {
      roleName: 'lambda-role',
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    const lambdaEnv = {
      LINE_CHANNEL_SECRET: process.env.LINE_CHANNEL_SECRET!!,
      LINE_CHANNEL_ACCESS_TOKEN: process.env.LINE_CHANNEL_ACCESS_TOKEN!!,
      S3_BUCKET_NAME: process.env.S3_BUCKET_NAME!!,
      S3_KEY_NAME: process.env.S3_KEY_NAME!!,
      TWITTER_ACCESS_TOKEN: process.env.TWITTER_ACCESS_TOKEN!!,
      TWITTER_ACCESS_TOKEN_SECRET: process.env.TWITTER_ACCESS_TOKEN_SECRET!!,
      TWITTER_CONSUMER_KEY: process.env.TWITTER_CONSUMER_KEY!!,
      TWITTER_CONSUMER_SECRET: process.env.TWITTER_CONSUMER_SECRET!!,
    };

    const webhookHandlerStack = new Function(this, 'WebhookHandlerFunction', {
      code: Code.fromAsset('../webhook_handler', {
        bundling: {
          image: Runtime.PYTHON_3_9.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output',
          ],
        },
      }),
      runtime: Runtime.PYTHON_3_9,
      handler: 'lambda_function.lambda_handler',
      environment: lambdaEnv,
      role: iamRoleForLambda,
      timeout: Duration.minutes(5),
      logRetention: RetentionDays.TWO_MONTHS,
    });

    const url = webhookHandlerStack.addFunctionUrl({
      authType: FunctionUrlAuthType.NONE,
    });

    const batchStack = new Function(this, 'BatchFunction', {
      code: Code.fromAsset('../batch', {
        bundling: {
          image: Runtime.PYTHON_3_9.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output',
          ],
        },
      }),
      runtime: Runtime.PYTHON_3_9,
      handler: 'lambda_function.lambda_handler',
      environment: lambdaEnv,
      role: iamRoleForLambda,
      timeout: Duration.minutes(5),
      logRetention: RetentionDays.TWO_MONTHS,
    });

    const batchInvoke = new Rule(this, 'DBDBotRule', {
      // cron: 毎日9:30, 21:30(JST) rule: 30 0,12 * * ? *
      schedule: Schedule.cron({
        minute: '30',
        hour: '0,12',
        day: '*',
        month: '*',
        year: '*',
      }),
      targets: [
        new LambdaFunction(batchStack),
      ],
    });

    const lineIdBucket = Bucket.fromBucketName(this, 'line-ids', 'line-ids');
    lineIdBucket.grantReadWrite(batchStack);
    lineIdBucket.grantReadWrite(webhookHandlerStack);
  }
}

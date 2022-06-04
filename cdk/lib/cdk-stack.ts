import { Stack, StackProps, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Function, Code, Runtime, FunctionUrlAuthType } from 'aws-cdk-lib/aws-lambda';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { Rule, Schedule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { Asset } from 'aws-cdk-lib/aws-s3-assets';
import { join } from 'path';

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
      ENV_NAME: 'prod',
      S3_BUCKET_NAME: 'line-ids',
      S3_KEY_NAME: 'ids.json',
    };

    const bundlingAssetLambdaCode = new Asset(this, 'BundlingAssetLambdaCode', {
      path: join(__dirname, '../../app'),
      bundling: {
        image: Runtime.PYTHON_3_9.bundlingImage,
        command: [
          'bash',
          '-c',
          [
            'curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python',
            'source $HOME/.poetry/env',
            'poetry export -f requirements.txt --output /asset-output/requirements.txt',
            'pip install -r /asset-output/requirements.txt -t /asset-output',
            'cp -au src /asset-output'
          ].join(' && '),
        ],
        user: 'root',
      }
    });
    const webhookHandlerStack = new Function(this, 'WebhookHandlerFunction', {
      code: Code.fromBucket(bundlingAssetLambdaCode.bucket, bundlingAssetLambdaCode.s3ObjectKey),
      runtime: Runtime.PYTHON_3_9,
      handler: 'src/lambda_webhook_handler.lambda_handler',
      environment: lambdaEnv,
      role: iamRoleForLambda,
      timeout: Duration.minutes(5),
      logRetention: RetentionDays.TWO_MONTHS,
    });

    const url = webhookHandlerStack.addFunctionUrl({
      authType: FunctionUrlAuthType.NONE,
    });

    const batchStack = new Function(this, 'BatchFunction', {
      code: Code.fromBucket(bundlingAssetLambdaCode.bucket, bundlingAssetLambdaCode.s3ObjectKey),
      runtime: Runtime.PYTHON_3_9,
      handler: 'src/lambda_batch.lambda_handler',
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

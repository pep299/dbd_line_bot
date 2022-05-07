import { Stack, StackProps, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Function, Code, Runtime,  } from 'aws-cdk-lib/aws-lambda';

export class CdkStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const iamRoleForBatch = new Role(this, 'IamRoleForBatch', {
      roleName: 'batch-lambda-role',
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ],
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
      environment: {
        TWITTER_ACCESS_TOKEN: '',
        TWITTER_ACCESS_TOKEN_SECRET: '',
        TWITTER_CONSUMER_KEY: '',
        TWITTER_CONSUMER_SECRET: '',
      },
      role: iamRoleForBatch,
      timeout: Duration.minutes(5),
    });
  }
}

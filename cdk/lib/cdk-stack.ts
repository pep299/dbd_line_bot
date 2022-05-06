import { Stack, StackProps, Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { DockerImageFunction, DockerImageCode } from 'aws-cdk-lib/aws-lambda';

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

    const batchStack = new DockerImageFunction(this, 'BatchFunction', {
      code: DockerImageCode.fromImageAsset('../batch'),
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

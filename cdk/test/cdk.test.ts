import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { CdkStack } from "../lib/cdk-stack";

test("snapshot test", () => {
  const app = new cdk.App();
  const stack = new CdkStack(app, "MyTestStack");
  const template = Template.fromStack(stack).toJSON();

  expect(template).toMatchSnapshot();
});

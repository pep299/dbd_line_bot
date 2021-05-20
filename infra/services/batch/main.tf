provider "aws" {}

resource "aws_lambda_function" "batch_function" {}

resource "aws_cloudwatch_event_rule" "DbD_bot" {}
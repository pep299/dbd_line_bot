import logging
import os
import sys
from dataclasses import dataclass

import boto3

logger = logging.getLogger()
logger.setLevel(logging.ERROR)


@dataclass
class Env:
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    OPENAI_API_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    S3_KEY_NAME: str = ""
    TWITTER_BEARER_TOKEN: str = ""


def get_env() -> Env:
    if os.getenv("ENV_NAME", None) == "prod":
        ssm = boto3.client("ssm")
        response = ssm.get_parameters(
            Names=[
                "LINE_CHANNEL_SECRET",
                "LINE_CHANNEL_ACCESS_TOKEN",
                "OPENAI_API_KEY",
                "TWITTER_BEARER_TOKEN",
                "S3_BUCKET_NAME",
                "S3_KEY_NAME",
            ],
        )
        secrets = {store["Name"]: store["Value"] for store in response["Parameters"]}
        return Env(**secrets)
    else:
        return Env(
            S3_BUCKET_NAME=get_env_by_key("S3_BUCKET_NAME"),
            S3_KEY_NAME=get_env_by_key("S3_KEY_NAME"),
            LINE_CHANNEL_SECRET=get_env_by_key("LINE_CHANNEL_SECRET"),
            LINE_CHANNEL_ACCESS_TOKEN=get_env_by_key("LINE_CHANNEL_ACCESS_TOKEN"),
            OPENAI_API_KEY=get_env_by_key("OPENAI_API_KEY"),
            TWITTER_BEARER_TOKEN=get_env_by_key("TWITTER_BEARER_TOKEN"),
        )


def get_env_by_key(key: str) -> str:
    value = os.getenv(key, None)
    if value is None:
        logger.error(f"Specify {key} as environment variable.")
        sys.exit(1)
    return value

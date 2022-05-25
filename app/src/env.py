import os
import sys
import logging

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

IS_PROD = os.getenv('ENV_NAME') is 'prod'

class Env:
    def __init__(
        self,
        LINE_CHANNEL_SECRET = '',
        LINE_CHANNEL_ACCESS_TOKEN = '',
        S3_BUCKET_NAME = '',
        S3_KEY_NAME = '',
        TWITTER_CONSUMER_KEY = '',
        TWITTER_CONSUMER_SECRET = '',
        TWITTER_ACCESS_TOKEN = '',
        TWITTER_ACCESS_TOKEN_SECRET = '',
    ) -> None:
        self.LINE_CHANNEL_SECRET = LINE_CHANNEL_SECRET
        self.LINE_CHANNEL_ACCESS_TOKEN = LINE_CHANNEL_ACCESS_TOKEN
        self.S3_BUCKET_NAME = S3_BUCKET_NAME
        self.S3_KEY_NAME = S3_KEY_NAME
        self.TWITTER_CONSUMER_KEY = TWITTER_CONSUMER_KEY
        self.TWITTER_CONSUMER_SECRET = TWITTER_CONSUMER_SECRET
        self.TWITTER_ACCESS_TOKEN = TWITTER_ACCESS_TOKEN
        self.TWITTER_ACCESS_TOKEN_SECRET = TWITTER_ACCESS_TOKEN_SECRET

def get_env() -> Env:
    return Env(
        LINE_CHANNEL_SECRET = get_env_by_key('LINE_CHANNEL_SECRET'),
        LINE_CHANNEL_ACCESS_TOKEN = get_env_by_key('LINE_CHANNEL_ACCESS_TOKEN'),
        S3_BUCKET_NAME = get_env_by_key('S3_BUCKET_NAME'),
        S3_KEY_NAME = get_env_by_key('S3_KEY_NAME'),
        TWITTER_CONSUMER_KEY = get_env_by_key('TWITTER_CONSUMER_KEY'),
        TWITTER_CONSUMER_SECRET = get_env_by_key('TWITTER_CONSUMER_SECRET'),
        TWITTER_ACCESS_TOKEN = get_env_by_key('TWITTER_ACCESS_TOKEN'),
        TWITTER_ACCESS_TOKEN_SECRET = get_env_by_key('TWITTER_ACCESS_TOKEN_SECRET'),
    )

def get_env_by_key(key: str) -> str:
    value = os.getenv(key, None)
    if value is None:
        logger.error(f'Specify {key} as environment variable.')
        sys.exit(1)
    return value

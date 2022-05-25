import os
import sys
import logging

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
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', None)
    if LINE_CHANNEL_SECRET is None:
        logger.error('Specify LINE_CHANNEL_SECRET as environment variable.')
        sys.exit(1)

    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
    if LINE_CHANNEL_ACCESS_TOKEN is None:
        logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
        sys.exit(1)

    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', None)
    if S3_BUCKET_NAME is None:
        logger.error('Specify S3_BUCKET_NAME as environment variable.')
        sys.exit(1)

    S3_KEY_NAME = os.getenv('S3_KEY_NAME', None)
    if S3_KEY_NAME is None:
        logger.error('Specify S3_KEY_NAME as environment variable.')
        sys.exit(1)

    TWITTER_CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY', None)
    if TWITTER_CONSUMER_KEY is None:
        logger.error('Specify TWITTER_CONSUMER_KEY as environment variable.')
        sys.exit(1)

    TWITTER_CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET', None)
    if TWITTER_CONSUMER_SECRET is None:
        logger.error('Specify TWITTER_CONSUMER_SECRET as environment variable.')
        sys.exit(1)

    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', None)
    if TWITTER_ACCESS_TOKEN is None:
        logger.error('Specify TWITTER_ACCESS_TOKEN as environment variable.')
        sys.exit(1)

    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', None)
    if TWITTER_ACCESS_TOKEN_SECRET is None:
        logger.error('Specify TWITTER_ACCESS_TOKEN_SECRET as environment variable.')
        sys.exit(1)

    return Env(
        LINE_CHANNEL_SECRET,
        LINE_CHANNEL_ACCESS_TOKEN,
        S3_BUCKET_NAME,
        S3_KEY_NAME,
        TWITTER_CONSUMER_KEY,
        TWITTER_CONSUMER_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET,
    )

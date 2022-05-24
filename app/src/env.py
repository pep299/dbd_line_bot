import os
import sys
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Env:
    def __init__(self) -> None:
        self.LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', None)
        if self.LINE_CHANNEL_SECRET is None:
            logger.error('Specify LINE_CHANNEL_SECRET as environment variable.')
            sys.exit(1)

        self.LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
        if self.LINE_CHANNEL_ACCESS_TOKEN is None:
            logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
            sys.exit(1)

        self.S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', None)
        if self.S3_BUCKET_NAME is None:
            logger.error('Specify S3_BUCKET_NAME as environment variable.')
            sys.exit(1)

        self.S3_KEY_NAME = os.getenv('S3_KEY_NAME', None)
        if self.S3_KEY_NAME is None:
            logger.error('Specify S3_KEY_NAME as environment variable.')
            sys.exit(1)

        self.TWITTER_CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY', None)
        if self.TWITTER_CONSUMER_KEY is None:
            logger.error('Specify TWITTER_CONSUMER_KEY as environment variable.')
            sys.exit(1)

        self.TWITTER_CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET', None)
        if self.TWITTER_CONSUMER_SECRET is None:
            logger.error('Specify TWITTER_CONSUMER_SECRET as environment variable.')
            sys.exit(1)

        self.TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', None)
        if self.TWITTER_ACCESS_TOKEN is None:
            logger.error('Specify TWITTER_ACCESS_TOKEN as environment variable.')
            sys.exit(1)

        self.TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', None)
        if self.TWITTER_ACCESS_TOKEN_SECRET is None:
            logger.error('Specify TWITTER_ACCESS_TOKEN_SECRET as environment variable.')
            sys.exit(1)

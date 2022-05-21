import os
import sys
import logging
import json
from datetime import datetime, timedelta, timezone

from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError

import boto3
import tweepy

# loggerの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LINE botの設定
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_access_token is None:
    logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)

# s3の設定
s3 = boto3.resource("s3")
bucket = os.getenv('S3_BUCKET_NAME', None)
key = os.getenv('S3_KEY_NAME', None)
if bucket is None:
    logger.error('Specify S3_BUCKET_NAME as environment variable.')
    sys.exit(1)
if key is None:
    logger.error('Specify S3_KEY_NAME as environment variable.')
    sys.exit(1)

# Twitter APIの設定
TWITTER_CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY', None)
TWITTER_CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET', None)
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', None)
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', None)
if TWITTER_CONSUMER_KEY is None:
    logger.error('Specify TWITTER_CONSUMER_KEY as environment variable.')
    sys.exit(1)
if TWITTER_CONSUMER_SECRET is None:
    logger.error('Specify TWITTER_CONSUMER_SECRET as environment variable.')
    sys.exit(1)
if TWITTER_ACCESS_TOKEN is None:
    logger.error('Specify TWITTER_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
if TWITTER_ACCESS_TOKEN_SECRET is None:
    logger.error('Specify TWITTER_ACCESS_TOKEN_SECRET as environment variable.')
    sys.exit(1)

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_api = tweepy.API(auth)

def lambda_handler(event, context):
    ok_json = {"isBase64Encoded": False,
               "statusCode": 200,
               "headers": {},
               "body": ""}
    error_json = {"isBase64Encoded": False,
                  "statusCode": 500,
                  "headers": {},
                  "body": "Error"}

    obj = s3.Object(bucket, key)
    ids = json.loads(obj.get()['Body'].read())

    def judge_output_dbd_official(status):
        return status.created_at >= datetime.now(timezone.utc) - timedelta(hours=12) and \
            bool(list(filter(lambda x: x in status.full_text, [
                'シュライン・オブ・シークレット',
                '引き換えコード',
                'BP',
                'ブラッドポイント',
                'インデスントシャード',
                'シャード',
                'アップデート'
            ])))

    push_list = list(filter(
        judge_output_dbd_official, twitter_api.user_timeline(user_id='DeadbyBHVR_JP', tweet_mode='extended', include_rts=False)
    ))

    def judge_output_ruby_nea(status):
        return status.created_at >= datetime.now(timezone.utc) - timedelta(hours=12) and \
            bool(list(filter(lambda x: x in status.full_text, [
                '引き換えコード',
                'コード',
            ])))

    push_list += list(filter(
        judge_output_ruby_nea, twitter_api.user_timeline(user_id='Ruby_Nea_', tweet_mode='extended', include_rts=False)
    ))

    for status in push_list:
        messages = []
        messages.append(TextSendMessage(text=status.full_text))
        if bool(status.entities.get('media')):
            messages.append(
                ImageSendMessage(
                    original_content_url=status.entities['media'][0]['media_url_https'],
                    preview_image_url=status.entities['media'][0]['media_url_https'],
                )
            )
        try:
            for sender_id in ids:
                line_bot_api.push_message(sender_id, messages=messages)
        except LineBotApiError as e:
            logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
            for m in e.error.details:
                logger.error("  %s: %s" % (m.property, m.message))
            return error_json

    return ok_json

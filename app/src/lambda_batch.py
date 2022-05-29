import logging
import json
from datetime import datetime, timedelta, timezone
from .env import get_env, IS_PROD, IS_DEV

from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

import boto3
from tweepy import OAuthHandler, API
from tweepy.models import Status

# global変数
logger = None
env = None
line_bot_api = None
s3 = None
twitter_api = None

# loggerの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if IS_PROD or IS_DEV:
    # env取得
    env = get_env()

    # LINE botの設定
    line_bot_api = LineBotApi(env.LINE_CHANNEL_ACCESS_TOKEN)

    # s3の設定
    s3 = boto3.resource("s3")

    # Twitter APIの設定
    auth = OAuthHandler(env.TWITTER_CONSUMER_KEY, env.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(env.TWITTER_ACCESS_TOKEN, env.TWITTER_ACCESS_TOKEN_SECRET)
    twitter_api = API(auth)

def lambda_handler(event, context):
    ok_json = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "body": ""
    }
    error_json = {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": {},
        "body": "Error"
    }
    sender_ids = get_sender_ids(env.S3_BUCKET_NAME, env.S3_KEY_NAME)

    push_list = get_send_message_by_dbd_official()
    push_list += get_send_message_by_ruby_nea()

    return ok_json if send_message(push_list, sender_ids) else error_json

def send_message(push_list: list[Status], sender_ids: list[str]) -> bool:
    raise_error = False
    for status in push_list:
        messages = []
        messages.append(TextSendMessage(text=status.full_text))
        for sender_id in sender_ids:
            try:
                line_bot_api.push_message(sender_id, messages=messages)
            except LineBotApiError as e:
                logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
                for m in e.error.details:
                    logger.error("  %s: %s" % (m.property, m.message))
                raise_error = True

    return not raise_error

def get_sender_ids(bucket :str, key: str) -> list[str]:
    obj = s3.Object(bucket, key)
    return json.loads(obj.get()['Body'].read())

def get_send_message_by_dbd_official() -> list[Status]:
    SCREEN_NAME = 'DeadbyBHVR_JP'
    OUTPUT_FILTER = [
        'シュライン・オブ・シークレット',
        '引き換えコード',
        'BP',
        'ブラッドポイント',
        'インデスントシャード',
        'シャード',
        'アップデート'
    ]
    statuses = get_statuses(SCREEN_NAME)
    return [status for status in statuses if judge_output_status(status, OUTPUT_FILTER)]

def get_send_message_by_ruby_nea() -> list[Status]:
    SCREEN_NAME = 'Ruby_Nea_'
    OUTPUT_FILTER = [
        '引き換えコード',
        'コード',
    ]
    statuses = get_statuses(SCREEN_NAME)
    return [status for status in statuses if judge_output_status(status, OUTPUT_FILTER)]

def get_statuses(screen_name: str) -> list[Status]:
    return twitter_api.user_timeline(screen_name=screen_name, count=20, tweet_mode='extended', exclude_replies=True, include_rts=False)

def judge_output_status(status: Status, filter_list: list) -> bool:
    return status.created_at >= datetime.now(timezone.utc) - timedelta(hours=12) and \
            bool(list(filter(lambda x: x in status.full_text, filter_list)))

import logging
import json
from datetime import datetime, timedelta, timezone
from app.src.env import get_env, IS_PROD

from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError

import boto3
import tweepy

# global変数
logger = None
env = None
line_bot_api = None
s3 = None
twitter_api = None

# loggerの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if IS_PROD:
    # env取得
    env = get_env()

    # LINE botの設定
    line_bot_api = LineBotApi(env.LINE_CHANNEL_ACCESS_TOKEN)

    # s3の設定
    s3 = boto3.resource("s3")

    # Twitter APIの設定
    auth = tweepy.OAuthHandler(env.TWITTER_CONSUMER_KEY, env.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(env.TWITTER_ACCESS_TOKEN, env.TWITTER_ACCESS_TOKEN_SECRET)
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

    obj = s3.Object(env.S3_BUCKET_NAME, env.S3_KEY_NAME)
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
        judge_output_dbd_official, twitter_api.user_timeline(screen_name='DeadbyBHVR_JP', count=20, tweet_mode='extended', exclude_replies=True, include_rts=False)
    ))

    def judge_output_ruby_nea(status):
        return status.created_at >= datetime.now(timezone.utc) - timedelta(hours=12) and \
            bool(list(filter(lambda x: x in status.full_text, [
                '引き換えコード',
                'コード',
            ])))

    push_list += list(filter(
        judge_output_ruby_nea, twitter_api.user_timeline(screen_name='Ruby_Nea_', count=20, tweet_mode='extended', exclude_replies=True, include_rts=False)
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

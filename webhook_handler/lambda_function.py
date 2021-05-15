import os
import sys
import logging
import json

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, JoinEvent, LeaveEvent, TextMessage, TextSendMessage, ImageSendMessage
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
import boto3
import tweepy

# loggerの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LINE botの設定
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    logger.error('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

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
    if "x-line-signature" in event["headers"]:
        signature = event["headers"]["x-line-signature"]
    elif "X-Line-Signature" in event["headers"]:
        signature = event["headers"]["X-Line-Signature"]
    body = event["body"]
    ok_json = {"isBase64Encoded": False,
               "statusCode": 200,
               "headers": {},
               "body": ""}
    error_json = {"isBase64Encoded": False,
                  "statusCode": 500,
                  "headers": {},
                  "body": "Error"}

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            logger.error("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json

    return ok_json

@handler.add(MessageEvent, message=TextMessage)
def message(event):
    if event.message.text == '今週の聖堂':
        status_list = twitter_api.user_timeline(id='DeadbyBHVR_JP', tweet_mode='extended')
        output_list = list(filter(lambda x: 'シュライン・オブ・シークレット' in x.full_text, status_list))

        if not output_list:
            return

        messages = []
        messages.append(TextSendMessage(text=output_list[0].full_text))
        if bool(output_list[0].entities.get('media')):
            messages.append(
                ImageSendMessage(
                    original_content_url=output_list[0].entities['media'][0]['media_url_https'],
                    preview_image_url=output_list[0].entities['media'][0]['media_url_https'],
                )
            )

        line_bot_api.reply_message(event.reply_token, messages=messages)

@handler.add(JoinEvent)
def store_id(event):
    logger.info('参加先id: ' + event.source.sender_id)
    obj = s3.Object(bucket, key)
    ids = json.loads(obj.get()['Body'].read())
    if (event.source.sender_id in ids):
        logger.info('id重複のため書き込まない')
    else:
        ids.append(event.source.sender_id)
        response = obj.put(Body=json.dumps(ids))
        logger.info(response)

@handler.add(LeaveEvent)
def delete_id(event):
    logger.info('退室先id: '+ event.source.sender_id)
    obj = s3.Object(bucket, key)
    ids = json.loads(obj.get()['Body'].read())
    if (event.source.sender_id in ids):
        new_ids = list(filter(lambda x: not x == event.source.sender_id, ids))
        response = obj.put(Body=json.dumps(new_ids))
        logger.info(response)
    else:
        logger.info('idが無いため削除しない')

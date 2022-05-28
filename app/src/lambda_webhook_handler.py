import logging
import json
from app.src.env import IS_PROD, IS_DEV, IS_TEST, get_env

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, JoinEvent, LeaveEvent, TextMessage, TextSendMessage
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
import boto3
import tweepy

# global変数
logger = None
env = None
line_bot_api = None
handler = None
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
    handler = WebhookHandler(env.LINE_CHANNEL_SECRET)

    # s3の設定
    s3 = boto3.resource("s3")

    # Twitter APIの設定
    auth = tweepy.OAuthHandler(env.TWITTER_CONSUMER_KEY, env.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(env.TWITTER_ACCESS_TOKEN, env.TWITTER_ACCESS_TOKEN_SECRET)
    twitter_api = tweepy.API(auth)

if IS_TEST:
    env = get_env()
    # LINE botの設定
    handler = WebhookHandler(env.LINE_CHANNEL_SECRET) # @handler.addがテストスクリプト前に実行されるため定義

def lambda_handler(event, context):
    if "x-line-signature" in event["headers"]:
        signature = event["headers"]["x-line-signature"]
    elif "X-Line-Signature" in event["headers"]:
        signature = event["headers"]["X-Line-Signature"]
    body = event["body"]
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
        status_list = twitter_api.user_timeline(screen_name='DeadbyBHVR_JP', count=50, tweet_mode='extended', exclude_replies=True, include_rts=False)
        output_list = list(filter(lambda x: 'シュライン・オブ・シークレット' in x.full_text, status_list))

        if not output_list:
            return

        messages = []
        messages.append(TextSendMessage(text=output_list[0].full_text))

        line_bot_api.reply_message(event.reply_token, messages=messages)

@handler.add(JoinEvent)
def store_id(event):
    logger.info('参加先id: ' + event.source.sender_id)
    obj = s3.Object(env.S3_BUCKET_NAME, env.S3_KEY_NAME)
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
    obj = s3.Object(env.S3_BUCKET_NAME, env.S3_KEY_NAME)
    ids = json.loads(obj.get()['Body'].read())
    if (event.source.sender_id in ids):
        new_ids = list(filter(lambda x: not x == event.source.sender_id, ids))
        response = obj.put(Body=json.dumps(new_ids))
        logger.info(response)
    else:
        logger.info('idが無いため削除しない')

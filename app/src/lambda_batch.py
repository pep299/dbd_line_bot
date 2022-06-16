import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import boto3
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage
from tweepy import API, OAuth2BearerHandler
from tweepy.models import Status

from .env import get_env

# loggerの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Any, context: Any) -> Dict[str, Any]:
    ok_json = {"isBase64Encoded": False, "statusCode": 200, "headers": {}, "body": ""}
    error_json = {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": {},
        "body": "Error",
    }

    env = get_env()

    sender_ids = get_sender_ids(env.S3_BUCKET_NAME, env.S3_KEY_NAME)

    auth = OAuth2BearerHandler(env.TWITTER_BEARER_TOKEN)
    twitter_api = API(auth)

    push_list = get_send_message_by_dbd_official(twitter_api)
    push_list += get_send_message_by_ruby_nea(twitter_api)

    return (
        ok_json
        if send_message(push_list, sender_ids, env.LINE_CHANNEL_ACCESS_TOKEN)
        else error_json
    )


def send_message(
    push_list: List[Status], sender_ids: List[str], line_channel_access_token: str
) -> bool:
    line_bot_api = LineBotApi(line_channel_access_token)
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


def get_sender_ids(bucket: str, key: str) -> List[str]:
    s3 = boto3.resource("s3")
    obj = s3.Object(bucket, key)
    return list(json.loads(obj.get()["Body"].read()))


def get_send_message_by_dbd_official(twitter_api: API) -> List[Status]:
    SCREEN_NAME = "DeadbyBHVR_JP"
    OUTPUT_FILTER = [
        "シュライン・オブ・シークレット",
        "引き換えコード",
        "BP",
        "ブラッドポイント",
        "インデスントシャード",
        "シャード",
        "アップデート",
        "ログイン",
        "ラインナップ",
    ]
    statuses = get_statuses(twitter_api, SCREEN_NAME)
    return [status for status in statuses if judge_output_status(status, OUTPUT_FILTER)]


def get_send_message_by_ruby_nea(twitter_api: API) -> List[Status]:
    SCREEN_NAME = "Ruby_Nea_"
    OUTPUT_FILTER = [
        "引き換えコード",
        "コード",
    ]
    statuses = get_statuses(twitter_api, SCREEN_NAME)
    return [status for status in statuses if judge_output_status(status, OUTPUT_FILTER)]


def get_statuses(twitter_api: API, screen_name: str) -> List[Status]:
    return list(
        twitter_api.user_timeline(
            screen_name=screen_name,
            count=20,
            tweet_mode="extended",
            exclude_replies=False,
            include_rts=False,
        )
    )


def judge_output_status(status: Status, filter_list: List[str]) -> bool:
    return status.created_at >= datetime.now(timezone.utc) - timedelta(
        hours=12
    ) and bool(list(filter(lambda x: x in status.full_text, filter_list)))

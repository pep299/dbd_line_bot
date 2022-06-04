import os
import json
from logging import INFO, ERROR
from pytest_mock import MockerFixture
from _pytest.logging import LogCaptureFixture
import boto3
from moto import mock_s3
from linebot.models import TextSendMessage
from linebot.models.error import Error, ErrorDetail
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from tweepy.models import Status
from app.src.lambda_webhook_handler import message, lambda_handler, store_id, delete_id
from app.src.env import get_env

def mock_line_bot_api(mocker: MockerFixture):
    return_mock = mocker.Mock()
    mocker.patch("app.src.lambda_webhook_handler.LineBotApi", return_value=return_mock)
    return return_mock

def test_lambda_handler_message(mocker: MockerFixture):
    event = {
        "headers": {
            "x-line-signature": "dummy"
        },
        "body": '{"events":[{"type":"message","message":{"type":"text","text":"今週の聖堂"},"replyToken":"dummy"}]}'
    }
    context = None
    reply_token = "dummy"
    send_message = "今週のシュライン・オブ・シークレットはdummy!"

    # 署名検証を無効にする
    mocker.patch("linebot.SignatureValidator.validate", return_value=True)

    # Twitterへのリクエストをmock
    test_status = Status.parse(None, { 'full_text': send_message })
    status_list = [test_status]
    mocker.patch("app.src.lambda_webhook_handler.API", return_value=mocker.Mock(**{'user_timeline.return_value': status_list}))

    # LINEへのリクエストをmock
    mock_reply_message = mock_line_bot_api(mocker)

    result = lambda_handler(event, context)

    assert result['statusCode'] == 200
    mock_reply_message.reply_message.assert_called_once_with(reply_token, messages=[TextSendMessage(text=send_message)])

def test_line_bot_api_error(mocker: MockerFixture, caplog: LogCaptureFixture):
    event = {
        "headers": {
            "x-line-signature": "dummy"
        },
        "body": ''
    }

    mocker.patch("linebot.WebhookHandler.handle", side_effect=\
            LineBotApiError(400, {}, error=Error(message='invalid id', details=[ErrorDetail(property='error', message='abcde')])))

    result = lambda_handler(event, None)

    assert ('root', ERROR, 'Got exception from LINE Messaging API: invalid id\n') in caplog.record_tuples
    assert ('root', ERROR, '  error: abcde') in caplog.record_tuples
    assert result['statusCode'] == 500

def test_invalid_signature_error(mocker: MockerFixture, caplog: LogCaptureFixture):
    event = {
        "headers": {
            "x-line-signature": "dummy"
        },
        "body": ''
    }

    mocker.patch("linebot.WebhookHandler.handle", side_effect=InvalidSignatureError)

    result = lambda_handler(event, None)

    assert ('root', ERROR, 'Detected invalid signature') in caplog.record_tuples
    assert result['statusCode'] == 500

def test_message_no_shrine(mocker: MockerFixture):
    # Twitterへのリクエストをmock
    status_list = []
    mocker.patch("app.src.lambda_webhook_handler.API", return_value=mocker.Mock(**{'user_timeline.return_value': status_list}))

    # LINEへのリクエストをmock
    mock_reply_message = mock_line_bot_api(mocker)

    message("今週の聖堂", "", get_env())

    mock_reply_message.assert_not_called()

def test_message_other_text(mocker: MockerFixture):
    # LINEへのリクエストをmock
    mock_reply_message = mock_line_bot_api(mocker)

    message("dummy", "", get_env())

    mock_reply_message.assert_not_called()

def setup_mock_s3(mocker: MockerFixture, content: str):
    bucket_name = "test"
    key = "test"
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)
    bucket.create()
    object = s3.Object(bucket_name, key)
    object.put(Body=content.encode('utf-8'))

    os.environ['S3_BUCKET_NAME'] = bucket_name
    os.environ['S3_KEY_NAME'] = key

@mock_s3
def test_lambda_handler_join(mocker: MockerFixture):
    event = {
        "headers": {
            "x-line-signature": "dummy"
        },
        "body": '{"events":[{"type":"join","source":{"type":"group","group_id":"abcde"}}]}'
    }
    context = None

    setup_mock_s3(mocker, '[]')

    # 署名検証を無効にする
    mocker.patch("linebot.SignatureValidator.validate", return_value=True)

    lambda_handler(event, context)

    obj = boto3.resource("s3").Object("test", "test")

    assert json.loads(obj.get()['Body'].read()) == ['abcde']

@mock_s3
def test_join_exist_id(mocker: MockerFixture, caplog: LogCaptureFixture):
    setup_mock_s3(mocker, '["abcde"]')

    store_id("abcde", get_env())

    assert ('root', INFO, 'id重複のため書き込まない') in caplog.record_tuples

@mock_s3
def test_lambda_handler_leave(mocker: MockerFixture):
    event = {
        "headers": {
            "X-Line-Signature": "dummy"
        },
        "body": '{"events":[{"type":"leave","source":{"type":"group","group_id":"abcde"}}]}'
    }
    context = None

    setup_mock_s3(mocker, '["abcde"]')

    # 署名検証を無効にする
    mocker.patch("linebot.SignatureValidator.validate", return_value=True)

    lambda_handler(event, context)

    obj = boto3.resource("s3").Object("test", "test")

    assert json.loads(obj.get()['Body'].read()) == []

@mock_s3
def test_leave_no_ids(mocker: MockerFixture, caplog: LogCaptureFixture):
    setup_mock_s3(mocker, '["fghij"]')

    delete_id("abcde", get_env())

    assert ('root', INFO, 'idが無いため削除しない') in caplog.record_tuples

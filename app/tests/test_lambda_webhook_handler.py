import json
from logging import INFO, ERROR
from pytest_mock import MockerFixture
from _pytest.logging import LogCaptureFixture
import boto3
from moto import mock_s3
from linebot.models import MessageEvent, JoinEvent, LeaveEvent, TextSendMessage
from linebot.models.error import Error, ErrorDetail
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from tweepy.models import Status
from app.src.lambda_webhook_handler import message, lambda_handler, store_id, delete_id
from app.src.env import Env

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
    mocker.patch("app.src.lambda_webhook_handler.twitter_api", mocker.Mock())
    mocker.patch("app.src.lambda_webhook_handler.twitter_api.user_timeline", return_value=status_list)

    # LINEへのリクエストをmock
    mocker.patch("app.src.lambda_webhook_handler.line_bot_api", mocker.Mock())
    mock_reply_message = mocker.patch("app.src.lambda_webhook_handler.line_bot_api.reply_message", return_value=None)

    result = lambda_handler(event, context)

    assert result['statusCode'] == 200
    mock_reply_message.assert_called_once_with(reply_token, messages=[TextSendMessage(text=send_message)])

def test_line_bot_api_error(mocker: MockerFixture, caplog: LogCaptureFixture):
    event = {
        "headers": {
            "x-line-signature": "dummy"
        },
        "body": ''
    }
    mocker.patch("app.src.lambda_webhook_handler.handler.handle", side_effect=\
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
    mocker.patch("app.src.lambda_webhook_handler.handler.handle", side_effect=InvalidSignatureError)
    result = lambda_handler(event, None)
    assert ('root', ERROR, 'Detected invalid signature') in caplog.record_tuples
    assert result['statusCode'] == 500

def test_message_no_shrine(mocker: MockerFixture):
    # Twitterへのリクエストをmock
    status_list = []
    mocker.patch("app.src.lambda_webhook_handler.twitter_api", mocker.Mock())
    mocker.patch("app.src.lambda_webhook_handler.twitter_api.user_timeline", return_value=status_list)
    # LINEへのリクエストをmock
    mocker.patch("app.src.lambda_webhook_handler.line_bot_api", mocker.Mock())
    mock_reply_message = mocker.patch("app.src.lambda_webhook_handler.line_bot_api.reply_message", return_value=None)

    event = MessageEvent(message={"type":"text","text":"今週の聖堂"})
    message(event)

    mock_reply_message.assert_not_called()

def test_message_other_text(mocker: MockerFixture):
    # LINEへのリクエストをmock
    mocker.patch("app.src.lambda_webhook_handler.line_bot_api", mocker.Mock())
    mock_reply_message = mocker.patch("app.src.lambda_webhook_handler.line_bot_api.reply_message", return_value=None)

    event = MessageEvent(message={"type":"text","text":"dummy"})
    message(event)

    mock_reply_message.assert_not_called()

def setup_mock_s3(mocker: MockerFixture, content: str):
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("test")
    bucket.create()
    object = s3.Object("test", "test")
    object.put(Body=content.encode('utf-8'))
    mocker.patch("app.src.lambda_webhook_handler.s3", s3)
    mocker.patch("app.src.lambda_webhook_handler.env", Env(S3_BUCKET_NAME="test", S3_KEY_NAME="test"))

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

    event = JoinEvent(source={"type":"group","group_id":"abcde"})
    store_id(event)

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

    event = LeaveEvent(source={"type":"group","group_id":"abcde"})
    delete_id(event)

    assert ('root', INFO, 'idが無いため削除しない') in caplog.record_tuples

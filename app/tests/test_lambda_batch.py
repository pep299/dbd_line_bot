from datetime import datetime, timedelta, timezone
import pytest
from pytest_mock import MockerFixture
import boto3
from moto import mock_s3
from linebot.models import TextSendMessage
from tweepy.models import Status
from app.src.env import Env
from app.src.lambda_batch import judge_output_status, lambda_handler, get_send_message_by_dbd_official, get_send_message_by_ruby_nea

def setup_mock_s3(mocker: MockerFixture, content: str):
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("test")
    bucket.create()
    object = s3.Object("test", "test")
    object.put(Body=content.encode('utf-8'))
    mocker.patch("app.src.lambda_batch.s3", s3)
    mocker.patch("app.src.lambda_batch.env", Env(S3_BUCKET_NAME="test", S3_KEY_NAME="test"))

@mock_s3
def test_lambda_handler(mocker: MockerFixture):
    setup_mock_s3(mocker, '["abcde"]')

    send_message = "引き換えコード: dummy"

    # Twitterへのリクエストをmock
    test_status = Status.parse(None, { 'full_text': send_message, 'created_at': (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%a %b %d %H:%M:%S %z %Y') })
    status_list = [test_status]
    mocker.patch("app.src.lambda_batch.twitter_api", mocker.Mock())
    mocker.patch("app.src.lambda_batch.twitter_api.user_timeline", return_value=status_list)

    # LINEへのリクエストをmock
    mocker.patch("app.src.lambda_batch.line_bot_api", mocker.Mock())
    mock_push_message = mocker.patch("app.src.lambda_batch.line_bot_api.push_message", return_value=None)

    result = lambda_handler(None, None)

    assert result['statusCode'] == 200
    assert mock_push_message.call_count == 2
    mock_push_message.assert_called_with("abcde", messages=[TextSendMessage(text=send_message)])

def test_no_get_dbd_official(mocker: MockerFixture):
    send_message = "dummy"

    # Twitterへのリクエストをmock
    test_status = Status.parse(None, { 'full_text': send_message, 'created_at': (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%a %b %d %H:%M:%S %z %Y') })
    status_list = [test_status]
    mocker.patch("app.src.lambda_batch.twitter_api", mocker.Mock())
    mocker.patch("app.src.lambda_batch.twitter_api.user_timeline", return_value=status_list)

    result = get_send_message_by_dbd_official()

    assert result == []

def test_no_get_ruby_nea(mocker: MockerFixture):
    send_message = "dummy"

    # Twitterへのリクエストをmock
    test_status = Status.parse(None, { 'full_text': send_message, 'created_at': (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%a %b %d %H:%M:%S %z %Y') })
    status_list = [test_status]
    mocker.patch("app.src.lambda_batch.twitter_api", mocker.Mock())
    mocker.patch("app.src.lambda_batch.twitter_api.user_timeline", return_value=status_list)

    result = get_send_message_by_ruby_nea()

    assert result == []

@pytest.mark.parametrize("input,expected", [
    (datetime(2022, 2, 22, 0, 59, 59, 999999, tzinfo=timezone.utc), False),
    (datetime(2022, 2, 22, 1, 00, 00, 000000, tzinfo=timezone.utc), True),
])
@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_date_filter_judge_output_status(mocker: MockerFixture, input, expected):
    filters = ['test']
    test_status = Status.parse(None, { 'full_text': 'test!', 'created_at': input.strftime('%a %b %d %H:%M:%S %z %Y') })

    result = judge_output_status(test_status, filters)
    assert expected == result

@pytest.mark.parametrize("filters,text,expected", [
    (['引き換えコード'], 'コード', False),
    (['コード'], '引き換えコード', True)
])
def test_str_filter_judge_output_status(filters, text, expected):
    test_status = Status.parse(None, { 'full_text': text, 'created_at': datetime.now(timezone.utc).strftime('%a %b %d %H:%M:%S %z %Y') })
    result = judge_output_status(test_status, filters)
    assert expected == result

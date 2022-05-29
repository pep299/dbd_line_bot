from datetime import datetime, timezone
from logging import ERROR
import pytest
from pytest_mock import MockerFixture
from _pytest.logging import LogCaptureFixture
import boto3
from moto import mock_s3
from linebot.models import TextSendMessage
from linebot.models.error import Error, ErrorDetail
from linebot.exceptions import LineBotApiError
from tweepy.models import Status
from app.src.env import Env
from app.src.lambda_batch import judge_output_status, lambda_handler, get_send_message_by_dbd_official, get_send_message_by_ruby_nea, send_message

def setup_mock_s3(mocker: MockerFixture, content: str):
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("test")
    bucket.create()
    object = s3.Object("test", "test")
    object.put(Body=content.encode('utf-8'))
    mocker.patch("app.src.lambda_batch.s3", s3)
    mocker.patch("app.src.lambda_batch.env", Env(S3_BUCKET_NAME="test", S3_KEY_NAME="test"))

def setup_mock_twitter_api(mocker: MockerFixture, send_message: str, created_at: str):
    test_status = Status.parse(None, { 'full_text': send_message, 'created_at': created_at })
    status_list = [test_status]
    mocker.patch("app.src.lambda_batch.twitter_api", mocker.Mock())
    mocker.patch("app.src.lambda_batch.twitter_api.user_timeline", return_value=status_list)

@mock_s3
@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_lambda_handler(mocker: MockerFixture):
    setup_mock_s3(mocker, '["abcde"]')

    send_message = "引き換えコード: dummy"
    created_at = 'Tue Feb 22 13:00:00 +0000 2022'

    # Twitterへのリクエストをmock
    setup_mock_twitter_api(mocker, send_message, created_at)

    # LINEへのリクエストをmock
    mocker.patch("app.src.lambda_batch.line_bot_api", mocker.Mock())
    mock_push_message = mocker.patch("app.src.lambda_batch.line_bot_api.push_message", return_value=None)

    result = lambda_handler(None, None)

    assert result['statusCode'] == 200
    assert mock_push_message.call_count == 2
    mock_push_message.assert_called_with("abcde", messages=[TextSendMessage(text=send_message)])

def test_line_bot_api_error(mocker: MockerFixture, caplog: LogCaptureFixture):
    push_list = [Status.parse(None, { 'full_text': '' })]
    sender_ids = ['abcde']
    mocker.patch("app.src.lambda_batch.line_bot_api", mocker.Mock())
    mocker.patch("app.src.lambda_batch.line_bot_api.push_message", side_effect=\
            LineBotApiError(400, {}, error=Error(message='invalid id', details=[ErrorDetail(property='error', message='abcde')])))
    result = send_message(push_list, sender_ids)
    assert ('root', ERROR, 'Got exception from LINE Messaging API: invalid id\n') in caplog.record_tuples
    assert ('root', ERROR, '  error: abcde') in caplog.record_tuples
    assert result == False

@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_no_get_dbd_official(mocker: MockerFixture):
    send_message = "dummy"
    created_at = 'Tue Feb 22 13:00:00 +0000 2022'

    # Twitterへのリクエストをmock
    setup_mock_twitter_api(mocker, send_message, created_at)

    result = get_send_message_by_dbd_official()

    assert result == []

@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_no_get_ruby_nea(mocker: MockerFixture):
    send_message = "dummy"
    created_at = 'Tue Feb 22 13:00:00 +0000 2022'

    # Twitterへのリクエストをmock
    setup_mock_twitter_api(mocker, send_message, created_at)

    result = get_send_message_by_ruby_nea()

    assert result == []

@pytest.mark.parametrize("input,expected", [
    ('Tue Feb 22 00:59:59 +0000 2022', False),
    ('Tue Feb 22 01:00:00 +0000 2022', True),
])
@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_date_filter_judge_output_status(mocker: MockerFixture, input, expected):
    filters = ['test']
    test_status = Status.parse(None, { 'full_text': 'test!', 'created_at': input })

    result = judge_output_status(test_status, filters)

    assert expected == result

@pytest.mark.parametrize("filters,text,expected", [
    (['引き換えコード'], 'コード', False),
    (['コード'], '引き換えコード', True)
])
@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_str_filter_judge_output_status(filters, text, expected):
    test_status = Status.parse(None, { 'full_text': text, 'created_at': 'Tue Feb 22 13:00:00 +0000 2022' })
    result = judge_output_status(test_status, filters)
    assert expected == result

import os
from datetime import datetime, timezone
from logging import ERROR
from typing import List

import boto3
import pytest
from _pytest.logging import LogCaptureFixture
from app.src.lambda_batch import (
    get_send_message_by_dbd_official,
    get_send_message_by_ruby_nea,
    judge_output_status,
    lambda_handler,
    send_message,
)
from aws_lambda_typing.context import Context
from aws_lambda_typing.events import EventBridgeEvent
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage
from linebot.models.error import Error, ErrorDetail
from moto import mock_s3
from pytest_mock import MockerFixture
from tweepy.models import Status


def setup_mock_s3(content: str) -> None:
    bucket_name = "test"
    key = "test"
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)
    bucket.create()
    object = s3.Object(bucket_name, key)
    object.put(Body=content.encode("utf-8"))

    os.environ["S3_BUCKET_NAME"] = bucket_name
    os.environ["S3_KEY_NAME"] = key


def setup_mock_twitter_api(
    mocker: MockerFixture, send_message: str, created_at: str
) -> None:
    test_status = Status.parse(
        None, {"full_text": send_message, "created_at": created_at}
    )
    status_list = [test_status]
    mocker.patch(
        "app.src.lambda_batch.API",
        return_value=mocker.Mock(**{"user_timeline.return_value": status_list}),
    )


@mock_s3
@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_lambda_handler(mocker: MockerFixture) -> None:
    setup_mock_s3('["abcde"]')

    send_message = "引き換えコード: dummy"
    created_at = "Tue Feb 22 13:00:00 +0000 2022"

    # Twitterへのリクエストをmock
    test_status = Status.parse(
        None, {"full_text": send_message, "created_at": created_at}
    )
    status_list = [test_status]
    mocker.patch(
        "app.src.lambda_batch.API",
        return_value=mocker.Mock(**{"user_timeline.return_value": status_list}),
    )

    # LINEへのリクエストをmock
    mock_line_bot_api = mocker.Mock()
    mocker.patch("app.src.lambda_batch.LineBotApi", return_value=mock_line_bot_api)

    result = lambda_handler(make_event(), Context())

    assert result["statusCode"] == 200
    assert mock_line_bot_api.push_message.call_count == 2
    mock_line_bot_api.push_message.assert_called_with(
        "abcde", messages=[TextSendMessage(text=send_message)]
    )


def make_event() -> EventBridgeEvent:
    return EventBridgeEvent(
        {
            "version": "",
            "id": "",
            "detail-type": "",
            "source": "",
            "account": "",
            "time": "",
            "region": "",
            "resources": [],
            "detail": {},
        }
    )


def test_line_bot_api_error(mocker: MockerFixture, caplog: LogCaptureFixture) -> None:
    push_list = [Status.parse(None, {"full_text": ""})]
    sender_ids = ["abcde"]

    line_bot_exception = LineBotApiError(
        400,
        {},
        error=Error(
            message="invalid id",
            details=[ErrorDetail(property="error", message="abcde")],
        ),
    )
    mocker.patch(
        "app.src.lambda_batch.LineBotApi",
        return_value=mocker.Mock(**{"push_message.side_effect": line_bot_exception}),
    )

    result = send_message(push_list, sender_ids, "")

    assert (
        "root",
        ERROR,
        "Got exception from LINE Messaging API: invalid id\n",
    ) in caplog.record_tuples
    assert ("root", ERROR, "  error: abcde") in caplog.record_tuples
    assert result is False


@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_no_get_dbd_official(mocker: MockerFixture) -> None:
    send_message = "dummy"
    created_at = "Tue Feb 22 13:00:00 +0000 2022"

    # Twitterへのリクエストをmock
    test_status = Status.parse(
        None, {"full_text": send_message, "created_at": created_at}
    )
    status_list = [test_status]
    mock = mocker.Mock(**{"user_timeline.return_value": status_list})

    result = get_send_message_by_dbd_official(mock)

    assert result == []


@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_no_get_ruby_nea(mocker: MockerFixture) -> None:
    send_message = "dummy"
    created_at = "Tue Feb 22 13:00:00 +0000 2022"

    # Twitterへのリクエストをmock
    test_status = Status.parse(
        None, {"full_text": send_message, "created_at": created_at}
    )
    status_list = [test_status]
    mock = mocker.Mock(**{"user_timeline.return_value": status_list})

    result = get_send_message_by_ruby_nea(mock)

    assert result == []


@pytest.mark.parametrize(
    "input,expected",
    [
        ("Tue Feb 22 00:59:59 +0000 2022", False),
        ("Tue Feb 22 01:00:00 +0000 2022", True),
    ],
)
@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_date_filter_judge_output_status(input: str, expected: bool) -> None:
    filters = ["test"]
    test_status = Status.parse(None, {"full_text": "test!", "created_at": input})

    result = judge_output_status(test_status, filters)

    assert expected == result


@pytest.mark.parametrize(
    "filters,text,expected", [(["引き換えコード"], "コード", False), (["コード"], "引き換えコード", True)]
)
@pytest.mark.freeze_time(datetime(2022, 2, 22, 13, 00, 00, 000000, tzinfo=timezone.utc))
def test_str_filter_judge_output_status(
    filters: List[str], text: str, expected: bool
) -> None:
    test_status = Status.parse(
        None, {"full_text": text, "created_at": "Tue Feb 22 13:00:00 +0000 2022"}
    )
    result = judge_output_status(test_status, filters)
    assert expected == result

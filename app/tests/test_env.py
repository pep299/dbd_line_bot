import os
from logging import ERROR
import pytest
from _pytest.logging import LogCaptureFixture
from app.src.env import Env, get_env, get_env_by_key

@pytest.fixture
def set_env():
    os.environ['LINE_CHANNEL_SECRET'] = 'lcs'
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'lcat'
    os.environ['S3_BUCKET_NAME'] = 's3bn'
    os.environ['S3_KEY_NAME'] = 's3kn'
    os.environ['TWITTER_CONSUMER_KEY'] = 'tck'
    os.environ['TWITTER_CONSUMER_SECRET'] = 'tcs'
    os.environ['TWITTER_ACCESS_TOKEN'] = 'tat'
    os.environ['TWITTER_ACCESS_TOKEN_SECRET'] = 'tats'

def test_get_env(set_env):
    expected = Env(
        LINE_CHANNEL_SECRET = 'lcs',
        LINE_CHANNEL_ACCESS_TOKEN = 'lcat',
        S3_BUCKET_NAME = 's3bn',
        S3_KEY_NAME = 's3kn',
        TWITTER_CONSUMER_KEY = 'tck',
        TWITTER_CONSUMER_SECRET = 'tcs',
        TWITTER_ACCESS_TOKEN = 'tat',
        TWITTER_ACCESS_TOKEN_SECRET = 'tats',
    )
    assert vars(get_env()) == vars(expected)

def test_then_no_key_env(caplog: LogCaptureFixture):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        get_env_by_key('TEST')
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    assert ('root', ERROR, 'Specify TEST as environment variable.') in caplog.record_tuples

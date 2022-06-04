import os
from logging import ERROR
import pytest
from _pytest.logging import LogCaptureFixture
import boto3
from moto import mock_ssm
from app.src.env import Env, get_env, get_env_by_key

@pytest.fixture
def set_env():
    os.environ['LINE_CHANNEL_SECRET'] = 'lcs'
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'lcat'
    os.environ['S3_BUCKET_NAME'] = 's3bn'
    os.environ['S3_KEY_NAME'] = 's3kn'
    os.environ['TWITTER_BEARER_TOKEN'] = 'tbt'

def test_get_env(set_env):
    expected = Env(
        LINE_CHANNEL_SECRET = 'lcs',
        LINE_CHANNEL_ACCESS_TOKEN = 'lcat',
        S3_BUCKET_NAME = 's3bn',
        S3_KEY_NAME = 's3kn',
        TWITTER_BEARER_TOKEN = 'tbt',
    )
    assert vars(get_env()) == vars(expected)

@mock_ssm
def test_get_env_prod(set_env):
    os.environ['ENV_NAME'] = 'prod'

    ssm = boto3.client('ssm')
    ssm.put_parameter(Name='LINE_CHANNEL_SECRET', Value='ssm_lcs')
    ssm.put_parameter(Name='LINE_CHANNEL_ACCESS_TOKEN', Value='ssm_lcat')
    ssm.put_parameter(Name='TWITTER_BEARER_TOKEN', Value='ssm_tbt')

    expected = Env(
        LINE_CHANNEL_SECRET = 'ssm_lcs',
        LINE_CHANNEL_ACCESS_TOKEN = 'ssm_lcat',
        S3_BUCKET_NAME = 's3bn',
        S3_KEY_NAME = 's3kn',
        TWITTER_BEARER_TOKEN = 'ssm_tbt',
    )
    assert vars(get_env()) == vars(expected)
    del os.environ['ENV_NAME']

def test_then_no_key_env(caplog: LogCaptureFixture):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        get_env_by_key('TEST')
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    assert ('root', ERROR, 'Specify TEST as environment variable.') in caplog.record_tuples

"""
Copyright https://gist.github.com/alexcasalboni/a545b68ee164b165a74a20a5fee9d133
"""
from typing import Any, Dict


LambdaDict = Dict[str, Any]


class LambdaClientContextMobileClient(object):
    app_package_name: str
    app_title: str
    app_version_code: str
    app_version_name: str
    installation_id: str


class LambdaClientContext(object):
    client: LambdaClientContextMobileClient
    custom: LambdaDict
    env: LambdaDict


class LambdaCognitoIdentity(object):
    cognito_identity_id: str
    cognito_identity_pool_id: str


class LambdaContext(object):
    aws_request_id: str
    client_context: LambdaClientContext
    function_name: str
    function_version: str
    identity: LambdaCognitoIdentity
    invoked_function_arn: str
    log_group_name: str
    log_stream_name: str
    memory_limit_in_mb: int

    @staticmethod
    def get_remaining_time_in_millis() -> int:
        return 0

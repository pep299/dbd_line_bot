from typing import Dict, List, TypedDict

EventBridgeEvent = TypedDict(
    "EventBridgeEvent",
    {
        "version": str,
        "id": str,
        "detail-type": str,
        "source": str,
        "account": str,
        "time": str,
        "region": str,
        "resources": List[str],
        "detail": Dict,
    },
)


class LambdaContext(TypedDict):
    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: str
    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    identity: object
    client_context: object


class LambdaResponse(TypedDict):
    isBase64Encoded: bool
    statusCode: int
    headers: Dict
    body: str

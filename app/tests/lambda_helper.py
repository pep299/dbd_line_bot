from app.src.lambda_types import EventBridgeEvent, LambdaContext


def make_context() -> LambdaContext:
    return LambdaContext(
        {
            "function_name": "",
            "function_version": "",
            "invoked_function_arn": "",
            "memory_limit_in_mb": "",
            "aws_request_id": "",
            "log_group_name": "",
            "log_stream_name": "",
            "identity": {},
            "client_context": {},
        }
    )

def make_event_bridge_event() -> EventBridgeEvent:
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
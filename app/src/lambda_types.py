from typing import Dict, TypedDict


class LambdaResponse(TypedDict):
    isBase64Encoded: bool
    statusCode: int
    headers: Dict
    body: str

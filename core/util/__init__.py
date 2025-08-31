from pydantic import BaseModel, ConfigDict, TypeAdapter
from typing import Any
import json
import uuid
import os

RequestId = str | int | float

class ErrorDetails(BaseModel):
    code: int
    message: str
    data: Any | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)


class ErrorResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: RequestId | None
    error: ErrorDetails

    model_config = ConfigDict(extra="forbid", frozen=True)


class SuccessResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: RequestId
    result: Any

    model_config = ConfigDict(extra="forbid", frozen=True)


Response = SuccessResponse | ErrorResponse
ResponseTypeAdapter = TypeAdapter(Response | list[Response])
ResponseTypeAdapterWs = TypeAdapter(Any)

def handle_json(response: Any):
    if isinstance(response, dict):
        if "error" in response:
            response = ErrorResponse.model_validate(response)
        else:
            response = SuccessResponse.model_validate(response)
    if isinstance(response, list):
        response = [handle_json(item) for item in response]

    return ResponseTypeAdapter.dump_json(response, by_alias=True)

def handle_json_ws(response: Any):
    return ResponseTypeAdapterWs.dump_json(response, by_alias=True)


def generate_tlid():
    return str(uuid.uuid4())[:8]
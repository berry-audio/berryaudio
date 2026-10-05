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

def format_position(ms):
    ms = ms or 0
    seconds = int(ms // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"

def format_codec(fmt):
    """Return the short codec abbreviation, or the original string if unknown."""
    CODEC_NAMES = {
        "DSD (Direct Stream Digital), least significant bit first, planar": "DSD",
        "Uncompressed 24-bit PCM audio": "PCM",
        "Uncompressed 16-bit PCM audio": "PCM",
        "MPEG-1 Layer 3 (MP3)": "MP3",
        "MPEG-1 Layer 2 (MP2)": "MP2",
        "MPEG-4 AAC": "AAC",
        "MPEG-2 AAC": "AAC",
        "Free Lossless Audio Codec (FLAC)": "FLAC",
        "Opus (low-latency lossy audio codec)": "OPUS",
        "opus": "OPUS",
        "Ogg Opus (Opus audio in Ogg container)": "OPUS",
        "Ogg Vorbis (lossy audio codec)": "OGG",
    }
    if not fmt:
        return ""
    return CODEC_NAMES.get(fmt, fmt)

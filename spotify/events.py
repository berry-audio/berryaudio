#!/usr/bin/env python3
import requests
import os

JSONRPC_ENDPOINT = "http://localhost:8080/rpc" 

event = dict(os.environ)
payload = {
        "jsonrpc": "2.0",
        "method": "spotify.message",
        "params": { "event": event },
        "id": 1
    }
requests.get(JSONRPC_ENDPOINT, json=payload)

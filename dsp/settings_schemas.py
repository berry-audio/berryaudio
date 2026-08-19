BACKEND_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "camilla_host": {"type": "string", "minLength": 1},
        "camilla_port": {
            "type": "integer",
        },
        "bind_address": {"type": "string", "minLength": 1},
        "port": {
            "type": "integer",
        },
        "ssl_certificate": {"type": ["string", "null"], "minLength": 1},
        "ssl_private_key": {"type": ["string", "null"], "minLength": 1},
        "gui_config_file": {"type": ["string", "null"], "minLength": 1},
        "config_dir": {"type": "string", "minLength": 1},
        "coeff_dir": {"type": "string", "minLength": 1},
        "default_config": {"type": ["string", "null"], "minLength": 1},
        "statefile_path": {"type": ["string", "null"], "minLength": 1},
        "log_file": {"type": ["string", "null"], "minLength": 1},
        "on_set_active_config": {"type": ["string", "null"], "minLength": 1},
        "on_get_active_config": {"type": ["string", "null"], "minLength": 1},
        "supported_capture_types": {
            "type": ["array", "null"],
            "items": {"type": "string", "minLength": 1},
        },
        "supported_playback_types": {
            "type": ["array", "null"],
            "items": {"type": "string", "minLength": 1},
        },
    },
    "required": [
        "camilla_host",
        "camilla_port",
        "bind_address",
        "port",
        "config_dir",
        "coeff_dir",
    ],
}

GUI_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "page_title": {"type": "string", "minLength": 1},
        "hide_capture_samplerate": {"type": "boolean"},
        "hide_silence": {"type": "boolean"},
        "hide_capture_device": {"type": "boolean"},
        "hide_playback_device": {"type": "boolean"},
        "hide_multithreading": {"type": "boolean"},
        "apply_config_automatically": {"type": "boolean"},
        "save_config_automatically": {"type": "boolean"},
        "status_update_interval": {"type": "integer", "minValue": 1},
        "volume_range": {"type": "number", "exclusiveMinimum": 0, "maxValue": 200},
        "volume_max": {"type": "integer", "minValue": -100, "maxValue": 50},
        "custom_shortcuts": {
            "type": ["array", "null"],
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string"},
                    "description": {"type": "string"},
                    "shortcuts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "config_elements": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "path": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "minLength": 1,
                                            },
                                            "reverse": {"type": ["boolean", "null"]},
                                        },
                                        "required": ["path"],
                                    },
                                },
                                "range_from": {"type": "number"},
                                "range_to": {"type": "number"},
                                "step": {"type": "number", "exclusiveMinimum": 0},
                                "type": {
                                    "type": ["string", "null"],
                                    "enum": ["boolean", "number"],
                                },
                            },
                            "if": {"properties": {"type": {"const": "number"}}},
                            "then": {"required": ["range_from", "range_to", "step"]},
                            "required": ["name", "config_elements"],
                        },
                    },
                },
                "required": ["section", "shortcuts"],
            },
        },
    },
    "required": [],
}

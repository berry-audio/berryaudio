import argparse
import logging
import ssl

import camilladsp
from aiohttp import web
from camilladsp_plot import VERSION as plot_version
from camilladsp_plot.validate_config import CamillaValidator

from backend.routes import setup_routes, setup_static_routes
from backend.settings import CONFIG_PATH, get_config
from backend.version import VERSION
from backend.views import version_string

LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]

# logging.info("info")
# logging.debug("debug")
# logging.warning("warning")
# logging.error("error")


def build_app(backend_config):
    app = web.Application(client_max_size=1024**3)  # set max upload file size to 1GB
    app["config_dir"] = backend_config["config_dir"]
    app["coeff_dir"] = backend_config["coeff_dir"]
    app["default_config"] = backend_config["default_config"]
    app["statefile_path"] = backend_config["statefile_path"]
    app["log_file"] = backend_config["log_file"]
    app["on_set_active_config"] = backend_config["on_set_active_config"]
    app["on_get_active_config"] = backend_config["on_get_active_config"]
    app["supported_capture_types"] = backend_config["supported_capture_types"]
    app["supported_playback_types"] = backend_config["supported_playback_types"]
    app["can_update_active_config"] = backend_config["can_update_active_config"]
    app["gui_config_file"] = backend_config["gui_config_file"]
    setup_routes(app)
    setup_static_routes(app)

    app["CAMILLA"] = camilladsp.CamillaClient(
        backend_config["camilla_host"], backend_config["camilla_port"]
    )
    app["STATUSCACHE"] = {
        "backend_version": version_string(VERSION),
        "py_cdsp_version": version_string(app["CAMILLA"].versions.library()),
        "py_cdsp_plot_version": plot_version,
        "backends": [],
        "playback_devices": {},
        "capture_devices": {},
        "labels": {"playback": None, "capture": None},
    }
    app["STORE"] = {
        "reconnect_thread": None,
        "cache_time": 0,
    }

    camillavalidator = CamillaValidator()
    if backend_config["supported_capture_types"] is not None:
        camillavalidator.set_supported_capture_types(
            backend_config["supported_capture_types"]
        )
    if backend_config["supported_playback_types"] is not None:
        camillavalidator.set_supported_playback_types(
            backend_config["supported_playback_types"]
        )
    app["VALIDATOR"] = camillavalidator
    return app


def main():
    parser = argparse.ArgumentParser(
        prog="python main.py", description="Backend for the CamillaDSP web GUI"
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Provide a path to a backend config file to use instead of the default",
        default=CONFIG_PATH,
    )
    parser.add_argument(
        "-l", "--log-level", help="Logging level", choices=LOG_LEVELS, default="WARNING"
    )
    parser.add_argument(
        "-a",
        "--aiohttp-log-level",
        help="AIOHTTP logging level",
        choices=LOG_LEVELS,
        default="WARNING",
    )

    args = parser.parse_args()

    logging.getLogger("aiohttp").setLevel(getattr(logging, args.aiohttp_log_level))
    logging.getLogger("root").setLevel(getattr(logging, args.log_level))

    config = get_config(args.config)

    app = build_app(config)
    if config.get("ssl_certificate"):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(
            config["ssl_certificate"], keyfile=config.get("ssl_private_key")
        )
    else:
        ssl_context = None
    web.run_app(
        app, host=config["bind_address"], port=config["port"], ssl_context=ssl_context
    )


if __name__ == "__main__":
    main()

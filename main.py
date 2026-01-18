import asyncio
import asyncio_glib
import argparse
import logging
import signal
import gbulb
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstPbutils", "1.0")

from core.core import Core
from core.actor import Actor
from core.logger import setup_logging
from gi.repository import GLib, Gst

asyncio.set_event_loop_policy(asyncio_glib.GLibEventLoopPolicy())

USE_GBULB = False
if USE_GBULB:
    gbulb.install()

logger = None


async def async_main(verbose=False):
    global logger
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logging(log_level).getChild("core")

    Gst.init(None)

    core = Core()
    extensions = [
        "config",
        "system",
        "mixer",
        "tracklist",
        "web",
        "radio",
        "source",
        "spotify",
        "shairportsync",
        "bluetooth",
        "local",
        "search",
        "storage",
        "playlist",
        "playback",
        "network",
        "snapcast",
    ]
    await core.load_extensions_by_name(extensions)

    welcome()
    logger.info("System started. Press Ctrl+C to exit.")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    try:
        await stop_event.wait()
    finally:
        logger.warning("Stopping extensions")
        await core.stop_all()
        logger.info("Extensions stopped cleanly")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()
    try:
        asyncio.run(async_main(args.verbose))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


def welcome():
    banner = r"""
    ██████╗░███████╗██████╗░██████╗░██╗░░░██╗  ░█████╗░██╗░░░██╗██████╗░██╗░█████╗░
    ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗░██╔╝  ██╔══██╗██║░░░██║██╔══██╗██║██╔══██╗
    ██████╦╝█████╗░░██████╔╝██████╔╝░╚████╔╝░  ███████║██║░░░██║██║░░██║██║██║░░██║
    ██╔══██╗██╔══╝░░██╔══██╗██╔══██╗░░╚██╔╝░░  ██╔══██║██║░░░██║██║░░██║██║██║░░██║
    ██████╦╝███████╗██║░░██║██║░░██║░░░██║░░░  ██║░░██║╚██████╔╝██████╔╝██║╚█████╔╝
    ╚═════╝░╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░  ╚═╝░░╚═╝░╚═════╝░╚═════╝░╚═╝░╚════╝░
    *** Welcome to Berry Audio by Varun Gujjar! ***
    *** Hi-Fi audio streaming and rendering platform with a python backend server and react frontend. ***
    """
    print(banner)

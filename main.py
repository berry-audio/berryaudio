import asyncio
import asyncio_glib
import argparse
import logging
import signal
import gbulb
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstPbutils", "1.0")

from version import __version__
from core.core import Core
from core.logger import setup_logging
from gi.repository import Gst

asyncio.set_event_loop_policy(asyncio_glib.GLibEventLoopPolicy())

USE_GBULB = False
if USE_GBULB:
    gbulb.install()

logger = None


async def async_main(verbose=False):
    welcome()

    global logger

    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logging(log_level).getChild("core")

    Gst.init(None)

    core = Core()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            logger.warning("Signal handlers are not supported")

    try:
        await core.load_extensions()
        logger.info("System started. Press Ctrl+C to exit.")
        await stop_event.wait()

    finally:
        logger.warning("Stopping extensions")

        try:
            await core.stop_all()
        except Exception:
            logger.exception("Error during extension shutdown")

        logger.debug("Extensions stopped cleanly")
        current = asyncio.current_task()
        pending = [
            task
            for task in asyncio.all_tasks()
            if task is not current and not task.done()
        ]

        if pending:
            logger.warning(
                "%d tasks still alive; attempting to cancel...",
                len(pending),
            )

            for task in pending:
                logger.debug(
                    "Pending: %s | %s",
                    task.get_name(),
                    task.get_coro(),
                )
                task.cancel()

            await asyncio.gather(
                *pending,
                return_exceptions=True,
            )

        logger.info("Berryaudio Shutdown complete")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    try:
        asyncio.run(async_main(args.verbose))
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass


def welcome():
    banner = f"""
    ██████╗░███████╗██████╗░██████╗░██╗░░░██╗  ░█████╗░██╗░░░██╗██████╗░██╗░█████╗░
    ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗░██╔╝  ██╔══██╗██║░░░██║██╔══██╗██║██╔══██╗
    ██████╦╝█████╗░░██████╔╝██████╔╝░╚████╔╝░  ███████║██║░░░██║██║░░██║██║██║░░██║
    ██╔══██╗██╔══╝░░██╔══██╗██╔══██╗░░╚██╔╝░░  ██╔══██║██║░░░██║██║░░██║██║██║░░██║
    ██████╦╝███████╗██║░░██║██║░░██║░░░██║░░░  ██║░░██║╚██████╔╝██████╔╝██║╚█████╔╝
    ╚═════╝░╚══════╝╚═╝░░╚═╝╚═╝░░░░░░░░░░░░░  ╚═╝░░╚═╝░╚═════╝░╚═════╝░╚═╝░░╚════╝░

    *** Welcome to Berry Audio by Varun Gujjar ***
    *** Hi-Fi audio streaming and rendering platform ***
    *** Version {__version__} ***
    *** Support: https://buymeacoffee.com/varungujjar ***
    """

    print(banner)


if __name__ == "__main__":
    main()

import logging, colorlog
from colorlog import ColoredFormatter


def setup_logging(level=logging.INFO):
    """Configure root logger with ColoredFormatter."""
    formatter = ColoredFormatter(
        "[  %(log_color)s%(levelname)s%(reset)s  ] [%(asctime)s] [%(name)s] => %(funcName)s : %(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':    'white',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red',
        }
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    # avoid duplicate handlers if setup_logging is called twice
    if not root.handlers:
        root.addHandler(handler)

    return root

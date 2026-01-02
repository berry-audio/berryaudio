import logging, colorlog
from colorlog import ColoredFormatter

def setup_logging(level=logging.INFO):
    """Configure root logger with ColoredFormatter."""

    logging.addLevelName(logging.DEBUG,    "DEBUG")
    logging.addLevelName(logging.INFO,     "INFO ")
    logging.addLevelName(logging.WARNING,  "WARN ")
    logging.addLevelName(logging.ERROR,    "ERROR")
    logging.addLevelName(logging.CRITICAL, "FATAL")

    formatter = ColoredFormatter(
        "[  %(log_color)s%(levelname)s%(reset)s  ] "
        "[%(asctime)s] [%(name)s] => %(funcName)s : %(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':'white',
            'INFO ':'green',
            'WARN ':'yellow',
            'ERROR':'red',
            'FATAL':'red',
        }
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        root.addHandler(handler)

    return root

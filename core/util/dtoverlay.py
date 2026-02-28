#!/usr/bin/env python3
from pathlib import Path
import sys
import os
import logging

CONFIG_PATH = Path("/boot/firmware/config.txt")
logger = logging.getLogger(__name__)


def update_dtoverlay(anchor: str, overlay: str):
    lines = CONFIG_PATH.read_text().splitlines()

    try:
        idx = lines.index(anchor)
    except ValueError:
        logger.error("Anchor not found", file=sys.stderr)
        sys.exit(1)

    i = idx + 1
    while i < len(lines) and lines[i].startswith("dtoverlay="):
        del lines[i]

    lines.insert(idx + 1, f"dtoverlay={overlay}")
    CONFIG_PATH.write_text("\n".join(lines) + "\n")

if os.geteuid() != 0:
    logger.error("Must be run as root", file=sys.stderr)
    sys.exit(1)

update_dtoverlay(sys.argv[1], sys.argv[2])

#!/usr/bin/env python3
from pathlib import Path
import sys
import os
import subprocess
import logging

CONFIG_PATH = Path("/boot/firmware/config.txt")
CMDLINE_PATH = Path("/boot/firmware/cmdline.txt")

logger = logging.getLogger(__name__)


def update_dtoverlay(overlay: str | None = None, anchor: str | None = None):
    if anchor is not None:
        subprocess.run(
            ["sudo", "/usr/bin/python3", __file__, "dtoverlay", anchor, overlay or ""],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.debug(f"Updated config.txt with dtoverlay={overlay}")
    else:
        logger.error("Anchor must be provided for dtoverlay update")
        sys.exit(1)


def update_cmdline(config: str | None = None):
    subprocess.run(
        ["sudo", "/usr/bin/python3", __file__, "cmdline", config or ""],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    logger.debug(f"Updated cmdline.txt with config={config}")


def _apply_dtoverlay(anchor: str, overlay: str):
    lines = CONFIG_PATH.read_text().splitlines()
    try:
        idx = lines.index(anchor)
    except ValueError:
        logger.error("Anchor not found")
        sys.exit(1)

    i = idx + 1
    while i < len(lines) and lines[i].startswith("dtoverlay="):
        del lines[i]

    if overlay:
        lines.insert(idx + 1, f"dtoverlay={overlay}")

    CONFIG_PATH.write_text("\n".join(lines) + "\n")


def _apply_cmdline(config: str | None):
    content = CMDLINE_PATH.read_text().strip()
    parts = content.split()

    parts = [p for p in parts if not p.startswith("video=")]

    if config:
        parts.insert(0, config)

    CMDLINE_PATH.write_text(" ".join(parts) + "\n")


if __name__ == "__main__":
    if os.geteuid() != 0:
        logger.error("Must be run as root")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "dtoverlay":
        _apply_dtoverlay(sys.argv[2], sys.argv[3])
    elif mode == "cmdline":
        _apply_cmdline(sys.argv[2])

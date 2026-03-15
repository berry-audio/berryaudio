import subprocess
import logging
import re
import sys
import shutil, os

from pathlib import Path

logger = logging.getLogger(__name__)


class SystemUtil:
    def __init__(self, core, db):
        super().__init__()
        self._core = core
        self._db = db

    async def service_camilladsp(self, state: str):
        """Control CamillaDSP service"""
        try:
            subprocess.run(
                ["sudo", "/bin/systemctl", state, "camilladsp.service"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.debug("CamillaDSP -> %s OK", state)
        except subprocess.CalledProcessError as e:
            logger.error("CamillaDSP -> %s failed: %s", state, e.stderr)
            raise

    async def service_samba(self, state: str):
        """Control Samba service"""
        try:
            subprocess.run(
                ["sudo", "/bin/systemctl", state, "smbd"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.debug("Samba -> %s OK", state)
        except subprocess.CalledProcessError as e:
            logger.error("Samba -> %s failed: %s", state, e.stderr)
            raise

    async def write_asoundrc(self, pcm=None, path: str = "/home/pi/.asoundrc"):
        """Switches between PCM device and bluealsa for RX/TX mode"""
        _config = self._db.get_config()
        _output_device = _config["mixer"]["output_device"]

        try:
            pcm = pcm or _output_device or "null_device"

            with open(path, "r") as f:
                content = f.read()

            match = re.search(r'pcm\s+"([^"]+)"', content)
            current_pcm = match.group(1) if match else None

            if current_pcm == pcm:
                return

            updated_content = re.sub(r'pcm\s+"[^"]+"', f'pcm "{pcm}"', content)

            with open(path, "w") as f:
                f.write(updated_content)

            logger.debug("PCM device updated to %s", pcm)

        except OSError as e:
            logger.error("Failed to write asoundrc: %s", e)
            raise

    async def write_xinitrc(self, xrandr: str = None, path: str = "/home/pi/.xinitrc"):
        if os.path.exists(path):
            shutil.copy(path, f"{path}.bak")

        lines = [
            "#!/bin/sh",
        ]

        if xrandr is not None:
            lines = [
                "xset s off",
                "xset -dpms",
                "xset s noblank",
                "unclutter -idle 0 -root &",
            ]
            lines.append(f"xrandr {xrandr}")
            lines.append(
                "berryaudio-1.0.0-app.AppImage --force-device-scale-factor=1.4 --no-sandbox > /tmp/electron_app.log 2>&1"
            )

        lines.append("# Development")
        lines.append(
            "# npm --prefix /home/pi/ba-frontend start > /tmp/electron.log 2>&1"
        )

        with open(path, "w") as f:
            f.write("\n".join(lines))

        os.chmod(path, 0o755)
        logger.debug(f"Written xinitrc with xrandr={xrandr}")

    async def write_dtoverlay(
        self, anchor: str | None = None, overlay: str | None = None
    ):
        if anchor is not None:
            try:
                subprocess.run(
                    [
                        "sudo",
                        "/usr/bin/python3",
                        __file__,
                        "dtoverlay",
                        anchor,
                        overlay or "",
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                logger.debug(f"Updated config.txt at '{anchor}' dtoverlay={overlay}")
            except subprocess.CalledProcessError as e:
                logger.error(f"dtoverlay update failed: {e.stderr.decode().strip()}")
            except Exception as e:
                logger.error(f"Unexpected error updating dtoverlay: {e}")
        else:
            logger.error("Anchor must be provided for dtoverlay update")
            sys.exit(1)

    async def write_cmdline(self, config: str | None = None):
        try:
            subprocess.run(
                ["sudo", "/usr/bin/python3", __file__, "cmdline", config or ""],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.debug(f"Updated cmdline.txt with config={config}")
        except subprocess.CalledProcessError as e:
            logger.error(f"cmdline update failed: {e.stderr.decode().strip()}")
        except Exception as e:
            logger.error(f"Unexpected error updating cmdline: {e}")


def apply_dtoverlay(anchor: str, overlay: str, path="/boot/firmware/config.txt"):
    config_path = Path("/boot/firmware/config.txt")

    lines = config_path.read_text().splitlines()
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

    config_path.write_text("\n".join(lines) + "\n")


def apply_cmdline(config: str | None, path="/boot/firmware/cmdline.txt"):
    config_path = Path("/boot/firmware/cmdline.txt")
    content = config_path.read_text().strip()
    parts = content.split()

    parts = [p for p in parts if not p.startswith("video=")]

    if config:
        parts.insert(0, config)

    config_path.write_text(" ".join(parts) + "\n")


if __name__ == "__main__":
    if os.geteuid() != 0:
        logger.error("Must be run as root")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "dtoverlay":
        apply_dtoverlay(sys.argv[2], sys.argv[3])
    elif mode == "cmdline":
        apply_cmdline(sys.argv[2])

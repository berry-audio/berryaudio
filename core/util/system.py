import subprocess
import logging
import re
import sys
import socket
import shutil
import os

from pathlib import Path

logger = logging.getLogger(__name__)


class SystemUtil:
    def __init__(self, core, db):
        super().__init__()
        self._core = core
        self._db = db

    def get_board(self) -> str:
        try:
            with open("/proc/device-tree/model", "r") as f:
                model = f.read().lower()
            if "zero 2" in model:
                return "PI_ZERO_2W"
            if "zero" in model:
                return "PI_ZERO_W"
            if "pi 5" in model:
                return "PI_5"
            if "pi 4" in model:
                return "PI_4"
            if "pi 3" in model:
                return "PI_3"
            if "pi 2" in model:
                return "PI_2"
            if "rock" in model:
                return "ROCKCHIP"
            if "odroid" in model:
                return "ODROID"
            if "orange" in model:
                return "ORANGE_PI"
            if "banana" in model:
                return "BANANA_PI"
            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    async def write_asoundrc(self, pcm=None, path: str = "/home/pi/.asoundrc"):
        """Switches between PCM device and bluealsa for RX/TX mode"""
        _config = self._db.get_config()
        _hw_device = _config["mixer"]["hw_device"]

        try:
            pcm = pcm or _hw_device or "null_device"

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
                logger.debug(
                    f"Updated config.txt at '{anchor}' dtoverlay={overlay}")
            except subprocess.CalledProcessError as e:
                logger.error(
                    f"dtoverlay update failed: {e.stderr.decode().strip()}")
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

    async def write_g_audio_config(
        self,
        samplerate: int | None = None,
    ):
        """Updates g_audio.conf with new sample rates and product info, then reloads the module"""
        manufacturer = self.get_board()
        product = f"{socket.gethostname()} USB DAC"

        try:
            subprocess.run(
                [
                    "sudo",
                    "/usr/bin/python3",
                    __file__,
                    "g_audio",
                    str(samplerate) if samplerate else "",
                    manufacturer or "",
                    product or "",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.debug(
                f"Updated g_audio.conf: p_srate={samplerate}, c_srate={samplerate}, "
                f"iManufacturer={manufacturer}, iProduct={product}"
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"g_audio config update failed: {e.stderr.decode().strip()}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating g_audio: {e}")
            raise


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


def apply_g_audio_config(
    samplerate: str | None = None,
    manufacturer: str | None = "Berryaudio OS",
    product: str | None = None,
    path: str = "/etc/modprobe.d/g_audio.conf",
):
    """Apply changes to g_audio.conf and reload the module. Creates file if it doesn't exist."""
    config_path = Path(path)

    idVendor = "0x1d6b"
    idProduct = "0x0105"
    iSerialNumber = "BA0001"
    p_chmask = "3"
    c_chmask = "3"
    p_ssize = "2"
    c_ssize = "2"

    config_template = """options g_audio \\
        idVendor={idVendor} \\
        idProduct={idProduct} \\
        iManufacturer="{manufacturer}" \\
        iProduct="{product}" \\
        iSerialNumber="{iSerialNumber}" \\
        p_srate={p_srate} \\
        c_srate={c_srate} \\
        p_chmask={p_chmask} \\
        c_chmask={c_chmask} \\
        p_ssize={p_ssize} \\
        c_ssize={c_ssize}
        """

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {config_path.parent}")
    except OSError as e:
        logger.error(f"Failed to create directory {config_path.parent}: {e}")
        raise

    if config_path.exists():
        try:
            content = config_path.read_text()
            logger.debug(f"Read existing config from {path}")
        except OSError as e:
            logger.error(f"Failed to read existing config: {e}")
            raise
    else:
        logger.debug(f"Config file not found, creating new one at {path}")
        default_samplerate = samplerate or "96000"
        default_product = product or "Berryaudio USB DAC"

        content = config_template.format(
            idVendor=idVendor,
            idProduct=idProduct,
            iManufacturer=manufacturer,
            iProduct=default_product,
            iSerialNumber=iSerialNumber,
            p_srate=default_samplerate,
            c_srate=default_samplerate,
            p_chmask=p_chmask,
            c_chmask=c_chmask,
            p_ssize=p_ssize,
            c_ssize=c_ssize,
        )

    if samplerate:
        content = re.sub(r"p_srate=\d+", f"p_srate={samplerate}", content)
        content = re.sub(r"c_srate=\d+", f"c_srate={samplerate}", content)

    if manufacturer:
        content = re.sub(
            r'iManufacturer="[^"]*"', f'iManufacturer="{manufacturer}"', content
        )

    if product:
        content = re.sub(
            r'iProduct="[^"]*"', f'iProduct="{product}"', content
        )

    try:
        config_path.write_text(content)
        logger.debug(f"Successfully wrote g_audio.conf to {path}")
    except OSError as e:
        logger.error(f"Failed to write g_audio.conf: {e}")
        raise

    try:
        modules_to_unload = ["g_audio",
                             "usb_f_uac2", "u_audio", "libcomposite"]
        for module in modules_to_unload:
            try:
                subprocess.run(
                    ["modprobe", "-r", module],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                )
                logger.debug(f"Unloaded {module}")
            except subprocess.CalledProcessError as e:
                logger.debug(
                    f"Could not unload {module}: {e.stderr.decode().strip()}")
            except subprocess.TimeoutExpired:
                logger.debug(f"Timeout unloading {module}")

        subprocess.run(
            ["modprobe", "g_audio"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.debug("Reloaded g_audio module")

    except subprocess.CalledProcessError as e:
        logger.error(f"modprobe failed: {e.stderr.decode().strip()}")
        raise


if __name__ == "__main__":
    if os.geteuid() != 0:
        logger.error("Must be run as root")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "dtoverlay":
        apply_dtoverlay(sys.argv[2], sys.argv[3])
    elif mode == "cmdline":
        apply_cmdline(sys.argv[2] if len(sys.argv) > 2 else None)
    elif mode == "g_audio":
        apply_g_audio_config(
            samplerate=sys.argv[2] if len(
                sys.argv) > 2 and sys.argv[2] else None,
            manufacturer=sys.argv[3] if len(
                sys.argv) > 3 and sys.argv[3] else None,
            product=sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None,
        )

import logging

logger = logging.getLogger(__name__)

def write_xinitrc(xrandr: str = None, path: str = "/home/pi/.xinitrc"):
    import shutil, os

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
    lines.append("# npm --prefix /home/pi/ba-frontend start > /tmp/electron.log 2>&1")
    
    with open(path, "w") as f:
        f.write("\n".join(lines))

    os.chmod(path, 0o755)
    logger.debug(f"Written xinitrc with xrandr={xrandr}")
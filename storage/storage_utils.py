import psutil
import pyudev
import subprocess
import re

from pathlib import Path

custom_root_mount = "/home/pi/my_music"
exclude_dev = ['/dev/mmcblk0p1']
internal_dev = ['/dev/mmcblk0p2']

def marketed_size_bytes(size_bytes: int) -> int:
    """Return approximate marketed size in GB (decimal units)."""
    gb = size_bytes / 1_000_000_000
    return int(gb)

def get_mounted_partitions():
    """Return dict: device -> (mountpoint, usage-info) for mounted partitions."""
    mounts = {}
    for p in psutil.disk_partitions(all=False):
        if "rw" in p.opts and p.fstype:
            usage = psutil.disk_usage(p.mountpoint)
            mounts[p.device] = {
                "mount": p.mountpoint,
                "fstype": p.fstype,
                "usage": usage,
            }
    return mounts

def get_fs_info(dev: str):
    """Get filesystem type and label for a device using blkid (handles spaces)."""
    try:
        output = subprocess.check_output(["blkid", dev], text=True).strip()
        fs_type = None
        label = None

        type_match = re.search(r'TYPE="([^"]+)"', output)
        if type_match:
            fs_type = type_match.group(1)

        label_match = re.search(r'LABEL="([^"]+)"', output)
        if label_match:
            label = label_match.group(1)

        return fs_type, label
    except subprocess.CalledProcessError:
        return None, None

def get_storage_info():
    """Return a dict with mounted and unmounted devices."""
    context = pyudev.Context()
    mounts = get_mounted_partitions()
    mounted = []
    unmounted = []

    for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
        devname = device.device_node
        if devname not in exclude_dev:
            devname = device.device_node
            parent = device.find_parent('block').device_node
            size_bytes = int(device.attributes.asint('size')) * 512
            removable = bool(int(device.attributes.get('removable', 0)))
            fs_type, label = get_fs_info(devname)

            device_info = {
                "dev": devname,
                "parent": parent,
                "removable": removable,
                "size_bytes": size_bytes,
                "marketed_gb": marketed_size_bytes(size_bytes),
                "fstype": fs_type,
                "label": 'Internal' if devname == internal_dev[0] else label,
            }

            if devname in mounts:
                u = mounts[devname]["usage"]

                mount_point = mounts[devname]["mount"]
                if mount_point == "/" and devname == internal_dev[0]:
                    mount_point = custom_root_mount

                device_info.update({
                    "status": "mounted",
                    "mount": mount_point,
                    "total": u.total,
                    "used": u.used,
                    "free": u.free,
                    "percent": u.percent,
                })
                mounted.append(device_info)
            else:
                device_info["status"] = "unmounted"
                unmounted.append(device_info)

    return {
        "mounted": mounted,
        "unmounted": unmounted
    }


from pathlib import Path

def list_paths(path, extensions=None):
    p = Path(path)
    results = []

    # Always include the parent directory entry first
    results.append({
        "name": "..",
        "type": "folder",
        "size": 0,
        "path": str(p.parent.resolve())
    })

    entries = []
    for item in p.iterdir():
        if item.is_dir():
            entries.append({
                "name": item.name,
                "type": "folder",
                "size": 0,
                "path": str(item.resolve())
            })
        else:
            if extensions is None or item.suffix.lower() in [ext.lower() for ext in extensions]:
                entries.append({
                    "name": item.name,
                    "type": "track",
                    "size": item.stat().st_size,
                    "path": str(item.resolve())
                })

    entries.sort(key=lambda x: (x["type"] != "folder", x["name"].lower()))

    results.extend(entries)
    return results



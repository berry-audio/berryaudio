import logging
import subprocess
import configparser
import io
import re

from pathlib import Path
from core.models import StorageShared

logger = logging.getLogger(__name__)

SMBD_CONF = "/etc/samba/smb.conf"


class StorageSMB:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self._shares = {s.name: s for s in self.list_shares()}

    async def share(
        self, uri: str, name: str = None, read_only: bool = False, comment: str = ""
    ):
        if not uri.startswith("storage:"):
            raise ValueError(f"Not a valid storage path: {uri}")

        _, path = uri.split(":", 1)

        folder = Path(path).resolve()
        if not folder.exists():
            raise ValueError(f"Path does not exist {folder}")
        if not folder.is_dir():
            raise ValueError(f"Path is not a directory {folder}")

        name = re.sub(r"[\[\]\'\"@#$]", "", name or folder.name).strip()

        self._shares[name] = StorageShared(
            name=name,
            uri=f"storage:{str(folder)}",
            read_only=read_only,
            comment=comment,
            browseable=True,
            guest_allowed=True if not self.username else False,
        )

        await self._write_conf()
        if self.username and self.password:
            self._set_samba_password()
        await self.restart()
        logger.info(f"Shared '{path}' (read_only={read_only})")
        return await self.status()

    async def unshare(self, uri: str):
        """Remove a share by path."""
        if not uri.startswith("storage:"):
            raise ValueError(f"Not a valid storage path: {uri}")

        _, path = uri.split(":", 1)

        await self._remove_conf(path)
        await self.restart()
        logger.info(f"Removed share for {path}")
        return await self.status()

    def list_shares(self) -> list[StorageShared]:
        config = configparser.RawConfigParser(
            delimiters=("=",), comment_prefixes=("#", ";"), strict=False
        )
        config.optionxform = str
        config.read(SMBD_CONF)
        shares = {}
        for name in config.sections():
            if name.lower() in ("global", "homes", "printers"):
                continue
            s = config[name]
            shares[name] = StorageShared(
                name=name,
                uri=f"storage:{s.get('path', '')}",
                comment=s.get("comment", ""),
                browseable=s.get("browseable", "yes") == "yes",
                read_only=s.get("read only", "no") == "yes",
                guest_allowed=s.get("guest ok", "no") == "yes",
                user=s.get("force user", ""),
                create_permissions=s.get("create mask", ""),
                directory_permissions=s.get("directory mask", ""),
            )
        return list(shares.values())

    def stop(self):
        subprocess.run(["sudo", "systemctl", "stop", "smbd"], check=False)
        logger.info("Stopped Samba service")

    async def restart(self):
        logger.debug("Restarting Samba service...")
        subprocess.run(["sudo", "systemctl", "restart", "smbd"], check=True)

    async def status(self):
        result = subprocess.run(
            ["sudo", "systemctl", "is-active", "smbd"], capture_output=True, text=True
        )
        status = result.stdout.strip() == "active"
        if status:
            logger.info("Samba is active and running.")
        else:
            logger.warning("Samba is not active.")
        return status

    async def _remove_conf(self, path: str):
        config = configparser.RawConfigParser(
            delimiters=("=",), comment_prefixes=("#", ";"), strict=False
        )
        config.optionxform = str
        config.read(SMBD_CONF)

        name = next(
            (
                s
                for s in config.sections()
                if config[s].get("path", "").strip() == path.strip()
            ),
            None,
        )
        if not name:
            logger.warning(f"No share found for path '{path}'")
            return

        del self._shares[name]
        await self._write_conf()
        logger.debug(f"Removed configuration for path: {name}")

    async def _write_conf(self):
        lines = []

        lines.append("[global]")
        global_opts = {
            "workgroup": "WORKGROUP",
            "server string": "Python SMB",
            "security": "user",
            "map to guest": "bad user" if not self.username else "never",
            "dns proxy": "no",
            "log level": "0",
            "socket options": "TCP_NODELAY IPTOS_LOWDELAY SO_RCVBUF=131072 SO_SNDBUF=131072",
            "read raw": "yes",
            "write raw": "yes",
            "max xmit": "65535",
            "dead time": "15",
            "getwd cache": "yes",
            "min protocol": "SMB2",
            "max protocol": "SMB3",
            "vfs objects": "fruit streams_xattr",
            "fruit:metadata": "stream",
            "fruit:posix_rename": "yes",
            "fruit:zero_file_id": "yes",
            "fruit:wipe_intentionally_left_blank_rfork": "yes",
            "fruit:delete_empty_adfiles": "yes",
        }
        for k, v in global_opts.items():
            lines.append(f"\t{k} = {v}")
        lines.append("")

        config = configparser.RawConfigParser(delimiters=("=",))
        config.optionxform = str
        for name, cfg in self._shares.items():
            cfg_name = name.replace("'", "")
            cfg_path = (
                cfg.uri.split(":", 1)[1] if cfg.uri.startswith("storage:") else None
            )
            if cfg_path is None:
                logger.error(f"Invalid URI for share '{name}': {cfg.uri}")
                continue
            config[cfg_name] = {
                "path": cfg_path,
                "comment": cfg.comment,
                "browseable": "yes" if cfg.browseable else "no",
                "read only": "yes" if cfg.read_only else "no",
                "guest ok": "yes" if cfg.guest_allowed else "no",
                "force user": cfg.user or "pi",
                "create mask": cfg.create_permissions or "0664",
                "directory mask": cfg.directory_permissions or "0775",
            }

        buf = io.StringIO()
        config.write(buf)
        lines.append(buf.getvalue())

        content = "\n".join(lines)
        subprocess.run(
            ["sudo", "tee", SMBD_CONF],
            input=content,
            text=True,
            capture_output=True,
        )
        logger.debug(f"Configuration written to {SMBD_CONF}")

    def _set_samba_password(self):
        """Set Samba password for user non-interactively."""
        proc = subprocess.run(
            ["sudo", "smbpasswd", "-a", "-s", self.username],
            input=f"{self.password}\n{self.password}\n",
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            subprocess.run(
                ["sudo", "smbpasswd", "-s", self.username],
                input=f"{self.password}\n{self.password}\n",
                text=True,
            )
        logger.debug(f"Password set for '{self.username}'")

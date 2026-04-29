import logging
import subprocess
import configparser
import io
import re
import psutil
import socket

from pathlib import Path
from core.models import Storage, Directory, StorageUsage

logger = logging.getLogger(__name__)

SMBD_CONF = "/etc/samba/smb.conf"


class StorageSmbManager:
    def __init__(self, name, core, db=None, username=None, password=None):
        self._name = name
        self._core = core
        self._db = db
        self.username = username
        self.password = password
        self._remote_username = None
        self._remote_password = None
        self._shares = {s.name: s for s in self.list_shared_directories()}
        self._smb_shares = {}

    async def samba_service(self, state: str):
        """Control Samba service"""

        try:
            subprocess.run(
                ["sudo", "/bin/systemctl", state, "smbd"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info("Service %s OK", state)
        except subprocess.CalledProcessError as e:
            logger.error("Service %s failed: %s", state, e.stderr)
            raise ValueError(f"Service {state} failed: {e.stderr}") from e

    async def samba_status(self):
        """Checks samba service status"""

        result = subprocess.run(
            ["sudo", "systemctl", "is-active", "smbd"], capture_output=True, text=True
        )
        status = result.stdout.strip() == "active"
        if status:
            logger.info("Active")
        else:
            logger.error("Inactive")
        return status

    async def share_directory(self, uri: str, name: str = None, read_only: bool = False):
        """Shares a Directory by URI."""

        if not uri.startswith(f"{self._name}:"):
            raise ValueError(f"Not a valid {self._name} path: {uri}")

        _, path = uri.split(":", 1)

        folder = Path(path).resolve()

        if not folder.exists():
            raise ValueError(f"Path does not exist {folder}")
        if not folder.is_dir():
            raise ValueError(f"Path is not a directory {folder}")

        name = re.sub(r"[\[\]\'\"@#$]", "", name or folder.name).strip()

        self._shares[name] = Directory(
            uri=uri,
            name=name,
            shared=True,
            read_only=read_only,
            guest_allowed=True if not self.username else False,
        )
        directory = self._shares[name]

        await self._write_conf()
        if self.username and self.password:
            self.samba_set_password()

        await self.samba_service("restart")
        self._core.send(
            target=["web", "display"], event="storage_shared", directory=directory
        )

        logger.info(f"Shared '{path}' (read_only={read_only})")
        return await self.samba_status()

    async def unshare_directory(self, uri: str):
        """Unshares a Directory by URI."""

        if not uri.startswith("storage:"):
            raise ValueError(f"Not a valid storage path: {uri}")

        _, path = uri.split(":", 1)

        shared = next((s for s in self._shares.values() if s.uri == uri), None)
        if not shared:
            raise ValueError(f"Share not found: {uri}")

        directory = Directory(
            uri=uri,
            name=shared.name,
            shared=False,
            read_only=shared.read_only,
            guest_allowed=shared.guest_allowed,
            create_permissions=shared.create_permissions,
            directory_permissions=shared.directory_permissions,
        )

        await self._remove_conf(path)

        self._core.send(
            target=["web", "display"],
            event="storage_unshared",
            directory=directory,
        )
        await self.samba_service("restart")
        self._core.send(
            target=["web", "display"], event="storage_unshared", directory=directory
        )
        logger.info(f"Removed share for {path}")
        return await self.samba_status()

    def list_shared_directories(self) -> list[Directory]:
        """Lists all shared directories."""

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
            shares[name] = Directory(
                uri=f"{self._name}:{s.get('path', '')}",
                name=name,
                shared=True,
                read_only=s.get("read only", "no") == "yes",
                guest_allowed=s.get("guest ok", "no") == "yes",
                user=s.get("force user", ""),
            )
        return list(shares.values())

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
        return name

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
                cfg.uri.split(":", 1)[1]
                if cfg.uri.startswith(f"{self._name}:")
                else None
            )
            if cfg_path is None:
                logger.error(f"Invalid URI for share '{name}': {cfg.uri}")
                continue
            config[cfg_name] = {
                "path": cfg_path,
                "browseable": "yes",
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

    async def set_credentials(self, username=None, password=None):
        """Sets global username password for sharing """

        if password and not username:
            raise ValueError("Username is required when password is provided")

        self.username = username
        self.password = password

        for name, share in self._shares.items():
            share.guest_allowed = True if not self.username else False

        await self._write_conf()

        if self.username and self.password:
            self.samba_set_password()

        await self.samba_service("restart")
        logger.info(
            f"Samba credentials with username: {self.username}, password: {self.password} saved successfully."
        )

    def samba_set_password(self):
        """Set Samba password for user non-interactively."""

        result = subprocess.run(
            ["id", self.username],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            subprocess.run(
                ["sudo", "useradd", "-M", "-s", "/sbin/nologin", self.username],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info(f"System user '{self.username}' created")

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

    def add_shared(
        self, ip: str, username: str = None, password: str = None
    ) -> dict | None:
        """Adds a NAS drive to OS """

        self._remote_username = None
        self._remote_password = None

        try:
            auth = f"{username}%{password}" if username and password else "%"

            result = subprocess.run(
                ["smbclient", "-L", f"//{ip}", "-U", auth],
                capture_output=True,
                text=True,
                timeout=5,
            )

            stdout = result.stdout
            stderr = result.stderr

            if "NT_STATUS_LOGON_FAILURE" in stdout:
                raise PermissionError(
                    f"Authentication failed for {ip} with user '{username}'"
                )

            if "NT_STATUS_ACCESS_DENIED" in stdout:
                raise PermissionError(f"Access denied on {ip}")

            if "NT_STATUS_CONNECTION_REFUSED" in stdout:
                raise ConnectionRefusedError(f"Connection refused on {ip}")

            if (
                "NT_STATUS_HOST_UNREACHABLE" in stdout
                or "NT_STATUS_HOST_UNREACHABLE" in stderr
            ):
                raise ConnectionError(f"Host unreachable: {ip}")

            if (
                "NT_STATUS_NO_SUCH_FILE" in stdout
                or "Name or service not known" in stderr
            ):
                raise ConnectionError(f"Host not found: {ip}")

            if "Failed to connect" in stderr or "Connection timed out" in stderr:
                raise ConnectionError(f"Could not connect to {ip}")

            if "NT_STATUS" in stdout:
                raise ConnectionError(f"SMB error on {ip}: {stdout.strip()}")

            if not stdout.strip():
                raise ConnectionError(f"No response from {ip}")

            self._remote_username = username
            self._remote_password = password

            shares = []
            parsing = False
            for line in stdout.splitlines():
                line = line.strip()
                if "Sharename" in line:
                    parsing = True
                    continue
                if "----------" in line:
                    continue
                if parsing and line == "":
                    break
                if parsing and line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[-1] == "Disk":
                        name = line.split("Disk")[0].strip()
                        if name and not name.endswith("$"):
                            shares.append(
                                Storage(
                                    icon="nas",
                                    name=name,
                                    dev=f"smb://{ip}/{name}",
                                    shared=False,
                                    status="mounted",
                                    read_only=False,
                                    guest_allowed=username is None,
                                    user=username or "",
                                )
                            )

            if not shares:
                raise ValueError(f"No SMB shares found on {ip}")

            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "Unknown"

            return {"ip": ip, "hostname": hostname, "shares": shares}

        except (PermissionError, ConnectionRefusedError, ConnectionError, ValueError):
            raise
        except subprocess.TimeoutExpired:
            raise ConnectionError(f"Timed out connecting to {ip}")
        except Exception as e:
            logger.error(f"{ip} error: {e}")
            return None

    def list_smb_shared(self) -> list[Storage]:
        """Lists all NAS drives from OS """

        storages = []
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3 and parts[2] == "cifs":
                    device, mount_point = parts[0], parts[1]
                    u = psutil.disk_usage(mount_point)

                    clean_device = device.replace("\\040", " ")
                    clean_name = clean_device.split("/")[-1]
                    smb_uri = f"smb://{clean_device.lstrip('/')}"
                    storages.append(
                        Storage(
                            icon="nas",
                            uri=f"{self._name}:{mount_point}",
                            name=clean_name,
                            dev=smb_uri,
                            shared=False,
                            fstype="cifs",
                            status="mounted",
                            usage=StorageUsage(
                                total=u.total,
                                used=u.used,
                                free=u.free,
                            ),
                        )
                    )

        self._smb_shares = storages
        return storages

    async def mount_shared(
        self, devs: list[str], username: str = None, password: str = ""
    ) -> bool:
        """Mounts a NAS drive from OS """

        try:
            for dev in devs:
                is_mounted = False

                if not dev.startswith("smb://"):
                    raise ValueError(f"Invalid SMB URI: {dev}")

                if self._db is None:
                    raise ValueError("DB not initialized")

                path = dev.replace("smb://", "")
                mount_name = path.replace("/", "_").replace(" ", "_").replace("'", "")
                mount_point = f"/media/pi/{mount_name}"

                with open("/proc/mounts", "r") as f:
                    if any(mount_point in line for line in f):
                        logger.info(f"'{dev}' already mounted, skipping")
                        is_mounted = True

                if not is_mounted:
                    subprocess.run(["sudo", "mkdir", "-p", mount_point], check=True)
                    options = "vers=2.0,sec=ntlmssp,uid=1000,gid=1000"

                    if username:
                        options += f",username={username},password={password}"
                    elif self._remote_username and self._remote_password:
                        options += f",username={self._remote_username},password={self._remote_password}"
                    else:
                        options += ",guest"

                    result = subprocess.run(
                        [
                            "sudo",
                            "mount",
                            "-t",
                            "cifs",
                            f"//{path}",
                            mount_point,
                            "-o",
                            options,
                        ],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode != 0:
                        stderr = result.stderr.strip()
                        if "13" in stderr:
                            raise PermissionError(
                                f"Permission denied mounting '{dev}' — check credentials"
                            )
                        elif "16":
                            raise ValueError(
                                f"'{dev}' is already mounted or resource is busy"
                            )
                        elif "115":
                            raise ConnectionError(
                                f"Timeout connecting to '{dev}' — check network"
                            )
                        elif "2":
                            raise FileNotFoundError(f"Share not found: '{dev}'")
                        else:
                            raise ConnectionError(f"Mount failed for '{dev}': {stderr}")

                u = psutil.disk_usage(mount_point)
                label = path.split("/")[-1]

                storage = Storage(
                    icon="nas",
                    uri=f"{self._name}:{mount_point}",
                    name=label,
                    dev=dev,
                    fstype="cifs",
                    status="mounted",
                    usage=StorageUsage(
                        total=u.total,
                        used=u.used,
                        free=u.free,
                    ),
                )
                self._smb_shares[dev] = storage

                config = self._db.get_config()
                config_storage = config.get(self._name, {}).get("smb_clients", {}) or {}
                if dev not in config_storage:
                    config_storage[str(dev)] = {
                        "username": self._remote_username,
                        "password": self._remote_password,
                    }
                self._db.set_config({self._name: {"smb_clients": config_storage}})

                if not is_mounted:
                    self._core.send(
                        target=["web", "display"],
                        event="storage_mounted",
                        storage=storage,
                    )

            return True

        except (ValueError, PermissionError, ConnectionError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to mount shares: {e}")
            return False

    async def unmount_shared(self, dev: str) -> bool:
        """Unmounts a NAS drive from OS """

        try:
            is_unmounted = False
            if not dev.startswith("smb://"):
                raise ValueError(f"Invalid SMB uri: {dev}")

            if self._db is None:
                raise ValueError("DB not initialized")

            path = dev.replace("smb://", "")
            mount_name = path.replace("/", "_").replace(" ", "_").replace("'", "")
            mount_point = f"/media/pi/{mount_name}"

            with open("/proc/mounts", "r") as f:
                if not any(mount_point in line for line in f):
                    logger.info(f"'{dev}' already unmounted, skipping")
                    is_unmounted = True

            if not is_unmounted:
                result = subprocess.run(
                    ["sudo", "umount", mount_point], capture_output=True, text=True
                )

                if result.returncode != 0:
                    stderr = result.stderr.strip()
                    if "16" in stderr:
                        raise ValueError(f"'{dev}' is busy")
                    elif "2" in stderr:
                        raise FileNotFoundError(f"'{mount_point}' not found")
                    elif "13" in stderr:
                        raise PermissionError(f"'{dev}' permission denied")
                    elif "22" in stderr:
                        raise ValueError(f"'{dev}' invalid argument")
                    else:
                        raise ConnectionError(f"'{dev}': {stderr}")

                subprocess.run(["sudo", "rmdir", mount_point], capture_output=True)

            config = self._db.get_config()
            config_storage = config.get(self._name, {}).get("smb_clients", {}) or {}
            config_storage.pop(str(dev), None)
            self._db.set_config({self._name: {"smb_clients": config_storage}})

            if self._smb_shares[dev]:
                self._core.send(
                    target=["web", "display"],
                    event="storage_removed",
                    storage=self._smb_shares[dev],
                )
                self._smb_shares.pop(dev, None)

            return True

        except (ValueError, PermissionError, ConnectionError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to unmount share: {e}")
            return False

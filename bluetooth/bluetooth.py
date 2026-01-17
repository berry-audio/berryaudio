import logging
import pydbus
import asyncio
import subprocess
import threading
import re
import os

from gi.repository import GLib
from core.actor import Actor
from core.models import Album, Artist, Track, TlTrack, Source
from core.types import PlaybackState

logger = logging.getLogger(__name__)
bus = pydbus.SystemBus()

DISCOVERY_TIME = 10  # seconds

# Connection Management
IFACE = "org.freedesktop.DBus.Properties"
IFACE_SIGNAL_LISTENER = "PropertiesChanged"
BLUEZ_SERVICE = "org.bluez"
BLUEZ_ADAPTER = "org.bluez.Adapter1"
BLUEZ_DEVICE = "org.bluez.Device1"
ADAPTER_PATH = "/org/bluez/hci0"

MNGR = bus.get(BLUEZ_SERVICE, "/")
ADAPTER = bus.get(BLUEZ_SERVICE, ADAPTER_PATH)

# Audio Management
BLUEALSA_SERVICE = "org.bluealsa"
BLUEALSA_MANAGER = "/org/bluealsa"
BLUEALSA_PCM = "org.bluealsa.PCM1"
BLUEALSA_SOFT_VOLUME = True
BLUEALSA_HW_VOLUME = 100

# paths
ASOUNDRC_PATH = "/home/pi/.asoundrc"
BLUETOOTH_APLAY_PATH = "/usr/bin/bluealsa-aplay"
BLUETOOTH_AGENT_PATH = "/usr/bin/bt-agent"
PCM_BLUEALSA = "bluealsa"

# Profiles
MODE_TX = "AD2P-source"
MODE_RX = "AD2P-sink"


class BluetoothExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._loop = asyncio.get_running_loop()
        self._core = core
        self._db = db
        self._config = config
        self._mode = MODE_RX
        self._interface_name = None
        self._devices = []
        self._track_mem = None
        self._volume = 0
        self._tl_track = TlTrack(0, track=Track())
        self._name = self._config["system"]["hostname"]
        self._device_aplay = self._config["playback"]["output_device"]
        self._device = "hw:CARD=DAC,DEV=0"
        self._proc_aplay = None
        self._proc_agent = None
        self._source = Source(type="bluetooth", controls=[], state={"connected": False})

    async def on_start(self):
        if not os.path.exists(BLUETOOTH_AGENT_PATH):
            logger.error("Bluetooth agent service missing")
            return

        if not os.path.exists(BLUETOOTH_APLAY_PATH):
            logger.error("Bluetooth aplay service missing")
            return

        await self._update_pcm()
        await self.on_adapter_set_state(False)
        threading.Thread(target=self._init_agent, daemon=True).start()
        logger.info("Started")
        bus.subscribe(
            iface=IFACE,
            signal=IFACE_SIGNAL_LISTENER,
            signal_fired=self._properties_changed,
        )

    async def on_event(self, message):
        if self._mode != MODE_TX:
            return

        event = message.get("event")
        if event not in ("volume_changed", "mixer_mute"):
            return

        try:
            connected_device = await self.on_device()
            if not connected_device:
                return

            address = connected_device.get("address")
            if (
                event == "volume_changed"
                and (volume := message.get("volume")) is not None
            ):
                await self.on_set_volume(
                    address=address, volume=volume, soft_volume=BLUEALSA_SOFT_VOLUME
                )
            elif event == "mixer_mute" and (mute := message.get("mute")) is not None:
                await self.on_set_volume(
                    address=address,
                    volume=self._volume,
                    soft_volume=BLUEALSA_SOFT_VOLUME,
                    mute=mute,
                )

        except Exception as e:
            print(f"Error handling {event}:", e)

    async def on_stop(self):
        await self._stop_aplay()
        self._stop_agent()
        logger.info("Stopped")

    async def on_start_service(self):
        await self.on_adapter_set_state(True)
        return True

    async def on_stop_service(self):
        if self._mode == MODE_RX:
            devices = await self.on_devices()
            for device in devices:
                if device.get("connected"):
                    path = self._addr_to_bluez_path(device["address"])
                    device_bus = bus.get(BLUEZ_SERVICE, path)
                    if hasattr(device_bus, "Disconnect"):
                        logger.debug(
                            f"Disconnecting bluetooth device {device.get('name')}"
                        )
                        device_bus.Disconnect()
        return True

    def _init_agent(self):  # todo move this to daemon service
        if os.path.exists(BLUETOOTH_AGENT_PATH):
            cmd = [BLUETOOTH_AGENT_PATH, "-c", "NoInputNoOutput"]
            logger.info(f"Started Bluetooth agent service")
            self._proc_agent = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            logger.error(f"Bluetooth agent service not found {BLUETOOTH_AGENT_PATH}")

    async def _init_aplay(self):
        """Bluetooth Alsa Play service"""
        if os.path.exists(BLUETOOTH_APLAY_PATH):

            def _proc_aplay():
                cmd = [
                    BLUETOOTH_APLAY_PATH,
                    "--pcm",
                    self._device_aplay,
                    "--profile-a2dp",
                ]
                self._proc_aplay = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                logger.info(f"Started Bluetooth aplay service")

            threading.Thread(target=_proc_aplay, daemon=True).start()
        else:
            logger.error(f"Bluetooth aplay service not found {BLUETOOTH_APLAY_PATH}")

    async def _stop_aplay(self):
        if self._proc_aplay is not None:
            self._proc_aplay.terminate()
            self._proc_aplay.kill()
            logger.info(f"Stopped Bluetooth aplay service")

    def _stop_agent(self):
        if self._proc_agent is not None:
            self._proc_agent.terminate()
            self._proc_agent.kill()

    def _clear_source_info(self):
        self._source.state.connected = False
        self._source.state.name = None
        self._source.state.icon = None
        self._source.state.address = None
        self._core._request("source.update_source", source=self._source)

    async def _handle_connected(self, interface_name: str):
        address = self._bluez_path_to_addr(interface_name)
        connected_device = await self.on_device(address)
        current_source = await self._core.request("source.get")
        current_mixer_volume = await self._core.request("mixer.get_volume")

        if not connected_device:
            return

        self._core.send(event="bluetooth_device_connected", device=connected_device)
        logger.info(
            f'Bluetooth device connected: {connected_device.get("name")} {connected_device.get("address")} ({self._mode})'
        )

        for device in await self.on_devices():
            if device.get("connected") and device.get("address") != address:
                path = self._addr_to_bluez_path(device["address"])
                device_bus = bus.get(BLUEZ_SERVICE, path)
                if hasattr(device_bus, "Disconnect"):
                    logger.debug(
                        f"Disconnecting other bluetooth device {device.get('name')}"
                    )
                    device_bus.Disconnect()

        if self._mode == MODE_RX:
            await self._stop_aplay()
            await self._init_aplay()
            await self._update_pcm()

            if not current_source or current_source.type != self._source.type:
                await self._core.request("source.set", type=self._source.type)

            self._source.state.connected = connected_device.get("connected")
            self._source.state.name = connected_device.get("name")
            self._source.state.icon = connected_device.get("icon")
            self._source.state.address = connected_device.get("address")
            self._core._request("source.update_source", source=self._source)

        if self._mode == MODE_TX:
            await self._stop_aplay()
            await self._update_pcm(PCM_BLUEALSA)
            await self.on_set_volume(  # set initial device hardware volume to 100
                address=connected_device.get("address"),
                volume=BLUEALSA_HW_VOLUME,
                soft_volume=False,
            )
            await self.on_set_volume(
                address=connected_device.get("address"),
                volume=current_mixer_volume,
                soft_volume=BLUEALSA_SOFT_VOLUME,
            )

            if current_source is not None and current_source.type == self._source.type:
                await self._core.request("source.set", type=None)
                self._core._request("playback.set_state", state=PlaybackState.STOPPED)

        connected_device = await self.on_device(address)
        self._core.send(event="bluetooth_device_updated", device=connected_device)

    async def _handle_disconnected(self, interface_name):
        address = self._bluez_path_to_addr(interface_name)
        disconnected_device = await self.on_device(address)
        connected_device = await self.on_device()
        current_source = await self._core.request("source.get")

        if not connected_device:
            await self._stop_aplay()
            await self._update_pcm()

            if self._mode == MODE_RX:
                self._clear_source_info()

            if self._mode == MODE_TX:
                if (
                    current_source is not None
                    and current_source.type == self._source.type
                ):
                    await self._core.request("source.set", type=None)

        self._core.send(
            event="bluetooth_device_disconnected",
            device=disconnected_device,
        )
        logger.info(
            f'Bluetooth device disconnected: {disconnected_device.get("name")} {disconnected_device.get("address")}'
        )

    def _properties_changed(self, *args):
        """Properties changed listener for python DBus"""
        sender, interface_name, member, path, parameters = args
        changed_iface, properties, invalidated = parameters

        if ADAPTER_PATH in interface_name:
            logger.debug(properties)

            if "Connected" in properties and changed_iface == "org.bluez.Device1":
                if properties.get("Connected"):
                    self._interface_name = interface_name
                else:
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task, self._handle_disconnected(interface_name)
                    )

            if "Device" in properties and changed_iface == "org.bluez.MediaEndpoint1":
                if "sink" in interface_name:
                    self._mode = MODE_RX

                if "source" in interface_name:
                    self._mode = MODE_TX

                self._loop.call_soon_threadsafe(
                    asyncio.create_task,
                    self._handle_connected(self._interface_name),
                )
                self._interface_name = None

            if "Discoverable" in properties:
                self._core.send(
                    event="bluetooth_state_changed", state=self.on_adapter_get_state()
                )

            if "Pairable" in properties:
                self._core.send(
                    event="bluetooth_state_changed", state=self.on_adapter_get_state()
                )

            if "Powered" in properties:
                if not properties.get("Powered"):
                    self._loop.call_soon_threadsafe(
                        asyncio.create_task,
                        self._update_pcm(),
                    )

            if "Status" in properties:
                if self._mode == MODE_RX:
                    if properties.get("Status") == "active":
                        self._bluealsa_aplay_to_pcm()

                    if properties.get("Status") == "playing":
                        self._core._request(
                            "playback.set_state", state=PlaybackState.PLAYING
                        )

                    if properties.get("Status") == "paused":
                        self._core._request(
                            "playback.set_state", state=PlaybackState.PAUSED
                        )

            if "Volume" in properties:
                pass  # todo to handle volume directly from here

            if "Track" in properties:
                self._bluealsa_aplay_to_pcm()

                _track = properties.get("Track")
                if _track:
                    _tl_track = self._tl_track.track.copy(
                        update={
                            "name": _track.get("Title", None),
                            "artists": (
                                frozenset([Artist(name=_track.get("Artist", None))])
                                if _track.get("Artist")
                                else []
                            ),
                            "albums": (
                                [Album(name=_track.get("Album"))]
                                if _track.get("Album")
                                else []
                            ),
                            "track_no": _track.get("TrackNumber", 0),
                            "length": _track.get("Duration", 0),
                        }
                    )
                    self._tl_track = TlTrack(0, track=_tl_track)
                    self._core._request(
                        "playback.set_metadata", tl_track=self._tl_track
                    )

    async def on_adapter_set_state(self, state: bool):
        """Sets Adapter State"""
        get_state = self.on_adapter_get_state()

        if get_state["powered"] == state:
            if state:
                ADAPTER.Set(BLUEZ_ADAPTER, "Discoverable", GLib.Variant("b", True))
            return self.on_adapter_get_state()

        try:
            if state:
                ADAPTER.Set(BLUEZ_ADAPTER, "Alias", GLib.Variant("s", self._name))
                ADAPTER.Set(BLUEZ_ADAPTER, "Powered", GLib.Variant("b", True))
                ADAPTER.Set(BLUEZ_ADAPTER, "Discoverable", GLib.Variant("b", True))
                ADAPTER.Set(BLUEZ_ADAPTER, "Pairable", GLib.Variant("b", True))
            else:
                ADAPTER.Set(BLUEZ_ADAPTER, "Discoverable", GLib.Variant("b", False))
                ADAPTER.Set(BLUEZ_ADAPTER, "Pairable", GLib.Variant("b", False))
                ADAPTER.Set(BLUEZ_ADAPTER, "Powered", GLib.Variant("b", False))

            logger.info(self.on_adapter_get_state())
            return self.on_adapter_get_state()

        except Exception:
            raise RuntimeError(f"Failed to set adapter state")

    def on_adapter_get_state(self):
        """Sets Adapter State"""
        try:
            return {
                "powered": ADAPTER.Get(BLUEZ_ADAPTER, "Powered"),
                "discoverable": ADAPTER.Get(BLUEZ_ADAPTER, "Discoverable"),
                "pairable": ADAPTER.Get(BLUEZ_ADAPTER, "Pairable"),
            }
        except Exception:
            raise RuntimeError(f"Failed to get adapter state")

    async def on_devices(self, rescan: bool = False) -> list[dict]:
        """
        Discover Bluetooth devices or return cached devices.
        """
        if rescan:
            await self.on_adapter_set_state(True)
            logger.info("Scanning for available Bluetooth devices...")
            ADAPTER.StartDiscovery()
            try:
                await asyncio.sleep(DISCOVERY_TIME)
            finally:
                ADAPTER.StopDiscovery()

        mng_objs = MNGR.GetManagedObjects()
        devices: list[dict] = []

        for path, interfaces in mng_objs.items():
            device = interfaces.get(BLUEZ_DEVICE)
            if not device or not device.get("Name"):
                continue

            pcm_info = self._bluealsa_to_pcm(device.get("Address"))
            pcm_volume = (
                round(pcm_info.get("Volume")[0] * 100 / 127)
                if pcm_info.get("Volume")
                else None
            )

            devices.append(
                {
                    "address": device.get("Address"),
                    "name": device.get("Name"),
                    "profile": pcm_info.get("Transport", None),
                    "alias": device.get("Alias"),
                    "icon": device.get("Icon"),
                    "paired": device.get("Paired", False),
                    "trusted": device.get("Trusted", False),
                    "connected": device.get("Connected", False),
                    "soft_volume": pcm_info.get("SoftVolume", True),
                    "volume": pcm_volume,
                    "channels": pcm_info.get("Channels"),
                    "audio_codec": pcm_info.get("Codec"),
                    "sample_rate": pcm_info.get("Rate"),
                    "bit_depth": self._decode_bluealsa_format(pcm_info.get("Format")),
                    "uuids": device.get("UUIDs", []),
                }
            )

        self._devices = devices

        if rescan:
            logger.info(f"Found ({len(devices)}) Bluetooth devices.")
            logger.debug(devices)

        return devices

    async def on_device(self, address: str | None = None):
        """
        Get device information by Bluetooth address.
        """
        devices = await self.on_devices()

        if address is not None:
            address = address.upper()
            for device in devices:
                if device.get("address") == address:
                    return device
            return None

        for device in devices:
            if device.get("connected"):
                return device

        return None

    async def on_trust(self, address: str) -> bool:
        """
        Trust a Bluetooth device by MAC address.
        """
        if not address:
            raise ValueError("Bluetooth address is required to trust a device")

        address = address.upper()
        path = self._addr_to_bluez_path(address)

        try:
            logger.debug(f"Attempting to trust device {address} ({path})")
            device = bus.get(BLUEZ_SERVICE, path)
            value = GLib.Variant("b", True)
            device.Set(BLUEZ_DEVICE, "Trusted", value)
            return True

        except Exception as e:
            raise RuntimeError(f"Failed to trust device {address}") from e

    async def on_connect(self, address: str) -> bool:
        """
        Connect to a Bluetooth device by MAC address.
        """
        if not address:
            raise ValueError("Bluetooth address is required")

        address = address.upper()
        connected_device = await self.on_device()
        if connected_device and connected_device.get("address") == address:
            return True

        connecting_device = await self.on_device(address)
        if not connecting_device:
            raise RuntimeError(f"Device {address} not found")

        path = self._addr_to_bluez_path(address)

        try:
            logger.debug(f"Attempting to connect to {path}")
            device = bus.get(BLUEZ_SERVICE, path)

            await self.on_trust(
                address
            )  # todo check if not trusted only then call this here
            device.Connect()

            return True

        except Exception as e:
            name = connecting_device.get("name", address)
            raise RuntimeError(f"Failed to connect device {name}") from e

    async def on_disconnect(self, address: str) -> bool:
        """
        Disconnect a Bluetooth device by MAC address.
        """
        if not address:
            raise ValueError("Bluetooth address is required to disconnect a device")

        address = address.upper()
        connected_device = await self.on_device()

        if not connected_device or connected_device.get("address") != address:
            return True  # Already disconnected

        # Ensure device exists
        disconnecting_device = await self.on_device(address)
        if not disconnecting_device:
            raise RuntimeError(f"Device {address} not found")

        path = self._addr_to_bluez_path(address)

        try:
            logger.debug(f"Disconnecting Bluetooth device {address} ({path})")

            device = bus.get(BLUEZ_SERVICE, path)

            if hasattr(device, "Disconnect"):
                device.Disconnect()

            return True

        except Exception as e:
            name = disconnecting_device.get("name", address)
            raise RuntimeError(
                f"Failed to disconnect device {name}. Check if Bluetooth is turned on."
            ) from e

    async def on_remove(self, address: str) -> bool:
        """
        Remove a Bluetooth device by MAC address.
        """
        if not address:
            raise ValueError("Bluetooth address is required to remove a device")

        address = address.upper()
        device_info = await self.on_device(address)
        connected_device = await self.on_device()

        if not device_info:
            raise RuntimeError(f"Device {address} not found")

        path = self._addr_to_bluez_path(address)

        try:
            if connected_device and connected_device.get("address") == address:
                await self.on_disconnect(address)

            ADAPTER.RemoveDevice(path)

            self._core.send(event="bluetooth_device_removed", device=device_info)
            logger.info(
                f"Bluetooth device removed: {device_info.get('name')} {address}"
            )

            return True

        except Exception as e:
            name = device_info.get("name", address)
            raise RuntimeError(
                f"Failed to remove device {name}. Check if Bluetooth is turned on."
            ) from e

    def on_device_command(self, mac_address: str, command: str) -> bool:
        """
        Send a player command to a Bluetooth device by MAC address.
        Supported commands: 'Play', 'Pause', 'Stop', 'Next', 'Previous'
        """
        mac_address = mac_address.upper()
        path = self._addr_to_bluez_path(mac_address)
        device = bus.get(BLUEZ_SERVICE, path)

        if not hasattr(device, command):
            logger.warning(f"Device {mac_address} does not support {command}")
            return False

        getattr(device, command)()
        logger.debug(f"Sent command '{command}' to device {mac_address}")
        return True

    async def on_set_volume(
        self,
        address: str,
        volume: int | None = None,
        soft_volume: bool = False,
        mute: bool = False,
    ) -> None:
        """
        Set Bluetooth TX volume for a device using BlueALSA.
        Accepts volume in range 0–100 and maps to 0–127.
        """
        address = address.upper()
        volume = max(0, min(100, volume))
        alsa_volume = round(volume * 127 / 100)
        self._volume = volume

        if mute:
            alsa_volume = 0

        pcm_path = f"/org/bluealsa/hci0/dev_{address.replace(':', '_')}/a2dpsrc/sink"

        try:
            pcm = bus.get("org.bluealsa", pcm_path)
        except Exception as e:
            raise RuntimeError(f"Failed to get PCM device for {address}") from e

        pcm.SoftVolume = soft_volume
        pcm.Volume = [alsa_volume, alsa_volume]

        logger.debug(f"Bluetooth device {address} volume {alsa_volume}, mute {mute}")

        return True

    def _bluez_path_to_addr(self, path: str) -> str:
        """
        Convert BlueZ device path to MAC address using regex.
        Example: '/org/bluez/hci0/dev_8C_85_90_C9_1D_18' -> '8C:85:90:C9:1D:18'
        """
        if not path:
            return

        match = re.search(r"dev_([0-9A-Fa-f]{2}(?:_[0-9A-Fa-f]{2}){5})$", path)
        if not match:
            raise ValueError(f"Invalid BlueZ device path: {path}")

        mac = match.group(1).replace("_", ":").upper()
        return mac

    def _addr_to_bluez_path(self, address: str, adapter: str = "hci0") -> str:
        _MAC_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")
        if not _MAC_RE.match(address):
            raise ValueError(f"Invalid Bluetooth address: {address}")

        addr = address.upper().replace(":", "_")
        return f"/org/bluez/{adapter}/dev_{addr}"

    def _bluealsa_to_pcm(self, address: str) -> str:
        """Convert a BlueALSA D-Bus object path to a PCM path."""
        bluealsa_mgr = bus.get(BLUEALSA_SERVICE, BLUEALSA_MANAGER)
        pcm_objs = bluealsa_mgr.GetManagedObjects()
        path = f"/org/bluealsa/hci0/dev_{address.replace(':', '_')}/a2dpsrc/sink"
        pcm_info = pcm_objs.get(path, {}).get(BLUEALSA_PCM, {})
        return pcm_info

    def _bluealsa_aplay_to_pcm(self):
        """Gets a bluetooth PCM Information."""
        try:
            result = subprocess.check_output(["bluealsa-aplay", "-l"], text=True)
            lines = result.splitlines()
            for line in lines:
                if "A2DP" in line:
                    match = re.search(
                        r"A2DP \((.*?)\): (.*?) (\d+) channels (\d+) Hz", line
                    )
                    if match:
                        codec, fmt, channels, rate = match.groups()
                        _tl_track = self._tl_track.track.copy(
                            update={
                                "sample_rate": int(rate),
                                "audio_codec": codec,
                                "bit_depth": fmt,
                                "channels": int(channels),
                            }
                        )
                        self._tl_track = TlTrack(0, track=_tl_track)
                        self._core._request(
                            "playback.set_metadata", tl_track=self._tl_track
                        )

        except Exception as e:
            return {"error": str(e)}

    def _decode_bluealsa_format(self, fmt):
        """Decode BlueALSA format integer to human-readable PCM format"""
        if fmt is None:
            return None

        mapping = {
            33296: "S16_LE",
            32784: "S24_LE",
            32808: "S32_LE",
        }
        return mapping.get(fmt, None)

    async def _update_pcm(self, new_pcm=None):
        """Switches between PCM Device and bluealsa for RX/TX Mode"""
        if not self._device:
            new_pcm = "null_device"

        if new_pcm is None:
            new_pcm = self._device

        with open(ASOUNDRC_PATH, "r") as f:
            content = f.read()

        match = re.search(r'pcm\s+"([^"]+)"', content)
        current_pcm = match.group(1) if match else None

        if current_pcm == new_pcm:
            return

        updated_content = re.sub(r'pcm\s+"[^"]+"', f'pcm "{new_pcm}"', content)
        with open(ASOUNDRC_PATH, "w") as f:
            f.write(updated_content)

        logger.debug(f"PCM device updated to {new_pcm}")
        self._restart_camilladsp()

    def _restart_camilladsp(self):
        """Restarts Camilla DSP after pcm device update"""
        subprocess.run(
            ["sudo", "/bin/systemctl", "restart", "camilladsp.service"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.debug("Restarted Camilla DSP")

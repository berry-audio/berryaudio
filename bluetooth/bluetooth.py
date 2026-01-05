import logging
import pydbus
import asyncio
import subprocess
import threading
import re
import os

from gi.repository import GLib
from pathlib import Path
from typing import Dict, List
from core.actor import Actor
from core.models import Image, RefType, Album, Artist, Ref, Track, TlTrack, Source
from core.types import PlaybackState

logger = logging.getLogger(__name__)

discovery_time = 15

bus = pydbus.SystemBus()
BLUEZ_SERVICE = 'org.bluez'
BLUEZ_ADAPTER = 'org.bluez.Adapter1'
BLUEZ_DEVICE = 'org.bluez.Device1'
ADAPTER_PATH = '/org/bluez/hci0'

mngr = bus.get(BLUEZ_SERVICE, '/')
adapter = bus.get(BLUEZ_SERVICE, ADAPTER_PATH) 
bluez = bus.get("org.freedesktop.DBus", "/org/bluez")

bluetooth_aplay_path = "/usr/bin/bluealsa-aplay"
bluetooth_agent_path = "/usr/bin/bt-agent"

class BluetoothExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db
        self._config = config
        self._devices = []
        self._track_mem = None
        self._tl_track = TlTrack(0, track=Track())
        self._name = self._config['system']['hostname']
        self._device = self._config['playback']['output_device']
        self._proc_aplay = None
        self._proc_agent = None
        self._source = Source(type='bluetooth', controls=[], state={'connected': False}) 
        self._source_active = False


    async def on_start(self):
        if not os.path.exists(bluetooth_agent_path):
            logger.error("Bluetooth agent service missing")
            return

        if not os.path.exists(bluetooth_aplay_path):
            logger.error("Bluetooth aplay service missing")
            return

        logger.info("Started")
        self.on_adapter_set_state(False)
        threading.Thread(target=self._init_agent, daemon=True).start()
        bus.subscribe(
            iface="org.freedesktop.DBus.Properties",
            signal="PropertiesChanged",
            signal_fired=self._properties_changed
        )


    async def on_event(self, message):
        pass


    async def on_stop(self):
        if self._proc_agent is not None:
            self._proc_agent.terminate()
            self._proc_agent.kill()
        logger.info("Stopped")


    async def on_start_service(self):
        self._source_active = True
        self._reset_meta()
        self.on_adapter_set_state(True)
        self._core._request("source.update_source", source=self._source)
        if self.on_device():
            self._init_aplay()
        else:    
            self._core.send(event="bluetooth_state_changed", state=self.on_adapter_get_state())
        logger.info(f"Started Bluetooth with name {self._name} on {self._device}")
        return True
    

    async def on_stop_service(self):
        await self._core.request("playback.clear")
        self._source_active = False
        self._stop_aplay()
        self.on_adapter_set_state(False)
        logger.debug('Stopped service')          
        return True
    

    def _init_agent(self):
        if os.path.exists(bluetooth_agent_path):
            cmd = [
                bluetooth_agent_path,
                "-c",
                "NoInputNoOutput"
            ]
            logger.info(f"Started Bluetooth agent service")  
            self._proc_agent = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            logger.error(f"Bluetooth agent service not found {bluetooth_agent_path}")  
        
        
    def _init_aplay(self):
        """Bluetooth Alsa Play service"""
        if os.path.exists(bluetooth_aplay_path):
            def _proc_aplay():
                cmd = [
                        bluetooth_aplay_path,
                        "--pcm", self._device,
                        "--profile-a2dp"
                    ]
                logger.info(f"Started Bluetooth aplay service")  
                
                self._proc_aplay = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            threading.Thread(target=_proc_aplay, daemon=True).start()
        else:
            logger.error(f"Bluetooth aplay service not found {bluetooth_aplay_path}")  


    def _stop_aplay(self):
        if self._proc_aplay is not None:
            self._proc_aplay.terminate()
            self._proc_aplay.kill()


    def _reset_meta(self, _track = {}):
        """Stop prev playback & reset meta info"""
        self._tl_track = TlTrack(0, track=Track())
        self._core._request("playback.set_metadata", tl_track=self._tl_track)


    def _properties_changed(self, *args):
        interface = args[1]
        params = args[4]

        if ADAPTER_PATH in interface:
            properties = params[1]
            logger.debug(properties)

            if "Status" in properties:
                if (properties["Status"] == 'playing'):
                    if self._source_active:
                        self._core._request("playback.set_state", state=PlaybackState.PLAYING)
                   
                if (properties["Status"] == 'paused'):
                    if self._source_active:
                        self._core._request("playback.set_state", state=PlaybackState.PAUSED)

            if ("Connected" in properties or "Bonded" in properties) and not "Player" in properties:
                is_connected = properties.get("Connected")
                is_bonded = properties.get("Bonded")
                connected_device = self.on_device()

                if not is_connected or not is_bonded:
                    disconnected_device = self.on_device(interface)
                    self._source.state.connected = False
                    self._source.state.name = None
                    self._source.state.icon = None
                    self._source.state.address = None
                    
                    self._tl_track = TlTrack(0, track=Track())
                    if self._source_active:
                        self._core._request("playback.set_metadata", tl_track=self._tl_track)
                        self._core._request("playback.set_state", state=PlaybackState.STOPPED)
                    
                    if disconnected_device:
                        self._core.send(event="bluetooth_device_disconnected", device=disconnected_device)
                        logger.info(f'Bluetooth device disconnected: {disconnected_device.get("name")} {disconnected_device.get("address")}')
                    
                    self._core.send(event="bluetooth_state_changed", state=self.on_adapter_get_state())
                        

                if connected_device or is_bonded:
                    for device in self._devices:
                        device_path = device.get("path")
                        if device_path != connected_device.get("path"):
                            self.on_disconnect(device_path)
                    
                    self._source.state.connected = connected_device.get("connected")
                    self._source.state.name = connected_device.get("name")
                    self._source.state.icon = connected_device.get("icon")
                    self._source.state.address = connected_device.get("address")

                    self._stop_aplay()
                    self._reset_meta()
                    self._init_aplay()
                    
                    async def _pcm_task():
                        # we have to wait for aplay to start
                        await asyncio.sleep(1)
                        self._pcm_info()

                    asyncio.create_task(_pcm_task())

                    self._core.send(event="bluetooth_device_connected", device=self.on_device(interface))
                    self._core.send(event="bluetooth_state_changed", state=self.on_adapter_get_state())
                    logger.info(f'Bluetooth device connected: {self._source.state.name} {self._source.state.address}')

                if self._source_active:
                    self._core._request("source.update_source", source=self._source)


            if "Track" in properties:
                self._pcm_info()
                
                _track = properties.get("Track")
                if _track:
                    _tl_track = self._tl_track.track.copy(update={
                        "name": _track.get("Title") if _track.get("Title") else 'Bluetooth', 
                        "artists": frozenset([Artist(name=_track.get("Artist"))]),
                        "albums": [Album(name = _track.get("Album"))],
                        "track_no": int(_track["TrackNumber"]) if _track.get("TrackNumber") else 0,
                        "length": int(_track["Duration"]) if _track.get("Duration") else 0
                        })
                    self._tl_track = TlTrack(0, track=_tl_track)
                    self._core._request("playback.set_metadata", tl_track=self._tl_track)

            if "Discoverable" in properties:
                 self._core.send(event="bluetooth_state_changed", state=self.on_adapter_get_state())

            if "Volume" in properties:
                pass #TODO


    def on_adapter_set_state(self, state):
        """Sets Adapter State """
        get_state = self.on_adapter_get_state()

        if get_state['powered'] == state:
            if state:
                adapter.Set(BLUEZ_ADAPTER, "Discoverable", GLib.Variant("b", True))
            return self.on_adapter_get_state()
        
        try:
            if state:
                adapter.Set(BLUEZ_ADAPTER,"Alias", GLib.Variant("s", self._name))
                adapter.Set(BLUEZ_ADAPTER, "Powered", GLib.Variant("b", True))
                adapter.Set(BLUEZ_ADAPTER, "Discoverable", GLib.Variant("b", True))
                adapter.Set(BLUEZ_ADAPTER, "Pairable", GLib.Variant("b", True))
            else:
                adapter.Set(BLUEZ_ADAPTER, "Discoverable", GLib.Variant("b", False))
                adapter.Set(BLUEZ_ADAPTER, "Pairable", GLib.Variant("b", False))
                adapter.Set(BLUEZ_ADAPTER, "Powered", GLib.Variant("b", False))

            logger.info(self.on_adapter_get_state())     
            return self.on_adapter_get_state()
        
        except Exception:
            raise RuntimeError(f"Failed to set adapter state")


    def on_adapter_get_state(self):
        """Sets Adapter State """
        try:
            return {
                'powered': adapter.Get(BLUEZ_ADAPTER, "Powered"),
                'discoverable': adapter.Get(BLUEZ_ADAPTER, "Discoverable"),
                'pairable': adapter.Get(BLUEZ_ADAPTER, "Pairable"),
                'connected': self.on_device(),
            }
        except Exception:
            raise RuntimeError(f"Failed to get adapter state")
        

    async def on_devices(self, rescan: bool = False):
        """Discover Bluetooth devices or return cached devices"""

        if rescan:
            self.on_adapter_set_state(True)

            logger.info("Scanning for available Bluetooth devices...")
            adapter.StartDiscovery()
            await asyncio.sleep(discovery_time)
            adapter.StopDiscovery()

        mng_objs = mngr.GetManagedObjects()
        devices = []

        for path, interfaces in mng_objs.items():
            device = interfaces.get(BLUEZ_DEVICE)
            if not device or not device.get("Name"):
                continue

            devices.append({
                "path": path,
                "name": device.get("Name"),
                "address": device.get("Address"),
                "alias": device.get("Alias"),
                "icon": device.get("Icon"),
                "connected": device.get("Connected"),
            })

        self._devices = devices
        logger.info(f"Found ({len(devices)}) Bluetooth devices.")
        logger.debug(devices)
        return devices


    def on_device(self, path=None):
        """Get device information by path or currently connected device."""
        mng_objs = mngr.GetManagedObjects()

        def build_device_info(path, device):
            return {
                "path": path,
                "name": device.get("Name"),
                "address": device.get("Address"),
                "alias": device.get("Alias"),
                "icon": device.get("Icon"),
                "connected": device.get("Connected"),
            }
        if path:
            try:
                if path in mng_objs and BLUEZ_DEVICE in mng_objs[path]:
                    device = mng_objs[path][BLUEZ_DEVICE]
                    return build_device_info(path, device)
            except (KeyError, AttributeError):
                pass
            return False

        # No path given — find currently connected device
        for path, props in mng_objs.items():
            device = props.get(BLUEZ_DEVICE)
            if device and device.get("Connected"):
                return build_device_info(path, device)
        return False


    def on_trust(self, path):
        """Trusts a bluetooth devices with mac address"""
        try:
            logger.debug(f"Attempting to Trust to {path}...")
            device = bus.get(BLUEZ_SERVICE, path)
            value = GLib.Variant("b", True)
            device.Set("org.bluez.Device1","Trusted",value)
            return True
        except Exception:
                raise RuntimeError(f"Failed to trust device {path}.Check the path and try again.")
        

    async def on_connect(self, path):
        """Connects to bluetooth device with address."""
        try:
            logger.debug(f"Attempting to connect to {path}...")
            get_new_device = self.on_device(path)
            if get_new_device:
                device = bus.get(BLUEZ_SERVICE, path)
                self._reset_meta()
                self.on_trust(path)
                device.Connect()
            return True
        
        except Exception:
            raise RuntimeError(f"Failed to connect device {path}.Check the path and try again.")


    def on_disconnect(self, path):
        """Disconnects a bluetooth device"""       
        try:
            logger.debug(f"Disconnecting bluetooth device  {path}")
            device = bus.get(BLUEZ_SERVICE, path)
            if hasattr(device, "Disconnect"):
                device.Disconnect()
            return True
        except Exception:
            raise RuntimeError(f"Failed to disconnect device {path}.Check the path and try again.")
        

    async def on_remove(self, path):
        """Removes a bluetooth devices."""
        try:
            self.on_disconnect(path)
            removed_device = self.on_device(path)
            adapter.RemoveDevice(path)
            self._core.send(event="bluetooth_device_removed", device=removed_device)
            logger.info(f'Bluetooth device removed: {removed_device.get("name")} {removed_device.get("address")}')
            return True
        except Exception:
            raise RuntimeError(f"Failed to remove device {path}.Check the path and try again.")


    def _pcm_info(self):
        """Gets a bluetooth PCM Information."""
        try:
            result = subprocess.check_output(["bluealsa-aplay", "-l"], text=True)
            lines = result.splitlines()
            for line in lines:
                if "A2DP" in line:
                    match = re.search(r"A2DP \((.*?)\): (.*?) (\d+) channels (\d+) Hz", line)
                    if match:
                        codec, fmt, channels, rate = match.groups()
                        _tl_track = self._tl_track.track.copy(update={
                            "sample_rate":int(rate), 
                            "audio_codec": codec,
                            "bit_depth": fmt,
                            "channels":int(channels)
                            })
                        self._tl_track = TlTrack(0, track=_tl_track)
                        if self._source_active:
                            self._core._request("playback.set_metadata", tl_track=self._tl_track)   
                 
        except Exception as e:
            return {"error": str(e)}    
        

    def player_stop(self, path):
        """Bluetooth device player Stop command"""
        device = bus.get(BLUEZ_SERVICE, path)
        if hasattr(device, "Stop"):
            device.Stop()
        return True
    

    def player_play(self, path):
        """Bluetooth device player Play command"""
        device = bus.get(BLUEZ_SERVICE, path)
        if hasattr(device, "Play"):
            device.Play()
        return True


    def player_pause(self, path):
        """Bluetooth device player Pause command"""
        device = bus.get(BLUEZ_SERVICE, path)
        if hasattr(device, "Pause"):
            device.Pause()
        return True


    def player_prev(self, path):
        """Bluetooth device player Previous command"""
        device = bus.get(BLUEZ_SERVICE, path)
        if hasattr(device, "Previous"):
            device.Previous()
        return True
    

    def player_next(self, path):
        """Bluetooth device player Next command"""
        device = bus.get(BLUEZ_SERVICE, path)
        if hasattr(device, "Next"):
            device.Next()
        return True
    

    def parse_a2dp_config(self, codec, config):
        if codec == 0:  # SBC
            freq_map = {
                0b10000000: 16000,
                0b01000000: 32000,
                0b00100000: 44100,
                0b00010000: 48000
            }
            channel_map = {
                0b00001000: "Mono",
                0b00000100: "Dual Channel",
                0b00000010: "Stereo",
                0b00000001: "Joint Stereo"
            }

            freq = next((v for k, v in freq_map.items() if config[0] & k), None)
            channel = next((v for k, v in channel_map.items() if config[0] & k), None)
            return {"codec": "SBC", "rate": freq, "channels": channel}

        elif codec == 2:  # AAC
            freq_map = {
                0x80: 8000, 0x40: 11025, 0x20: 12000, 0x10: 16000,
                0x08: 22050, 0x04: 24000, 0x02: 32000, 0x01: 44100,
                0x00: 48000  # fallback
            }
            rate_byte = config[1]
            freq = freq_map.get(rate_byte & 0xFF, "Unknown")
            return {"codec": "AAC", "rate": freq, "channels": "Unknown"}

        return {"codec": f"Unknown ({codec})", "rate": "Unknown", "channels": "Unknown"}


    def _get_audio_pcm_info(self, device_path):
        try:
            mng_objs = mngr.GetManagedObjects()      
            for path in mng_objs:
                device = mng_objs[path].get('org.bluez.MediaTransport1')
                if device is not None and device.get('Device') == device_path:
                    return self.parse_a2dp_config(device.get('Codec'), device.get('Configuration'))

        except Exception as e:
            return f"Error retrieving PCM info: {e}"
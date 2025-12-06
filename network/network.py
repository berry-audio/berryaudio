
#***************************************************************************************
#  Network Connection Manager
#  Author : Varun Gujjar    
#  © Copyright 2025 Berryaudio
# ***************************************************************************************

import logging
import subprocess
import threading
import time
import nmcli

from core.actor import Actor

logger = logging.getLogger(__name__)

CONFIG_WIFI_CHECK_INTERVAL = 5
CONFIG_AP_PASSWORD = '1234567890'

class NetworkExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db
        self._config = config
        self._devices = []
        self._conn_in_progress = False
        self._name = self._config['system']['hostname']


    async def on_start(self):
       threading.Thread(target=self._init_network, daemon=True).start()
       logger.info("Started")


    async def on_event(self, message):
        pass


    async def on_stop(self):
        logger.info("Stopped")


    def _init_network(self):
        doOnce_2 = True
        while True:
            _get_net_devices = self.on_devices()
            for net_device in _get_net_devices:
                device = net_device.get('device')
                state = net_device.get('state')
                connection = net_device.get('connection')
                if device == 'wlan0':
                    if state == 'connected':
                        if doOnce_2:
                            doOnce_2 = False
                            logger.info(f"Wifi connected - {connection}")
                    else:
                        if connection != 'Hotspot':
                            if not self._conn_in_progress:    
                                self.on_ap_mode()
            logger.debug("Network check complete")
            time.sleep(CONFIG_WIFI_CHECK_INTERVAL)


    def on_devices(self):
        self._devices = nmcli.device()
        device_list = []
        for dev in self._devices:
            device_list.append({
                'device': dev.device,
                'type': dev.device_type,
                'state': dev.state,
                'connection': dev.connection
            })
        return device_list


    def on_device(self, ifname):
        network_info = nmcli.device.show(ifname=ifname)
        result = {
            'device': network_info.get('GENERAL.DEVICE'),
            'type': network_info.get('GENERAL.TYPE'),
            'mac_address': network_info.get('GENERAL.HWADDR'),
            'mtu': network_info.get('GENERAL.MTU'),
            'state': network_info.get('GENERAL.STATE'),
            'connection': network_info.get('GENERAL.CONNECTION'),
            'ipv4_address': network_info.get('IP4.ADDRESS[1]').split('/')[0] if '/' in network_info.get('IP4.ADDRESS[1]') else network_info.get('IP4.ADDRESS[1]'),
            'ipv4_gateway': network_info.get('IP4.GATEWAY'),
            'ipv4_dns': network_info.get('IP4.DNS[1]'),
            'ipv4_routes': [
                network_info.get('IP4.ROUTE[1]'),
                network_info.get('IP4.ROUTE[2]')
            ],
            'ipv6_addresses': [
                network_info.get('IP6.ADDRESS[1]'),
                network_info.get('IP6.ADDRESS[2]'),
                network_info.get('IP6.ADDRESS[3]')
            ],
            'ipv6_gateway': network_info.get('IP6.GATEWAY'),
            'ipv6_dns': network_info.get('IP6.DNS[1]'),
            'ipv6_routes': [
                network_info.get('IP6.ROUTE[1]'),
                network_info.get('IP6.ROUTE[2]'),
                network_info.get('IP6.ROUTE[3]'),
                network_info.get('IP6.ROUTE[4]'),
                network_info.get('IP6.ROUTE[5]')
            ]
        }
        return result

        
    def on_ap_mode(self):
        logger.info(f'Starting AP mode with name {self._name} and passkey {CONFIG_AP_PASSWORD}')
        nmcli.device.wifi_hotspot(
            ssid=self._name, 
            password=CONFIG_AP_PASSWORD
            )
        self._core.send(event="network_state_changed", device=self.on_device(ifname='wlan0'), networks=self.on_wifi())
        return True


    def on_disconnect(self, ifname):
        nmcli.device.disconnect(ifname=ifname)
        self._core.send(event="network_state_changed", device=self.on_device(ifname='wlan0'), networks=self.on_wifi())
        return True


    def on_connect(self, ifname):
        nmcli.device.connect(ifname=ifname)
        self._core.send(event="network_state_changed", device=self.on_device(ifname='wlan0'), networks=self.on_wifi())
        return True
    

    def on_device_down(self, name):
        nmcli.connection.down(name=name)
        return True
    

    def on_device_up(self, name):
        nmcli.connection.up(name=name)
        return True


    def on_delete(self, name):
        nmcli.connection.delete(name=name)
        self._core.send(event="network_state_changed", device=self.on_device(ifname='wlan0'), networks=self.on_wifi())
        return True
    

    def on_modify(self, ifname, name, ipv4_address, ipv4_gateway, ipv4_dns, method='auto'):
        self._conn_in_progress = True
        nmcli.connection.modify(name, {
            'ipv4.addresses': f'{ipv4_address}/24' if method == 'manual' else '',
            'ipv4.gateway': ipv4_gateway if method == 'manual' else '',
            'ipv4.dns': ipv4_dns if method == 'manual' else '',
            'ipv4.method': method
        })
        nmcli.connection.down(name)
        nmcli.connection.up(name)
        self._conn_in_progress = False
        self._core.send(event="network_state_changed", device=self.on_device(ifname=ifname), networks=self.on_wifi())
        return True


    def on_connect_wlan(self, ssid, password):
        self._conn_in_progress = True
        nmcli.device.wifi_connect(
            ssid=ssid,
            password=password
            ) 
        self._conn_in_progress = False
        self._core.send(event="network_state_changed", device=self.on_device(ifname='wlan0'), networks=self.on_wifi())
        return True


    def on_wifi(self, rescan=False):
        wifi_devices = nmcli.device.wifi(rescan=rescan)
        discovered_networks = []
        for device in wifi_devices:
            discovered_networks.append({
                'ssid': device.ssid,
                'bssid': device.bssid,
                'mode': device.mode,
                'channel': device.chan,
                'frequency': device.freq,
                'rate': device.rate,
                'signal': device.signal,
                'security': device.security,
                'connected': device.in_use
            })

        logger.debug(f"Found wifi networks - ({str(discovered_networks)}) ")
        return discovered_networks

    
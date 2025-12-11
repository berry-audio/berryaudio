import { REF } from "@/constants/refs";
import { PLAYBACK_STATE, REPEAT_MODE, SHUFFLE_MODE } from "@/constants/states";
import { SelectProps } from "antd";

export interface Artist {
  __model__: "Artist";
  uri: string;
  name: string;
  sortname: string | null;
  musicbrainz_id: string | null;
}

export interface Album {
  __model__: "Album";
  uri: string;
  name: string;
  artists: Artist[];
  num_tracks: number | null;
  num_discs: number | null;
  date: string | null;
  musicbrainz_id: string | null;
}

export interface Image {
  __model__: "Image";
  uri: string;
  width: number | null;
  height: number | null;
}

export interface Track {
  __model__: "Track";
  uri: string;
  name: string;
  artists: Artist[];
  album: Album;
  albums?: Album[];
  composers: Artist[];
  performers: Artist[];
  genre: string | null;
  track_no: number | null;
  disc_no: number | null;
  date: string | null;
  length: number;
  bitrate: number;
  comment: string | null;
  musicbrainz_id: string | null;
  last_modified: number | null;
  images: Image[];
  audio_codec: string;
  sample_rate: number;
  channels: number;
  bit_depth: any;
}

export interface TlTrack {
  __model__: "TlTrack";
  tlid: number;
  track: Track;
}

export interface Playlist {
  __model__: "Playlist";
  uri: string;
  name: string;
  tracks: TlTrack[];
  last_modified: string;
}

export interface Ref {
  __model__: "Ref";
  uri: string;
  name: string;
  type: REF;
  artists: Artist[];
  albums: Album[];
  composers: Artist[];
  performers: Artist[];
  genre: string;
  track_no: number;
  country: string;
  disc_no: number;
  date: string;
  length: number;
  bitrate: number;
  comment: string;
  musicbrainz_id: string | null;
  last_modified: string;
  images: Image[];
}

export interface MediaPlayer {
  source: Source;
  playback_state: PLAYBACK_STATE;
  repeat_mode: REPEAT_MODE;
  shuffle_mode: SHUFFLE_MODE;
  volume: number;
  mute: boolean;
  elapsed_ms: number;
  current_track: TlTrack;
  current_track_cover: string | undefined;
  current_playlist: TlTrack[];
  current_playlist_loading: boolean;
  is_standby: boolean;
}

export interface Source {
  type: string;
  controls?: string[];
  state?: {
    connected?: boolean;
    user_name?: string;
    connection_id?: string;
    name?: string;
    icon?: string;
    address?: string;
  };
}

export interface BluetoothDevice {
  path: string;
  adapter?: string;
  name: string;
  address: string;
  alias: string;
  icon: string;
  paired?: boolean;
  trusted?: boolean;
  bonded?: boolean;
  connected?: boolean;
  class?: number;
}

export interface AdapterState {
  powered: boolean;
  discoverable: boolean;
  pairable: boolean;
  connected: boolean | BluetoothDevice;
}

export interface BluetoothState {
  adapter_state: AdapterState;
  device_connected: undefined | {};
  devices_available: BluetoothDevice[];
}

export interface StorageDevice {
  dev: string;
  parent: string;
  removable: boolean;
  size_bytes: number;
  marketed_gb: number;
  fstype: string;
  label: string;
  status: "mounted" | "unmounted" | "removed";
  mount: string;
  total: number;
  used: number;
  free: number;
  percent: number;
}

export interface StorageInfo {
  mounted: StorageDevice[];
  unmounted: StorageDevice[];
}

export interface NetworkState {
  networks: WifiNetwork[];
  devices: {};
}

export interface NetworkDevice {
  device: string;
  type: string;
  mac_address: string;
  mtu: string;
  state: string;
  connection: string;
  ipv4_address: string;
  ipv4_gateway: string;
  ipv4_dns: string;
  ipv4_routes: string[];
  ipv6_addresses: string[];
  ipv6_gateway: string;
  ipv6_dns: string;
  ipv6_routes: string[];
}

export interface NetworkConnectionInfo {
  name: string;
  uuid: string | null;
  device: string;
  ip_iface: string | null;
  state: string | null;
  is_default: string | null;
  is_default6: string | null;
  vpn: string | null;
  dbus_path: string | null;
  con_path: string | null;
  zone: string | null;
  master_path: string | null;
  connection_id: string | null;
  connection_uuid: string | null;
  connection_type: string | null;
  connection_interface: string | null;
  connection_autoconnect: string | null;
  connection_autoconnect_priority: string | null;
  connection_read_only: string | null;
  connection_timestamp: string | null;
  connection_metered: string | null;
  ethernet_port: string | null;
  ethernet_speed: string | null;
  ethernet_duplex: string | null;
  ethernet_auto_negotiate: string | null;
  ethernet_mac: string | null;
  ethernet_mtu: string | null;
  ipv4_method: string;
  ipv4_dns: string | null;
  ipv4_dns_search: string | null;
  ipv4_dns_options: string | null;
  ipv4_dns_priority: string | null;
  ipv4_addresses: string | null;
  ipv4_gateway: string | null;
  ipv4_route_metric: string | null;
  ipv4_route_table: string | null;
  ipv4_may_fail: string | null;
  ipv4_address: string | null;
  ipv4_gateway_runtime: string | null;
  ipv4_dns_runtime: string | null;
  ipv4_routes: (string | null)[];
  ipv6_method: string | null;
  ipv6_dns: string | null;
  ipv6_dns_priority: string | null;
  ipv6_gateway: string | null;
  ipv6_route_metric: string | null;
  ipv6_route_table: string | null;
  ipv6_addresses: (string | null)[];
  ipv6_gateway_runtime: string | null;
  ipv6_dns_runtime: string | null;
  ipv6_routes: (string | null)[];
}

export interface WifiNetwork {
  ssid: string;
  bssid: string;
  mode: string;
  channel: number;
  frequency: number;
  rate: number;
  signal: number;
  security: string;
  connected: boolean;
}

export type ViewMode = "list" | "grid";

export interface PcmDevice {
  device: string;
  name: string;
  channels_min: number;
  channels_max: number;
  formats: string[];
  supported_rates: string[];
}

export interface SelectOption {
  label: string;
  value: string;
}

export interface CustomSelect<T = any> extends SelectProps<T> {}

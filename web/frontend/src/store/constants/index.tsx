export enum SOCKET_EVENTS {
   SOCKET_CONNECTED = "socket/connected",
   SOCKET_DISCONNECTED = "socket/disconnected",
   SOCKET_EVENT = "socket/event"
}

export enum PLAYER_EVENTS {
   POSITION_UPDATED = "player/position",
   VOLUME_CHANGED ="player/volume"
}

export enum INFO_EVENTS {
   PLAYLISTS_UPDATED = "event/playlists/updated",
   SCAN_UPDATED = "event/scan/library/updated",
   SCAN_ARTIST_UPDATED = "event/scan/library/artist/updated",
   SCAN_BLUETOOTH_COMPLETED = 'event/scan/bluetooth/updated',
   SET_BLUETOOTH_STATE = 'event/set/bluetooth/state'
}

export enum DIALOG_EVENTS {
   DIALOG_CLOSE = "dialog/close",
   DIALOG_PLAYLISTS = "dialog/playlists",
   DIALOG_PLAYLIST_RENAME = "dialog/playist/rename", 
   DIALOG_PLAYLIST_DELETE = "dialog/playist/delete",
   DIALOG_CLEAR_LIBRARY = "dialog/library/clear",
   DIALOG_ADD_LIBRARY = "dialog/library/add",
   DIALOG_SCAN_LIBRARY = "dialog/library/scan",
   DIALOG_INFO_LIBRARY = "dialog/library/info",
   DIALOG_SCAN_LIBRARY_ARTIST = "dialog/library/scan/artist",
   DIALOG_BLUETOOTH_NOT_CONNECTED = "dialog/bluetooth/unavailable",
   DIALOG_REBOOT = "dialog/system/reboot",
   DIALOG_POWER_OPTIONS = "dialog/system/power",
}

export enum OVERLAY_EVENTS {
   OVERLAY_SEARCH = "overlay/search",
   OVERLAY_NOWPLAYING = "overlay/nowplaying",
   OVERLAY_LIBRARY = "overlay/library",
   OVERLAY_VOLUME = "overlay/volume",
   OVERLAY_STANDBY = "overlay/standby",
   OVERLAY_CLOSE = "overlay/close"
}
const dev = import.meta.env.DEV
const dev_host = import.meta.env.VITE_DEV_HOST
const host = dev ? dev_host : window.location.hostname;

export const WEBSOCKET_URL = `ws://${host}:8080/ws`;
export const SERVER_URL = `http://${host}:8080`;
export const CAMILLA_DSP_URL = `http://${host}:8081`;
export const STROKE_WIDTH = 1.5
export const THEME_COLOR = '#0CFFBD'

export const ICON_WEIGHT = 'light'
export const ICON_LG = 40
export const ICON_SM = 25
export const ICON_XS = 20

export const WLAN_DEVICE = 'wlan0'
export const ETH_DEVICE = 'eth0'

export const THEME_TEXT = 'text-yellow-700'

import { ICON_SM, ICON_WEIGHT, SERVER_URL } from "@/constants";
import { REPEAT_MODE, SHUFFLE_MODE } from "@/constants/states";
import { Album, Artist } from "@/types";
import { LaptopIcon, NetworkIcon, WifiHighIcon } from "@phosphor-icons/react";

/**
 * Checks if url contains http, https.
 */
export const isHttpUrl = (url: string): boolean => {
  return /^https?:\/\//i.test(url);
};

/**
 * Returns a comma-separated string of artist names.
 * @param artists - An array of Artist objects.
 * @returns A string listing all artist names, or an empty string if none exist.
 */
export const getArtists = (artists: Artist[]): string => {
  return `${artists?.map((artist: any) => (artist.name?.trim() ? artist.name : undefined)).join(",") || ""}`;
};

/**
 * Returns a comma-separated string of album names.
 * @param albums - An array of Artist objects.
 * @returns A string listing all artist names, or an empty string if none exist.
 */
export const getAlbums = (albums: Album[]): string => {
  return `${albums?.map((album: any) => (album.name?.trim() ? album.name : "Unknown")).join(",") || ""}`;
};

// Determine repeat mode string based on boolean values
export const getRepeatMode = (repeat: boolean, single: boolean): REPEAT_MODE => {
  if (!repeat && !single) return REPEAT_MODE.REPEAT_OFF;
  if (repeat && single) return REPEAT_MODE.REPEAT_SINGLE;
  if (repeat) return REPEAT_MODE.REPEAT_ALL;
  return REPEAT_MODE.REPEAT_OFF;
};

/**
 * Determines shuffle mode based on backend boolean.
 */
export const getShuffleMode = (random: boolean): SHUFFLE_MODE => (random ? SHUFFLE_MODE.SHUFFLE_ON : SHUFFLE_MODE.SHUFFLE_OFF);

/**
 * Converts a duration in ms to mm:ss or hh:mm:ss.
 */
export const convertMillisecondstoTime = (milliseconds: number): string => {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const h = String(hours).padStart(2, "0");
  const m = String(minutes).padStart(2, "0");
  const s = String(seconds).padStart(2, "0");

  return hours ? `${h}:${m}:${s}` : `${m}:${s}`;
};

/**
 * Gets total duration of the track.
 */
export const getTotalDuration = (duration: number) => convertMillisecondstoTime(duration ?? 0);

/**
 * Gets current playback position in formatted time.
 */
export const getPosition = (position: number) => convertMillisecondstoTime(position);

/**
 * Returns the track's bitrate in kbps.
 */
export const getBitrate = (bitrate: number) => `${Math.floor((bitrate ?? 0) / 1000)}kbps`;

/**
 * Returns the track's sample rate in khz.
 */
export const getSampleRate = (samplerate: number) => `${Math.floor((samplerate ?? 0) / 1000)}kHz`;

/**
 * Returns the track'saudio codec shortname.
 */
export const getCodecName = (format: string) => {
  if (!format) return "";

  type CodecFormat =
    | "DSD (Direct Stream Digital), least significant bit first, planar"
    | "Uncompressed 24-bit PCM audio"
    | "Uncompressed 16-bit PCM audio"
    | "MPEG-1 Layer 3 (MP3)"
    | "MPEG-1 Layer 2 (MP2)"
    | "MPEG-4 AAC"
    | "MPEG-2 AAC"
    | "Free Lossless Audio Codec (FLAC)";

  const mapping: Record<CodecFormat, string> = {
    "DSD (Direct Stream Digital), least significant bit first, planar": "DSD",
    "Uncompressed 24-bit PCM audio": "PCM",
    "Uncompressed 16-bit PCM audio": "PCM",
    "MPEG-1 Layer 3 (MP3)": "MP3",
    "MPEG-1 Layer 2 (MP2)": "MP2",
    "MPEG-4 AAC": "AAC",
    "MPEG-2 AAC": "AAC",
    "Free Lossless Audio Codec (FLAC)": "FLAC",
  };

  return mapping[format as CodecFormat] || format;
};

/**
 * Returns the source fullname.
 */
export const getSourceName = (type: string) => {
  if (!type) return "Unknown";

  type SourceType = "bluetooth" | "spotify" | "shairportsync" | "none";

  const mapping: Record<SourceType, string> = {
    bluetooth: "Bluetooth",
    spotify: "Spotify Connect",
    shairportsync: "Airplay",
    none: " ",
  };

  return mapping[type as SourceType] || type;
};

/**
 * Returns the track's bit dept rate in bits.
 */
export const getBitDepth = (format: string) => {
  if (!format) return "";

  type AudioFormat = "S16_LE" | "S24_32LE" | "S16" | "S24_LE" | "S32_LE" | "S16_BE" | "S24_BE" | "S32_BE" | "S16LE" | "S24LE" | "F32LE";

  const mapping: Record<AudioFormat, string> = {
    S16_LE: "16bit",
    S16: "16bit",
    S24_LE: "24bit",
    S24_32LE: "32bit",
    S32_LE: "32bit",
    S16_BE: "16bit",
    S24_BE: "24bit",
    S32_BE: "32bit",
    S16LE: "16bit",
    S24LE: "24bit",
    F32LE: "32bit",
  };

  return mapping[format as AudioFormat] || format;
};
/**
 * Returns array to comma seperated list
 */
export const arrayToText = (array: []) => {
  return array?.map((item: any) => item).join(", ");
};

export const getImage = (imageUri: string) => {
  const isRemote = isHttpUrl(imageUri);
  return imageUri ? (isRemote ? imageUri : `${SERVER_URL}${imageUri}`) : undefined;
};

/**
 * Returns MB or GB
 */
export function formatSize(mb: number): string {
  if (mb < 1024) {
    return `${mb.toFixed(2)} MB`;
  } else {
    const gb = mb / 1024;
    return `${gb.toFixed(2)} GB`;
  }
}

/**
 * Convert a size in bytes into a human-readable string
 * (B, KB, MB, GB, TB …) with two decimal places.
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  const value = bytes / Math.pow(k, i);
  return `${value.toFixed(2)} ${units[i]}`;
}

export const formatNo = (no: number) => {
  return String(no).padStart(2, "0");
};

/**
 * Split a "type:id" URI into name and numeric id.
 * @param {string} uri - The URI string (e.g. "playlist:42").
 * @returns {{ name: string, id: number }} The parsed name and id.
 */
export const splitUri = (uri: string) => {
  const [name, id] = uri.split(":");
  return { name, id };
};

export const formatDate = (dateString: string): string => {
  const isoString = dateString.replace(" ", "T");
  const date = new Date(isoString);
  const day = date.getDate();
  const month = date.toLocaleString("en-US", { month: "short" });
  const year = date.getFullYear();
  return `${day} ${month}, ${year}`;
};

/**
 * Returns the track'saudio codec shortname.
 */
export const getPCMPlaybackName = (device_name: string) => {
  if (!device_name) return "";

  type PCMDevice = "Loopback" | "bcm2835 Headphones" | "RPi DAC+" | "vc4-hdmi-0" | "vc4-hdmi-1";

  const mapping: Record<PCMDevice, string> = {
    Loopback: "Loopback",
    "bcm2835 Headphones": "Headphones",
    "RPi DAC+": "DAC+",
    "vc4-hdmi-0": "HDMI-0",
    "vc4-hdmi-1": "HDMI-1",
  };

  return mapping[device_name as PCMDevice] || device_name;
};

/**
 * Returns the network name and icon
 */
export const getNetworkDeviceName = (device: string) => {
  return (
    <>
      {device === "wlan0" ? (
        <>
          <WifiHighIcon weight={ICON_WEIGHT} size={ICON_SM} className="mr-2" />
        </>
      ) : device === "eth0" ? (
        <>
          <LaptopIcon weight={ICON_WEIGHT} size={ICON_SM} className="mr-2" />
        </>
      ) : (
        <>
          <NetworkIcon weight={ICON_WEIGHT} size={ICON_SM} />
        </>
      )}
    </>
  );
};

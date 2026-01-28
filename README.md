![Description](/web/frontend/public/assets/berryaudio_logo_dark.png)

Berryaudio is a diy open source audiophile audio player / streamer for **[Raspberry Pi](https://www.raspberrypi.com/)** designed for for pure music listening experience with a beautifully crafted, responsive, touch-optimized user interface.
— No ads, no subscription, just pure rich, high-resolution playback and a sleek beautiful responsive UI for your DAC setup.

Built using **gstreamer**, **python** as server, **reactjs** & **typescript** as client, designed for smooth performance across touch displays, Building your own custom music system headless or with an attached display.

![Description](/web/frontend/public/assets/screenshot.png)

> "As an audiophile, a software engineer, and someone who loves building own products, I’ve always wanted an audio system/streamer built with my own preferred tech stack—something modern, intuitive, and truly customizable. With modern hardware,computing power and with a vision to preserve offline experiences & privacy, I’m convinced you can build almost anything without relying on the cloud services.
> After years of missing the simplicity of Winamp and the smart features of old MusicMatch (some of you might not even remember those days), along with the charm of classic audio systems, I finally decided to create something for myself. So today, I’m starting that journey: building a DAC setup that blends the best of modern features with the soul of legacy audio systems." - Varun Gujjar
>
> A big thank you to the **Moode** and **Mopidy** communities for their research and hard work, which greatly inspired and influenced the development of this project.

> [!NOTE]
> The developer of this application is not liable for any misuse or legal issues arising from its
> use and is not affiliated with any content providers. This application hosts zero content.
>
> Berryaudio is intended for offline use only by default; the user manages any external sources. Berryaudio does
> not condone or supports piracy.

## Overview

- Designed for the Raspberry Pi (should also work on other single board computers)
- Supports MP3, FLAC, WAV, OGG, DSD, DSF, and other formats, with detailed codec info, ID3 tag reading, and cover art extraction.
- Bluetooth streaming, AirPlay 2, Spotify Connect, and built-in file browser for easy library management.
- Bluetooth receiver and transmitter support (Handles automatically based on device connected)
- Multi-room synchronized audio playback 
- Curated list of 200+ radio stations, including major providers like BBC and SomaFM.
- Full ID3 tag support, music scanning, and automatic artist info from TheAudioDB.com.
- Create and manage playlists with touch-friendly drag-and-drop sorting and playback modes (Repeat, Shuffle).
- Supports SD cards, USB HDD and SSD drives.
- Manage Bluetooth, view system stats, and control power options (Shutdown, Reboot, Standby).
- Manage wireless & ethernet network, Hotspot, IP configurations direclty from the interface
- No need to install any app can be fully controlled using a responsive web interface.

## Application

- Turn your old Amp or Bluetooth speaker(with AUX input) into a Jukebox/Multiroom/Wifi Streaming device
- Using it as an independent DAC Setup with touch screen

## Download

You can download the ready image based on Bookworm OS from the following link
[berryaudio_latest.img.zip](http://berryaudio.org/berryaudio_latest.img.zip)\
Scroll below to see a list of supported hardware

## Getting Started

Installation guides, SD card flashing instructions, and hardware compatibility & features.

- [Documentation](https://docs.berryaudio.org/)
- [Getting Started](https://docs.berryaudio.org/getting-started/introduction.html)
- [Installation & Setup](https://docs.berryaudio.org/getting-started/installation.html)
- [Community Forum](https://community.berryaudio.org/)
- [Website](https://www.berryaudio.org/)

## Supported Hardware
- [Raspberry Pi Boards](https://docs.berryaudio.org/getting-started/supported-hardware.html#supported-raspberry-pi)
- [Audio Boards](https://docs.berryaudio.org/getting-started/supported-hardware.html#supported-dac-adc)


## Features

### Playback

- Supports MP3, M4A, MP4, AAC, FLAC, OGG, OPUS, WMA, WAV and DSF (Supported DAC only) audio formats.
- Reads ID3 tags and extracts cover art from various file types
- Displays detailed audio codec, sample rate and bit-depth information
- Fast search by artist, album and track

### Sources

- Bluetooth streaming with aptX, LDAC, SBC XQ+, with metadata display (Supported devices only)
- Use as a Bluetooth receiver or transmitter
- AirPlay 2 receiver (PCM 44 kHz / 32-bit), supports cover art & metadata display ([Shairport Sync](https://github.com/mikebrady/shairport-sync))
- Spotify Connect supports cover art & metadata display ([Librespot](https://github.com/librespot-org/librespot))
- Built-in File Browser for easy navigation and library management

### Multiroom

- Synchronized audio playback across multiple rooms
- Low-latency streaming with Snapcast (PCM, FLAC, Opus, Ogg)
- Group and manage multiple audio clients easily
- Perfectly in-sync playback between devices
- Client and server-side volume control management
- Can be used as a receiver or transmitter

### Internet Radio

- Curated list of 200+ radio stations
- Includes Pop, Rock, 80s, News, and more
- Features major radio stations from providers such as BBC, Flux FM and SomaFM

### Library

- Full ID3 tag and cover art support for various file formats
- Scan for music from multiple storage locations
- Automatically download artist information from TheAudioDB.com [AudioDB](https://www.theaudiodb.com/)
- Browse your library by Artist, Album, Genre and Tracks
- Add artists or albums directly to playlists & queue
- Infinite query based smooth scroll to support large music libraries

### Playlists

- Create and manage playlists
- Touch-friendly drag & drop sortable playlists and the Now Playing queue
- Playback modes: Repeat All, Repeat One and Shuffle

### Storage

- Supports SD Card
- External USB Pen Drives & HDD Drives
- Mounts & Un-Mounts Automatically
- NVME & PCle (not tested but should work)

### Networking

- Scan and manage Bluetooth devices via D-Bus
- Discover and manage Wi-Fi networks
- Enables Wi-Fi hotspot if no wireless network connected
- Manage Ethernet connection
- Configure IP settings (manual/static or DHCP)

### Power

- View CPU, memory, and internal storage usage stats
- Shutdown, Reboot, and Standby options available from the interface
- Standby screen displays local date and time

### Camilla DSP

- Supports all DSP features [Camilla DSP](https://github.com/HEnquist/camilladsp)
- Supports high-quality filters, routing, mixing, and gain control
- Create custom EQ profiles (PEQ, GEQ, FIR, IIR filters)
- Load and switch between multiple DSP presets
- Real-time DSP updates without restarting playback
- Supports high-resolution audio pipelines (up to 32-bit / 384 kHz depending on hardware)

### Coming Soon

- DLNA
- Network folder sharing
- And More ...

## License

Berry Audio is released under the MIT License.  
Fork it, modify it, and build your perfect listening setup.

## Contributing

We welcome your contributions! Based on functionality and code quality, contributions may be integrated directly into the core system or offered as user-contributed modules that can be installed separately.

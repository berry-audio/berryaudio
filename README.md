![Description](/web/frontend/public/assets/berryaudio_logo_dark.png)


Berryaudio is a diy open source audiophile audio player / streamer for **[Raspberry Pi](https://www.raspberrypi.com/)** designed for for pure music listening experience with a beautifully crafted, responsive, touch-optimized user interface.
 — No ads, no subscription, just pure rich, high-resolution playback and a sleek beautiful responsive UI for your DAC setup.

Built using  **gstreamer**, **python**, **reactjs** & **typescript**, designed for smooth performance across touch displays, Building your own custom music system headless or with an attached display.

![Description](/web/frontend/public/assets/screenshot.png)


> "With a motivation of building my own products and as a music and tech enthusiast, I always wanted a music player built with my favorite stack that is modern, intuitive & customizable. After missing the simplicity of Winamp and the smart features of MusicMatch from years and music systems from the past, I decided to build something for my own and thought it would be something worth sharing ?" - Varun Gujjar
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
- Curated list of 200+ radio stations, including major providers like BBC and SomaFM.
- Full ID3 tag support, music scanning, and automatic artist info from TheAudioDB.com.
- Create and manage playlists with touch-friendly drag-and-drop sorting and playback modes (Repeat, Shuffle).
- Supports SD cards, USB drives, and auto mounts.
- Manage Bluetooth, view system stats, and control power options (Shutdown, Reboot, Standby).
- High-quality audio filters, EQ profiles, and real-time DSP updates.

## Download
You can download the ready image based on Bookworm OS from the following link
[berryaudio_v1.0.0.img.zip](http://berryaudio.org/berryaudio_v1.0.0.img.zip)


## Getting Started
Installation guides, SD card flashing instructions, and hardware compatibility details will be shared here.
- **Installation Guide**: [Coming Soon](https://placeholder-link-to-wifi-setup.com)
- **Community Forum**: [community.berryaudio.org](https://community.berryaudio.org/)
- **Website**: [www.berryaudio.org](https://www.berryaudio.org/)


## Features

### Playback

- Supports MP3, M4A, MP4, AAC, FLAC, OGG, OPUS, WMA, WAV, and DSF audio formats. 
- Reads ID3 tags and extracts cover art from various file types
- Displays detailed audio codec, sample rate, and bit-depth information
- Fast search by artist, album, and track

### Sources

- Bluetooth streaming with aptX, LDAC, SBC XQ+, with metadata display (Supported devices only)
- AirPlay 2 receiver (PCM 44 kHz / 32-bit), supports  cover art & metadata display  ([Shairport Sync](https://github.com/mikebrady/shairport-sync))
- Spotify Connect supports cover art & metadata display ([Librespot](https://github.com/librespot-org/librespot))
- Built-in File Browser for easy navigation and library management

### Internet Radio

- Curated list of 200+ radio stations
- Includes Pop, Rock, 80s, News, and more
- Features major radio stations from providers such as BBC, Flux FM, and SomaFM

### Library

- Full ID3 tag and cover art support for various file formats
- Scan for music from multiple storage locations
- Automatically download artist information from TheAudioDB.com [AudioDB](https://www.theaudiodb.com/)
- Browse your library by Artist, Album, Genre, and Tracks
- Add artists or albums directly to playlists & queue
- Infinite, query based scroll to support large libraries

### Playlists

- Create and manage playlists
- Touch-friendly drag & drop sortable playlists and the Now Playing queue
- Playback modes: Repeat All, Repeat One, and Shuffle


### Storage

- Supports SD Card
- External USB Pen Drives & HDD Drives
- Mounts & Un-Mounts Automatically
- NVME & PCle (not tested but should work)


### Networking & Power

- Scan and manage Bluetooth devices over D-Bus
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

### Supported Single Board Computers

- Raspberry pi 4B [Link](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
- Pi Zero 2W [Link](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
- Have not tested but should work with other Pi Boards
- If you have tested on any other hardware please feel free to share them.

### Supported DACs

- DAC+ [Link](https://www.raspberrypi.com/products/dac-plus/)
- PCM5122 HIFI I2S DAC + [Link](https://www.waveshare.com/pcm5122-audio-board-a.htm)
- Have not tested but should work with other natively supported DAC boards
- If you have tested on any other hardware please feel free to share them.


### In Progress

- Snapcast Multiroom
- DLNA
- Wifi Management
- Network folder sharing

## License

Berry Audio is released under the MIT License.  
Fork it, modify it, and build your perfect listening setup.


## Contributing

We welcome your contributions! Based on functionality and code quality, contributions may be integrated directly into the core system or offered as user-contributed modules that can be installed separately.


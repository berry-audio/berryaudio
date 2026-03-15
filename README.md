![Description](https://github.com/berry-audio/ba-frontend/blob/main/public/assets/berryaudio_logo_dark.png)

> ⭐ If this project helps you, consider 
> [Buy me a Coffee](https://www.buymeacoffee.com/varungujjar)
> to keep it alive and maintained. 



Berryaudio is a diy open source audiophile audio player / streamer for **[Raspberry Pi](https://www.raspberrypi.com/)** designed for for pure music listening experience with a beautifully crafted, responsive, touch-optimized user interface.
— No ads, no subscription, just pure rich, high-resolution playback and a sleek beautiful responsive UI for your DAC setup.

Built using **gstreamer**, **python** as server, **reactjs** & **typescript** as client, designed for smooth performance across touch displays, Building your own custom music system headless or with an attached display.

![Description](https://www.berryaudio.org/images/screenshot.png)

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
- **New: Network folder sharing from mounted drives**
- Manage Bluetooth, view system stats, and control power options (Shutdown, Reboot, Standby).
- Manage wireless & ethernet network, Hotspot, IP configurations direclty from the interface
- No need to install any app can be fully controlled using a responsive web interface.

## Application

- Turn your old Amp or Bluetooth speaker(with AUX input) into a Jukebox/Multiroom/Wifi Streaming device
- Using it as an independent DAC Setup with touch screen

## Download

You can download the ready image based on Bookworm OS from the following link
[berryaudio_v3.0.0.img.zip](http://berryaudio.org/berryaudio_latest.img.zip)\
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

- Supports **MP3, M4A, MP4, AAC, FLAC, OGG, OPUS, WMA, WAV, and DSF** audio formats *(DSF requires a supported DAC)*  
- Reads **ID3 tags** and extracts **embedded cover art** from various file types  
- Displays detailed **audio codec, sample rate, and bit-depth information**  
- Fast search by **artist, album, and track**

### Sources

- **Bluetooth streaming** with **aptX, LDAC, SBC XQ+**, including metadata display *(supported devices only)*  
- Can be used as a **Bluetooth receiver or transmitter**  
- **AirPlay 2 receiver** *(PCM 44/48 kHz / 32-bit)* with cover art & metadata display — powered by [Shairport Sync v5.0](https://github.com/mikebrady/shairport-sync)  
- **Spotify Connect** with cover art & metadata display — powered by [Librespot](https://github.com/librespot-org/librespot)  
- Built-in **File Browser** for easy navigation and library management  

### Display

- Supports **SSD1322, SSD1306, and Waveshare 2.8" DSI displays** with new fonts and icons — ([Display wiring guide](https://docs.berryaudio.org/display/generic-hdmi.html))  
- OLED displays *(SSD1322 & SSD1306)* include **Spectrum Analyzer modes and a Retro VU Meter visualizer**

### Multiroom

- **Synchronized audio playback** across multiple rooms  
- **Low-latency streaming** with **Snapcast** *(PCM, FLAC, Opus, Ogg)*  
- Easily **group and manage multiple audio clients**  
- **Perfectly synchronized playback** between devices  
- **Client and server-side volume control**  
- Can be used as a **receiver or transmitter**

### Internet Radio

- **Curated list of 200+ radio stations**  
- Includes **Pop, Rock, 80s, News, and more**  
- Features major stations such as **BBC, FluxFM, and SomaFM**

### Library

- Full **ID3 tag and cover art support** across various file formats  
- Scan and index music from **multiple storage locations**  
- Automatically download **artist information** from [TheAudioDB](https://www.theaudiodb.com/)  
- Browse music by **Artist, Album, Genre, and Tracks**  
- Add **artists or albums directly to playlists or the queue**  
- **Infinite query-based smooth scrolling** for large music libraries  

### Playlists

- **Create and manage playlists**  
- **Touch-friendly drag-and-drop** sorting for playlists and the **Now Playing queue**  
- Playback modes: **Repeat All, Repeat One, and Shuffle**

### Storage

- Supports **SD cards**  
- Supports **external USB drives** *(pen drives & HDDs)*  
- **Automatic mount and unmount** for connected storage devices  
- Supports **NVMe & PCIe storage** *(not fully tested but expected to work)*  
- **SMB network folder sharing** from mounted drives  
- Supports adding **remote NAS storage** from **Windows, macOS, and other network locations**

### Networking

- Scan and manage **Bluetooth devices via D-Bus**  
- Discover and manage **Wi-Fi networks**  
- Automatically enables a **Wi-Fi hotspot if no network is connected**  
- Manage **Ethernet connections**  
- Configure **IP settings** *(DHCP or manual/static)*

### Power

- View **CPU, memory, and storage usage statistics**  
- **Shutdown, reboot, and standby** controls from the interface  
- Standby screen displays **local date and time**

### Camilla DSP

- Supports all DSP features of [CamillaDSP](https://github.com/HEnquist/camilladsp)  
- Advanced **filtering, routing, mixing, and gain control**  
- Create custom **EQ profiles** *(PEQ, GEQ, FIR, IIR filters)*  
- **Load and switch between multiple DSP presets**  
- **Real-time DSP updates** without restarting playback  
- Supports **high-resolution audio pipelines** *(up to 32-bit / 384 kHz depending on hardware)*

### Coming Soon

- DLNA
- GPIO Buttons
- Infrared Remote
- FM Tuner
- Line In Audio

## Hardware

Berryaudio has been tested on the following Raspberry Pi (Bookworm OS). While it should work with other versions of Pi aswell feel free to share your tests so it can be added to the list below.

<table>
    <thead>
        <tr>
        <th width="40%">Version</th>
        <th width="50%">Description</th>
        <th width="5%">Link</th>
        <th width="5%">Status</th>
        </tr>
    </thead>
    <tbody>
            <tr>
        <td>Raspberry Pi Zero</td>
        <td>CPU: BCM2835 @ 1 GHz Memory: 512 MB Wi‑Fi: None Bluetooth: None</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-zero/">Link</a></td>
        <td>-</td>
    </tr>
    <tr>
        <td>Raspberry Pi Zero W</td>
        <td>CPU: BCM2835 @ 1 GHz Memory: 512 MB Wi‑Fi: 802.11n Bluetooth: 4.0/BLE</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-zero/">Link</a></td>
        <td>-</td>
    </tr>
    <tr>
        <td>Raspberry Pi Zero 2 W</td>
        <td>CPU: Quad‑core Cortex‑A53 @ 1 GHz Memory: 512 MB Wi‑Fi: 802.11n Bluetooth: 4.2/BLE</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/">Link</a></td>
        <td>Tested</td>
    </tr>
    <tr>
        <td>Raspberry Pi 1 Model B+</td>
        <td>CPU: BCM2835 Memory: 512 MB Wi‑Fi: None Bluetooth: None</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-1-model-b-plus/">Link</a></td>
        <td>-</td>
    </tr>
    <tr>
        <td>Raspberry Pi 3 Model B</td>
        <td>CPU: Quad‑core Cortex‑A53 Memory: 1 GB Wi‑Fi: 802.11n Bluetooth: 4.1/BLE</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-3-model-b/">Link</a></td>
        <td>-</td>
    </tr>
    <tr>
        <td>Raspberry Pi 3 Model B+</td>
        <td>CPU: Quad‑core Cortex‑A53 @ 1.4 GHz Memory: 1 GB Wi‑Fi: 802.11ac Bluetooth: 4.2/BLE</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/">Link</a></td>
        <td>-</td>
    </tr>
    <tr>
        <td>Raspberry Pi 4 Model B</td>
        <td>CPU: Quad‑core Cortex‑A72 Memory: 1/2/4/8 GB Wi‑Fi: 802.11ac Bluetooth: 5/BLE</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-4-model-b/">Link</a></td>
        <td>Tested</td>
    </tr>
    <tr>
        <td>Raspberry Pi 5</td>
        <td>CPU: Quad‑core Cortex‑A76 Memory: 1/2/4/8/16 GB Wi‑Fi: 802.11ac Bluetooth: 5/BLE</td>
        <td><a href="https://www.raspberrypi.com/products/raspberry-pi-5/">Link</a></td>
        <td>Tested</td>
    </tr>
    </tbody>
</table>

## Audio Boards

Below are the list of DACs that have been tested and are confirmed to work out of the box. More will be added as testing progresses. If you have a DAC you’d like to see supported, or are able to provide a board for testing, we’d be happy to include it on the platform—your contributions are always welcome!

<table>
    <thead>
        <tr>
        <th width="30%">Board Name</th>
        <th width="20%">Chip</th>
        <th width="10%">Volume</th>
        <th width="10%">Sample Rate</th>
        <th width="5%">Link</th>
        <th width="5%">Status</th>
        </tr>
    </thead>
    <tbody>
     <tr>
        <td>Built-in Pi 3.5mm output</td>
        <td>Pi 3B, 3B+, 4B</td>
        <td>Software</td>
        <td>48kHz</td>
        <td><a href="https://www.raspberrypi.com/products/dac-plus/">Link</a></td>
        <td>Tested</td>
    </tr>
    <tr>
        <td>Rpi DAC+</td>
        <td>DAC: PCM5122</td>
        <td>Hardware</td>
        <td>384kHz</td>
        <td><a href="https://www.raspberrypi.com/products/dac-plus/">Link</a></td>
        <td>Tested</td>
    </tr>
     <tr>
        <td>PCM Audio Board (A)</td>
        <td>DAC: PCM5122</td>
        <td>Hardware</td>
        <td>384kHz</td>
        <td><a href="https://www.waveshare.com/pcm5122-audio-board-a.htm">Link</a></td>
        <td>Tested</td>
    </tr>
     <tr>
        <td>reSpeaker 2-Mics HAT v2</td>
        <td>DAC: WM8960, ADC: WM8960</td>
        <td>Hardware</td>
        <td>48kHz</td>
        <td><a href="https://www.seeedstudio.com/ReSpeaker-2-Mics-Pi-HAT.html">Link</a></td>
        <td>Tested</td>
    </tr>
      <tr>
        <td>Hifiberry DAC+ADC</td>
        <td>DAC: PCM5122, ADC: PCM1861</td>
        <td>Hardware</td>
        <td>384kHz</td>
        <td><a href="https://www.hifiberry.com/shop/boards/dacplus-adc/">Link</a></td>
        <td>Tested</td>
    </tr>
    </tbody>
</table>

## Displays

Below are the list of Displays that have been tested and are confirmed to work out of the box. More will be added as testing progresses. If you have a Display you’d like to see supported, or are able to provide a board for testing, we’d be happy to include it on the platform—your contributions are always welcome!

<table>
    <thead>
        <tr>
        <th width="30%">Display Name</th>
        <th width="20%">Resolution</th>
        <th width="10%">Type</th>
        <th width="10%">Protocol</th>
        <th width="10%">Setup</th>
        <th width="5%">Link</th>
        <th width="5%">Status</th>
        </tr>
    </thead>
    <tbody>
     <tr>
        <td>SSD1322</td>
        <td>256x64</td>
        <td>OLED</td>
        <td>SPI</td>
        <td><a href="https://docs.berryaudio.org/display/ssd1322-oled.html">Setup</a></td>
        <td><a href="https://www.amazon.de/Gvvsjgdbis-Display-SSD1322-Parallel-Lötstift/dp/B0DSZCTGF9/">Link</a></td>
        <td>Tested</td>
    </tr>
    <tr>
        <td>SSD1306</td>
        <td>128x64</td>
        <td>OLED</td>
        <td>I2C</td>
        <td><a href="https://docs.berryaudio.org/display/ssd1306-oled.html">Setup</a></td>
        <td><a href="https://www.amazon.de/-/en/AZDelivery-OLED-Parent-Pixel-Inches/dp/B01L9GC470/">Link</a></td>
        <td>Tested</td>
    </tr>
    <tr>
        <td>Waveshare 2.8" DSI LCD</td>
        <td>640x480</td>
        <td>LCD</td>
        <td>DSI</td>
        <td><a href="https://docs.berryaudio.org/display/waveshare-28-dsi-lcd.html">Setup</a></td>
        <td><a href="https://www.waveshare.com/2.8inch-dsi-lcd.htm">Link</a></td>
        <td>Tested</td>
    </tr>
    </tbody>
</table>


## License

Berry Audio is released under the MIT License.  
Fork it, modify it, and build your perfect listening setup.

## Contributing

We welcome your contributions! Based on functionality and code quality, contributions may be integrated directly into the core system or offered as user-contributed modules that can be installed separately.



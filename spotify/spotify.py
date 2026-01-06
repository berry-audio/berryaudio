import logging
import subprocess
import threading
import asyncio
import socket
import os

from pathlib import Path
from core.actor import Actor
from core.models import Album, Artist, Track, Image, TlTrack, Source
from core.types import PlaybackState, PlaybackControls

logger = logging.getLogger(__name__)

librespot_path = "/usr/local/bin/librespot"
on_event_path = Path(__file__).parent / "events.py"

class SpotifyExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db
        self._config = config
        self._proc = None
        self._tl_track = None
        self._timer = None
        self._timer_running = True
        self._timer_paused = False
        self._elapsed_timer_count = 0
        self._bitrate = "320"
        self._sample_rate = 44100
        self._initial_volume = "95"
        self._bit_depth = "S16"
        self._audio_codec = "Ogg"
        self._name = self._config['system']['hostname']
        self._backend = "alsa"
        self._device = self._config['playback']['output_device']
        self._source = Source(type='spotify', controls=[], state={'connected': False}) 
        self._source_active = False

    async def on_start(self):
        if not os.path.exists(librespot_path):
            logger.error("Librespot service missing")
            return
        
        logger.info("Started")
        

    async def on_event(self, message):
        pass


    async def on_stop(self):
        await self.on_stop_service()
        logger.info("Stopped")


    async def on_stop_service(self):
        await self._core.request("playback.clear")
        self._source_active = False
        await self._stop_timer()

        if self._proc is not None:
            self._proc.terminate()
            self._proc.kill()
        logger.debug('Stopped service')    
        return True


    async def on_start_service(self):
        self._source_active = True
        if os.path.exists(librespot_path):
            threading.Thread(target=self._librespot_init, daemon=True).start()
            await self._meta_init()
            logger.info(f"Started Spotify Connect with name {self._name} on {self._device}")
        else:
            logger.error(f"Librespot service missing")      
        return True


    async def _meta_init(self):
        """Reset metadata handling"""
        self._tl_track = TlTrack(0, track=Track())
        await self._core.request("playback.set_metadata", tl_track=self._tl_track)


    async def on_message(self, event):
        """Handle incoming events from librespot"""
        logger.debug(event)
        
        if 'PLAYER_EVENT' in event and self._source_active:
            if event["PLAYER_EVENT"] in ('session_connected'):
                self._source.state.user_name = event["USER_NAME"]
                self._source.state.connection_id = event["CONNECTION_ID"]
                self._source.state.connected = True
                logger.info(f"Connected to Spotify account: {self._source.state.user_name}")

            if event["PLAYER_EVENT"] in ('session_disconnected'):
                if "connection_id" in self._source.state:
                    if event["CONNECTION_ID"] == self._source.state.connection_id:
                         self._source.state.connected = False
                await self._stop_timer()
                await self._meta_init()
                await self._core.request("playback.stop_playback")
                await self._core.request("source.update_source", source=self._source)
                logger.warning(f"Disconnected from Spotify account: {self._source.state.user_name}")
                
            if event["PLAYER_EVENT"] in ('session_client_changed'):
                self._source.state.name = self._source.state.user_name #event["CLIENT_NAME"] not available anymore
                await self._stop_timer()
                await self._meta_init()
                await self._core.request("playback.set_state", state=PlaybackState.STOPPED)
                await self._core.request("playback.set_time_position", position_ms=0)
                await self._core.request("source.update_source", source=self._source)

            if event["PLAYER_EVENT"] in ('seeked', 'position_correction'):
                await self._core.request("playback.set_time_position", position_ms=int(event["POSITION_MS"]))
                self._elapsed_timer_count = int(event["POSITION_MS"]) / 1000 #milliseconds to seconds  

            if event["PLAYER_EVENT"] in ('seeked', 'position_correction'):
                await self._core.request("playback.set_time_position", position_ms=int(event["POSITION_MS"]))    
                self._core.send(event="track_position_updated", time_position=int(event["POSITION_MS"]))

            if event["PLAYER_EVENT"] in ('playing'):
                await self._resume_timer()
                await self._core.request("playback.set_state", state=PlaybackState.PLAYING)
                self._core.send(event="track_playback_resumed", tl_track=self._tl_track, time_position=int(event["POSITION_MS"]))

            if event["PLAYER_EVENT"] in ('paused'):
                await self._pause_timer()
                await self._core.request("playback.set_state", state=PlaybackState.PAUSED)
                await self._core.request("playback.set_time_position", position_ms=int(event["POSITION_MS"]))
                self._core.send(event="track_playback_paused", tl_track=self._tl_track, time_position=int(event["POSITION_MS"]))                    

            if event["PLAYER_EVENT"] in ('end_of_track', 'unavailable', 'preload_next', 'preloading', 'loading', 'stopped'):
                pass # TODO

            if event["PLAYER_EVENT"] in ('volume_changed'):    
                pass # TODO

            if event["PLAYER_EVENT"] in ('track_changed'):
                covers = event["COVERS"]
                image = covers.split('\n')[0] if covers else "/images/no_cover.jpg"

                if self._tl_track is not None:
                    await self._stop_timer()
                    await self._core.request("playback.stop_playback")

                track = Track(
                        uri = event["URI"] or "",
                        name = event["NAME"] or "Unknown",
                        artists = frozenset([Artist(name=event["ARTISTS"] or "")]),
                        albums = frozenset([Album(name = event["ALBUM"] or "")]),
                        composers=frozenset(),
                        performers=frozenset(),
                        track_no = int(event["NUMBER"]) or 0,
                        disc_no = int(event["DISC_NUMBER"]) or 0,
                        length = int(event["DURATION_MS"]) or 0,  
                        bitrate= int(self._bitrate) * 1000,
                        sample_rate = self._sample_rate,
                        bit_depth = self._bit_depth,
                        channels = 2,
                        audio_codec = self._audio_codec,
                        images= [Image(uri=image)] or [],
                    )
                self._tl_track = TlTrack(0, track=track)
                await self._start_timer()
                await self._core.request("playback.set_metadata", tl_track=self._tl_track)
                self._core.send(event="track_playback_started", tl_track=self._tl_track)

            
    def _librespot_init(self):
        cmd = [
                librespot_path,
                "--bitrate", self._bitrate,
                "--format", self._bit_depth,
                "--name", self._name,
                "--cache", "/tmp/spotify_cache",
                "--disable-audio-cache",
                "--backend", self._backend,
                "--onevent", on_event_path,
                "--initial-volume", self._initial_volume,
                "--enable-volume-normalisation",
                "--device-type", "avr",
                "--device", self._device,
            ]
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1 
        )

        def log(stream, label):
            for line in iter(stream.readline, ''):
                logger.debug(line.strip())
            stream.close()    

        threading.Thread(target=log, args=(self._proc.stdout, "STDOUT"), daemon=True).start()
        threading.Thread(target=log, args=(self._proc.stderr, "STDERR"), daemon=True).start()


    async def _pause_timer(self):
        """Pause track elapsed timer"""
        self._timer_paused = True


    async def _resume_timer(self):
        """Resume track elapsed timer"""
        self._timer_paused = False


    async def _stop_timer(self):
        """Stop track elapsed timer"""
        self._timer_running = False
        self._timer_paused = False
        self._elapsed_timer_count = 0
        if self._timer:
            self._timer.cancel()
            self._timer = None


    async def _start_timer(self):
        """Start track elapsed timer"""
        self._timer_running = True
        self._timer_paused = False
        self._elapsed_timer_count = 0
        self._timer = asyncio.create_task(self._elapsed_timer())


    async def _elapsed_timer(self):
        """Set track position every second"""
        try:
            while self._timer_running:
                if not self._timer_paused:
                    self._elapsed_timer_count += 1
                    await self._core.request("playback.set_time_position", position_ms=int(self._elapsed_timer_count * 1000))
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

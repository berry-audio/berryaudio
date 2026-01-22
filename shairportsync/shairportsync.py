import logging
import threading
import subprocess
import asyncio
import socket
import os
import time

from pathlib import Path
from core.actor import Actor
from core.models import Album, Artist, Track, Image, TlTrack, Source
from core.types import PlaybackState

logger = logging.getLogger(__name__)

shairport_path = "/usr/local/bin/shairport-sync"
shairport_render_path = "/usr/local/bin/shairport-sync-metadata-reader"
shairport_config_path = Path(__file__).parent / "shairport-sync.conf"
shairport_render_tmp = "/tmp/shairport-sync-metadata"

class ShairportsyncExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db
        self._config = config
        self._proc = None
        self._proc_meta = None
        self._source = Source(type='shairportsync', controls=[], state={'connected': False}) 
        self._tl_track = TlTrack(0, track=Track())
        self._timer = None
        self._timer_running = True
        self._timer_paused = False
        self._elapsed_timer_count = 0
        self._pend = False
        self._name = self._config['system']['hostname']
        self._device = self._config['mixer']['output_audio']
        self._source_active = False


    async def on_start(self):
        if not os.path.exists(shairport_path):
            logger.error("Shairport service missing")
            return

        if not os.path.exists(shairport_render_path):
            logger.error("Shairport meta service missing")
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
        self._stop_timer()
        
        if self._proc is not None:
            self._proc.terminate()
            self._proc.kill()

        if self._proc_meta is not None:    
            self._proc_meta.terminate()
            self._proc_meta.kill()

        logger.debug('Stopped service')          
        return True


    async def on_start_service(self):
        self._source_active = True
        if os.path.exists(shairport_path) and os.path.exists(shairport_render_path):
            threading.Thread(target=self._shairportsync_init, daemon=True).start()
            threading.Thread(target=self._shairportsync_meta_init, daemon=True).start()
            self._clean_images_dir()
            self._reset_meta()
            logger.info(f"Started Shairport Sync with name {self._name} on {self._device}")
        else:
            logger.error(f"Shairport servics missing")          
        return True 
    

    def _clean_images_dir(self):
        image_path = Path(__file__).parent.parent / "web" / "www" / "images" / "shairportsync"
        if image_path.exists() and image_path.is_dir():
            for item in image_path.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                except Exception as e:
                    print(f"Failed to delete {item}: {e}")
        else:
            print(f"Directory does not exist: {image_path}")
           


    def _reset_meta(self):
        """Reset metadata handling"""
        self._tl_track = TlTrack(0, track=Track())
        if self._source_active:
            self._core._request("playback.set_metadata", tl_track=self._tl_track)
    

    def _shairportsync_init(self):
        """Starting shairportsync service"""
        cmd = [
                shairport_path,
                "--name",self._name,
                "-c", shairport_config_path,
                "--timeout", "120",
                "--", "-d", self._device,
                "--metadata-enable",
                "-v"
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
                if 'warning' in line:
                    logger.warning(line.strip())
                else:    
                    logger.debug(line.strip())
            stream.close()    

        threading.Thread(target=log, args=(self._proc.stdout, "STDOUT"), daemon=True).start()
        threading.Thread(target=log, args=(self._proc.stderr, "STDERR"), daemon=True).start()


    def _shairportsync_meta_init(self):
        if not os.path.exists(shairport_render_tmp):
            os.mkfifo(shairport_render_tmp)
            logger.debug(f"Created FIFO: {shairport_render_tmp}")

        self._proc_meta = subprocess.Popen(
            [
                shairport_render_path, 
                '--raw',
            ],
            stdin=open(shairport_render_tmp, "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        def _update_picture():
            image_path = Path(__file__).parent.parent / "web" / "www" / "images" / "shairportsync"

            if not image_path.exists():
                image_path.mkdir(parents=True, exist_ok=True)

            files = [
                f for f in list(image_path.glob("cover*.jpg")) + list(image_path.glob("cover*.png"))
                if f.exists()
            ]

            if files:
                picture_file = files[0]
                picture_uri = (Image(uri=f"/images/shairportsync/{picture_file.name}"),) 
            else:
                picture_uri = () 

            _tl_track = self._tl_track.track.copy(update={"images": picture_uri})
            self._tl_track = TlTrack(tlid=0, track=_tl_track)
            if self._source_active:
                self._core._request("playback.set_metadata", tl_track=self._tl_track)


        def _parse_metadata_line(line: str):
            line = line.strip()
            if not line:
                return None

            parts = line.split(":", 1)
            head = parts[0].strip()

            try:
                meta_type, meta_code = head.split()[:2]
                meta_type = meta_type.strip('"')
                meta_code = meta_code.strip('"')
            except ValueError:
                return None  # malformed line

            val = None
            if len(parts) > 1:
                hex_val = parts[1].strip()
                if hex_val.startswith("0x"):
                    try:
                        val = bytes.fromhex(hex_val[2:]).decode("utf-8", errors="ignore")
                    except ValueError:
                        val = hex_val  # not valid hex
                else:
                    val = hex_val
            return meta_type, meta_code, val    

        # Start processing raw data here
        for line in self._proc_meta.stdout:
            
            try:
                meta_type, meta_code, val = _parse_metadata_line(line)
                logger.debug(f"{meta_type}, {meta_code}, {val}") 

                if(meta_code == 'conn'): #connected
                    self._source.state.connection_id = val

                if(meta_code == 'disc'): #disconnected
                    self._source.state.connection_id = val
                    self._source.state.connected = False

                    if self._source_active:
                        self._core._request("playback.set_state", state=PlaybackState.STOPPED)
                        self._core._request("playback.set_time_position", position_ms=0)
                        self._core._request("source.update_source", source=self._source)
                    self._stop_timer()
                    self._reset_meta()

                if(meta_code == 'ofps'): #sample rate
                    _tl_track = self._tl_track.track.copy(update={"sample_rate": int(val), "audio_codec": "PCM"})
                    self._tl_track = TlTrack(tlid=0, track=_tl_track)
                
                if(meta_code == 'ofmt'): #bit dept
                    _tl_track = self._tl_track.track.copy(update={"bit_depth": val})
                    self._tl_track = TlTrack(tlid=0, track=_tl_track)

                if(meta_code == 'snam'): #connecting device name
                    self._source.state.connected = True
                    self._source.state.name = val
                    self._start_timer()
                    self._pause_timer()

                    if self._source_active:
                        self._core._request("playback.set_state", state=PlaybackState.STOPPED)
                        self._core._request("playback.set_time_position", position_ms=0)
                        self._core._request("source.update_source", source=self._source)

                if(meta_code == 'cmac'):  #connecting device mac
                    self._source.state.address = val

                if(meta_code == 'mdst'): #sequence of metadata is about to start
                    pass # TODO
                    
                if(meta_code == 'asal'):
                    _tl_track = self._tl_track.track.copy(update={"album": Album(name = val)})
                    self._tl_track = TlTrack(tlid=0, track=_tl_track)

                if(meta_code == 'asar'):
                    _tl_track = self._tl_track.track.copy(update={"artists": frozenset([Artist(name=val)])})
                    self._tl_track = TlTrack(tlid=0, track=_tl_track)

                if(meta_code == 'minm'):
                    _tl_track = self._tl_track.track.copy(update={"name": val})
                    self._tl_track = TlTrack(tlid=0, track=_tl_track)

                if(meta_code == 'mden'): #sequence of metadata has ended
                    # self._clean_images_dir()
                    if self._source_active:
                        self._core._request("playback.set_metadata", tl_track=self._tl_track)

                if(meta_code == 'prsm'): #play stream resume
                    self._resume_timer()
                    if self._source_active:
                        self._core._request("playback.set_state", state=PlaybackState.PLAYING)

                if(meta_code == 'pbeg'): #play stream begin
                    pass # TODO
                
                if(meta_code == 'pend'): #play stream end
                    self._pause_timer()
                    if self._source_active:
                        self._core._request("playback.set_state", state=PlaybackState.PAUSED)
                
                if(meta_code == 'aend'): #play stream end
                    pass # TODO

                if(meta_code == 'pfls'): #play stream flush
                    pass # TODO
                
                if(meta_code == 'pcst'): #picture has been sent
                    pass # TODO

                if(meta_code == 'PICT'):
                    if val == None:
                         pass # TODO

                if(meta_code == 'pcen'): #picture has been sent
                    _update_picture()

                    
                if(meta_code == 'prgr'): #play sequence, the current play point and the end of the play sequence
                    position_values = val.split("/")
                    if len(position_values) == 3:
                        start, current, end = map(int, position_values)
                        
                        position_ms = int(((current - start) / 44100) * 1000)
                        track_length_ms = int(((end - start) / 44100) * 1000)

                        _tl_track = self._tl_track.track.copy(update={"length": track_length_ms})
                        self._tl_track = TlTrack(tlid=0, track=_tl_track)
                        self._elapsed_timer_count = int(position_ms / 1000)

                        if self._source_active:
                            self._core.send(target="web", event="track_position_updated", time_position=position_ms)
                            self._core._request("playback.set_time_position", position_ms=position_ms)
                            self._core._request("playback.set_metadata", tl_track=self._tl_track)
                        

            except Exception:
                raise RuntimeError(f"Error init meta info")     
               
                    
    def _pause_timer(self):
        """Pause track elpased timer"""
        self._timer_paused = True


    def _resume_timer(self):
        """Resume track elpased timer"""
        self._timer_paused = False


    def _stop_timer(self):
        """Stop track elpased timer"""
        self._timer_running = False
        self._timer_paused = False
        self._elapsed_timer_count = 0
        if self._timer and self._timer.is_alive():
            self._timer.join()
        self._timer = None


    def _start_timer(self):
        """Start track elpased timer"""
        self._timer_running = True
        self._timer_paused = False
        self._timer = threading.Thread(target=self._elapsed_timer, daemon=True)
        self._timer.start()


    def _elapsed_timer(self):
        """Set track position every second """
        while self._timer_running:
            if not self._timer_paused:
                self._elapsed_timer_count += 1
                if self._source_active:
                    self._core._request("playback.set_time_position", position_ms=int(self._elapsed_timer_count * 1000))
                time.sleep(1) 
            else:
                time.sleep(0.1)       
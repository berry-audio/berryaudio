import logging
from pathlib import Path

from gi.repository import GLib, Gst
from core.actor import Actor
from core.models import Image, Album, Artist, Track, TlTrack
from core.types import PlaybackState

logger = logging.getLogger(__name__)

class PlaybackExtension(Actor):
    def __init__(self, core, db, config):
        super().__init__()
        self._core = core
        self._db = db
        self._config = config
        self._state = PlaybackState.STOPPED
        self._playing = False
        self._buffering = False
        self._pipeline: None
        self._sink: None
        self._source: None
        self._convert: None
        self._resample: None
        self._setup_resample = False
        self._duration = 0
        self._elapsed = 0 
        self._time_source_id = None
        self._playback_uri = None
        self._track = TlTrack(tlid=0, track=Track())


    def _setup_playbin(self):
        self._pipeline = Gst.Pipeline.new("audio-player")
        self._source = Gst.ElementFactory.make("uridecodebin", "source")
        self._convert = Gst.ElementFactory.make("audioconvert", "convert")
        self._resample = Gst.ElementFactory.make("audioresample", "resample")
        self._sink = Gst.ElementFactory.make("alsasink", "sink")
        self._sink.set_property("device", self._config['playback']['output_device'])

        self._pipeline.add(self._source)
        self._pipeline.add(self._sink)
            
        if self._setup_resample:
            logger.info('Resample On')
            self._pipeline.add(self._convert)
            self._pipeline.add(self._resample)
            self._convert.link(self._resample)
            self._resample.link(self._sink)

        else:
            logger.info('Resample Off')
            self._source.link(self._sink)

        self._source.connect("pad-added", self._on_pad_added)

        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

                    
    def _on_pad_added(self, decodebin, pad):
        caps = pad.query_caps(None)
        name = caps.get_structure(0).get_name()

        if name.startswith("audio/"):
            if self._setup_resample:
                sink_pad = self._convert.get_static_pad("sink")
            else:
                sink_pad = self._sink.get_static_pad("sink")    
            if pad.is_linked():
                return
            pad.link(sink_pad)

            def probe(pad, info):
                caps = pad.get_current_caps()
                if not caps:
                    return Gst.PadProbeReturn.OK
                structure = caps.get_structure(0)
                if structure.has_name("audio/x-raw"):
                    rate = structure.get_int("rate")[1] if structure.has_field("rate") else None
                    channels = structure.get_int("channels")[1] if structure.has_field("channels") else None
                    
                    bit_depth = None
                    if structure.has_field("width"):
                        bit_depth = structure.get_int("width")[1]
                    elif structure.has_field("depth"):
                        bit_depth = structure.get_int("depth")[1]
                    elif structure.has_field("format"):
                        bit_depth = structure.get_string("format")
                            
                    _track =  self._track.track.copy(update={
                            "sample_rate": rate,
                            "channels":channels,
                            "bit_depth": bit_depth,
                            "resample": self._setup_resample,
                        })       
                    self._track = TlTrack(tlid=self._track.tlid, track=_track)
                    self._core.send(event='track_meta_updated',  tl_track=self._track)
                return Gst.PadProbeReturn.REMOVE

            pad.add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, probe)


    def _on_message(self, bus, message):
        t = message.type

        if t == Gst.MessageType.TAG:
            tags = message.parse_tag()
            updates = {}

            for i in range(tags.n_tags()):
                tag_name = tags.nth_tag_name(i)
                for j in range(tags.get_tag_size(tag_name)):
                    value = tags.get_value_index(tag_name, j)

                    if isinstance(value, Gst.Sample):
                        buf = value.get_buffer()
                        result, mapinfo = buf.map(Gst.MapFlags.READ)
                        if result:
                            BASE_DIR = Path(__file__).resolve().parent.parent  
                            cover_path = BASE_DIR / "web" / "www" / "images" / "nowplaying" / "cover.jpg"
                            with open(cover_path, "wb") as f:
                                f.write(mapinfo.data)
                            buf.unmap(mapinfo)
                            # print("Cover art saved as cover.jpg")
                        continue
                    if tag_name == "audio-codec":
                        updates["audio_codec"] = value
                    elif tag_name == "nominal-bitrate":
                        updates["bitrate"] = value
                    elif tag_name == "bitrate" and not getattr(self._track, "bitrate", None):
                        updates["bitrate"] = round(value / 1000) * 1000
                    elif tag_name == "title":
                        updates["name"] = value
                    elif tag_name == "album":
                        updates["albums"] = frozenset([Album(name=value)])
                    elif tag_name == "artist":
                        updates["artists"] = frozenset([Artist(name=value)])
                    elif tag_name == "genre":
                        updates["genre"] = value
                    self._buffering = False
                     
            if updates:
                updated_track = self._track.track.copy(update=updates)
                _track = TlTrack(tlid=self._track.tlid, track=updated_track)

                def _has_changes(old: TlTrack, new: TlTrack) -> bool:
                        return old.model_dump_json() != new.model_dump_json()  
                
                if _has_changes(self._track, _track):
                    self._track = _track  
                    self._core.send(event='track_meta_updated',  tl_track=self._track)

        if t == Gst.MessageType.DURATION_CHANGED:
            self._get_duration()

        elif t == Gst.MessageType.BUFFERING:
            if not self._buffering:
                self._buffering = True
                self._core.send(event='track_playback_buffering')

        elif t == Gst.MessageType.EOS:
            self._stop()
            self._core.send(event='track_playback_ended', tl_track=self._track)
            
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.warning(f"Debug: {debug}")
            
            if "-1" in debug or "-4" in debug:
                self._setup_resample = True
                self._pipeline.set_state(Gst.State.NULL)
                self._setup_playbin()
                self._play()
            else:                
                _track = self._track.track.copy(update={"artists": frozenset([Artist(name="Playback Error")])})
                self._track = TlTrack(tlid=self._track.tlid, track=_track)
                self._stop()
                self._core.send(event='track_meta_updated',  tl_track=self._track)
                self._core.send(event='track_playback_error', tl_track=self._track)
                self._core.send(event='track_playback_ended', tl_track=self._track)
                logger.warning(f"Unavailable {self._track}")

        elif t == Gst.MessageType.STREAM_START:
            pass
    

    def _get_duration(self):
        success, duration = self._pipeline.query_duration(Gst.Format.TIME)
        if success and duration > 0:
            self._duration = int(duration / Gst.SECOND)  * 1000
            _track = self._track.track.copy(update={"length": self._duration})
            self._track = TlTrack(tlid=self._track.tlid, track=_track)
            self._core.send(event='track_meta_updated',  tl_track=self._track) 


    def _start_time_tracking(self):
        if self._time_source_id:
            GLib.source_remove(self._time_source_id)
        def update_elapsed():
            if self._pipeline:
                success, position = self._pipeline.query_position(Gst.Format.TIME)
                if success:
                    self._elapsed = int(( position / Gst.SECOND ) * 1000)
                    duration_sec = ( self._duration / Gst.SECOND ) * 1000
            return True
        
        self._time_source_id = GLib.timeout_add(500, update_elapsed) 


    async def _load_uri(self, uri: str, tlid: int) -> None:
        try:
            _uri = uri.split(":")
            if len(_uri) != 2:
                logger.error(f"Invalid URI format: {uri}")
                return

            ext, track_id = _uri
            await self._core.request("source.set", type=ext)

            get_track = await self._core.request(f"{ext}.lookup_track", id=track_id)
            playback_uri = await self._core.request(f"{ext}.playback_uri", id=track_id)

            if not get_track:
                logger.error(f"Track not found for {uri}")
                return

            if not playback_uri:
                logger.error(f"Playback URI not found for {uri}")
                return

            self._playback_uri = playback_uri
            self._track = TlTrack(tlid=tlid, track=get_track)
            self._core.send(event="track_meta_updated", tl_track=self._track)

        except Exception as e:
            logger.exception(f"Error starting playback for {uri}: {e}")



    async def on_start(self):
        try:
            self._setup_playbin()
        except GLib.Error:
            logger.exception("Unknown GLib error on audio startup.")
        logger.info("Started")
       

    async def on_stop(self):
        return self._stop()


    async def on_clear(self):
        self._stop()
        self._playback_uri = None
        self.on_set_metadata(None)


    def on_stop_playback(self):
        return self._stop()


    async def on_event(self, message):
        if message['event'] == "tracklist_changed":
            if not message['tl_tracks']: #checks if tracklist is clear
                #assign tlid = 0 if track was started playing from playlist and then the playlist was cleared
                self._track = TlTrack(tlid=0, track=self._track.track.copy())


    async def on_play(self, uri: str | None = None, tlid : int | None = 0) -> bool:
        if uri:
            self._setup_resample = False
            self._pipeline.set_state(Gst.State.NULL)
            self._setup_playbin()
            await self._load_uri(uri, tlid)
            if self._stop():
                return self._play()
        else:
            if self._state in (PlaybackState.PAUSED, PlaybackState.STOPPED):
                return self._play()
        

    def on_seek(self, time_position: int):
        if time_position < 1:
            time_position = 1 
        if time_position:
            ms = time_position / 1000
            success = self._pipeline.seek(
                1.0,                    
                Gst.Format.TIME,         
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,  
                Gst.SeekType.SET, ms * Gst.SECOND,    
                Gst.SeekType.NONE, -1  
            )
            self._elapsed = time_position
            self._core.send(event='track_position_updated',  time_position=time_position) 
            if success:
                return True
            else:
                return False


    async def on_next(self, from_ui: bool = True) -> bool:
        next_track = await self._core.request("tracklist.next_track", from_ui=from_ui)        
        if next_track is not None:
            await self._load_uri(next_track.track.uri, next_track.tlid)
            self._stop()
            self._play()
        else:
            self._stop()     
        return True
    

    async def on_previous(self, from_ui: bool = True) -> bool:
        previous_track = await self._core.request("tracklist.previous_track", from_ui=from_ui)
        if previous_track is not None:
            await self._load_uri(previous_track.track.uri, previous_track.tlid)
            self._stop()
            self._play()
        else:
           self._stop()       
        return True


    async def on_get_current_tl_track(self):
        return self._track


    def on_get_state(self):
        return self._state  


    def on_set_state(self, state: PlaybackState) -> bool:
        self._state = state
        self._core.send(event='playback_state_changed',  state=self._state)
        return True


    def on_get_time_position(self) -> int:
        return self._elapsed


    def on_set_time_position(self, position_ms: int) -> bool:
        self._elapsed = position_ms
        return True


    def on_set_metadata(self, tl_track: TlTrack | None) -> bool:
        if tl_track is None:
            self._playback_uri = None
            self._track = TlTrack(tlid=0, track=Track())
        else:
            self._track = tl_track
        self._core.send(event='track_meta_updated',  tl_track=self._track) 
        return True


    def on_pause(self):
        if self._playing:
            self._pipeline.set_state(Gst.State.PAUSED)
            self._state = PlaybackState.PAUSED

            if self._time_source_id:
                GLib.source_remove(self._time_source_id)
                self._time_source_id = None

            self._core.send(
                    event='track_playback_paused', 
                    tl_track=self._track, 
                    time_position=self._elapsed, 
                )
            self._core.send(event='playback_state_changed',  state=self._state)
        return True


    def _stop(self):
        self._pipeline.set_state(Gst.State.NULL)
        self._state = PlaybackState.STOPPED
        self._playing = False

        if self._time_source_id:
            GLib.source_remove(self._time_source_id)
            self._time_source_id = None
        
        self._elapsed = 0
        self._core.send(event='playback_state_changed',  state=self._state)
        return True


    def _play(self):
        if not self._playback_uri:
            logger.warning("No track provided")
            return
        old_state = self._state
        self._source.set_property("uri", self._playback_uri)

        self._pipeline.set_state(Gst.State.PAUSED)
        self._pipeline.get_state(Gst.CLOCK_TIME_NONE)
        self._get_duration()

        self._pipeline.set_state(Gst.State.PLAYING)
        self._state = PlaybackState.PLAYING
        self._playing = True

        self._start_time_tracking()

        if old_state == PlaybackState.PAUSED:
            self._core.send(
                event='track_playback_resumed',  
                tl_track=self._track,
                time_position=self._elapsed
            )
        else:
             self._elapsed = 0
             self._core.send(
                event='track_playback_started',  
                tl_track=self._track,
                time_position=self._elapsed
            )

        self._core.send(event='playback_state_changed',  state=self._state)
        return True
   


    
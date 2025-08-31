
import logging
import uuid
import base64
import os

from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from mutagen import File
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from mutagen.mp3 import MP3, HeaderNotFoundError
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis

try:
    from mutagen.oggopus import OggOpus  # optional, not always installed
except Exception:
    OggOpus = None
try:
    from mutagen.asf import ASF  # WMA
except Exception:
    ASF = None

logger = logging.getLogger(__name__)

class Metadata:
    def __init__(self, cover_dir: str):
        if not cover_dir: 
            #must be a folder in web/www/images/<folder>
            raise ValueError("cover_dir must be provided and cannot be empty.")
        self.cover_dir = cover_dir
        self.cover_dir_path = Path(__file__).resolve().parent.parent.parent / 'web' / 'www' / 'images' / cover_dir
        

    def _save_cover_bytes(self, data: bytes, mime: Optional[str]) -> Optional[str]:
            if not data:
                return None
            ext = ".jpg"
            if mime:
                m = mime.lower()
                if "png" in m:
                    ext = ".png"
                elif "jpeg" in m or "jpg" in m:
                    ext = ".jpg"
                elif "webp" in m:
                    ext = ".webp"
                elif "bmp" in m:
                    ext = ".bmp"
                # fall through keeps .jpg if unknown
            os.makedirs(self.cover_dir_path, exist_ok=True)
            uid = uuid.uuid4().hex  # long unique id
            fname = uid + ext
            out_path = os.path.join(self.cover_dir_path, fname)
            with open(out_path, "wb") as f:
                f.write(data)
            return f"/images/{self.cover_dir}/{fname}"


    def extract_cover_and_tags(self, fullpath: str) -> Tuple[Optional[str], Dict[str, Any]]:
            """
            Returns (cover_path, tags_dict)
            tags_dict keys: name, album, artist, genre, track_number, disc_number, length, bitrate, sample_rate, year
            """
            tags: Dict[str, Any] = {
                "name": None,
                "album": None,
                "artist": None,
                "genre": None,
                "track_number": None,
                "disc_number": None,
                "length": None,
                "bitrate": None,
                "sample_rate": None,
                "year": None,
            }
            cover_path: Optional[str] = None

            try:
                audio = File(fullpath, easy=False)
            except HeaderNotFoundError:
                logger.warning(f"Skipping invalid MP3 (bad headers): {fullpath}")
                return None, tags
            except Exception as e:
                logger.error(f"Error opening {fullpath}: {e}")
                return None, tags

            if audio is None:
                logger.warning(f"Unsupported or unreadable file: {fullpath}")
                return None, tags

            try:
                tags["length"] = float(getattr(audio.info, "length", None) or 0) * 1000 or None
            except Exception:
                pass
            try:
                tags["bitrate"] = int(getattr(audio.info, "bitrate", None) or 0) or None
            except Exception:
                pass
            try:
                tags["sample_rate"] = int(getattr(audio.info, "sample_rate", None) or 0) or None
            except Exception:
                pass

            # ---- MP3 (ID3) ----
            if isinstance(audio, MP3):
                # textual tags (prefer TXXX/Easy equivalents if present)
                try:
                    id3 = audio.tags if isinstance(audio.tags, ID3) else ID3(fullpath)
                except ID3NoHeaderError:
                    id3 = None

                if id3:
                    # Title / Album / Artist / Genre / Track / Disc / Year
                    def txt(frame_id_list):
                        for fid in frame_id_list:
                            f = id3.get(fid)
                            if f:
                                try:
                                    return str(f.text[0]).strip() if hasattr(f, "text") and f.text else None
                                except Exception:
                                    pass
                        return None

                    tags["name"] = txt(["TIT2"])
                    tags["album"] = txt(["TALB"])
                    tags["artist"] = txt(["TPE1"])
                    tags["genre"] = txt(["TCON"])
                    # Track number like "3/12"
                    tn = txt(["TRCK"])
                    if tn:
                        try:
                            tags["track_number"] = int(str(tn).split("/")[0])
                        except Exception:
                            pass
                    dn = txt(["TPOS"])
                    if dn:
                        try:
                            tags["disc_number"] = int(str(dn).split("/")[0])
                        except Exception:
                            pass
                    yr = txt(["TDRC", "TDOR", "TYER"])
                    if yr:
                        # try to parse to int if possible
                        try:
                            tags["year"] = int(str(yr)[:4])
                        except Exception:
                            pass

                    # Cover
                    apics = [f for f in id3.values() if isinstance(f, APIC)]
                    if apics:
                        # prefer front cover (type=3)
                        front = next((a for a in apics if getattr(a, "type", None) == 3), apics[0])
                        cover_path = self._save_cover_bytes(front.data, getattr(front, "mime", None))

            # ---- MP4/M4A ----
            elif isinstance(audio, MP4):
                atags = audio.tags or {}
                def first_key(keys):
                    for k in keys:
                        if k in atags and atags[k]:
                            v = atags[k]
                            return v[0] if isinstance(v, list) else v
                    return None
                tags["name"] = first_key(["\xa9nam"])
                tags["album"] = first_key(["\xa9alb"])
                tags["artist"] = first_key(["\xa9ART"])
                tags["genre"] = first_key(["\xa9gen"])
                # track/disc may be tuples like (track, total)
                tr = atags.get("trkn")
                if tr and len(tr) and isinstance(tr[0], tuple) and tr[0][0]:
                    tags["track_number"] = int(tr[0][0])
                dc = atags.get("disk")
                if dc and len(dc) and isinstance(dc[0], tuple) and dc[0][0]:
                    tags["disc_number"] = int(dc[0][0])
                yr = first_key(["\xa9day"])
                if yr:
                    try:
                        tags["year"] = int(str(yr)[:4])
                    except Exception:
                        pass
                # cover(s)
                covr = atags.get("covr")
                if covr:
                    c = covr[0]
                    mime = None
                    if isinstance(c, MP4Cover):
                        if c.imageformat == MP4Cover.FORMAT_PNG:
                            mime = "image/png"
                        else:
                            mime = "image/jpeg"
                        cover_path = self._save_cover_bytes(bytes(c), mime)

            # ---- FLAC ----
            elif isinstance(audio, FLAC):
                vorb = audio
                tags["name"] = (vorb.get("title", [None]) or [None])[0]
                tags["album"] = (vorb.get("album", [None]) or [None])[0]
                tags["artist"] = (vorb.get("artist", [None]) or [None])[0]
                tags["genre"] = (vorb.get("genre", [None]) or [None])[0]
                tn = (vorb.get("tracknumber", [None]) or [None])[0]
                if tn:
                    try:
                        tags["track_number"] = int(str(tn).split("/")[0])
                    except Exception:
                        pass
                dn = (vorb.get("discnumber", [None]) or [None])[0]
                if dn:
                    try:
                        tags["disc_number"] = int(str(dn).split("/")[0])
                    except Exception:
                        pass
                yr = (vorb.get("date", [None]) or [None])[0] or (vorb.get("year", [None]) or [None])[0]
                if yr:
                    try:
                        tags["year"] = int(str(yr)[:4])
                    except Exception:
                        pass
                if vorb.pictures:
                    pic = vorb.pictures[0]
                    cover_path = self._save_cover_bytes(pic.data, pic.mime)

            # ---- OGG Vorbis / Opus ----
            elif isinstance(audio, OggVorbis) or (OggOpus and isinstance(audio, OggOpus)):
                v = audio
                def g(key):
                    val = v.tags.get(key) if v.tags else None
                    return val[0].strip() if val else None
                tags["name"] = g("title")
                tags["album"] = g("album")
                tags["artist"] = g("artist")
                tags["genre"] = g("genre")
                tn = g("tracknumber")
                if tn:
                    try:
                        tags["track_number"] = int(str(tn).split("/")[0])
                    except Exception:
                        pass
                dn = g("discnumber")
                if dn:
                    try:
                        tags["disc_number"] = int(str(dn).split("/")[0])
                    except Exception:
                        pass
                yr = g("date") or g("year")
                if yr:
                    try:
                        tags["year"] = int(str(yr)[:4])
                    except Exception:
                        pass
                # Cover art in Vorbis can be in METADATA_BLOCK_PICTURE (base64 FLAC picture)
                mbp_list = (v.tags.get("metadata_block_picture") if v.tags else None) or []
                if mbp_list:
                    try:
                        picdata = base64.b64decode(mbp_list[0])
                        pic = Picture()
                        pic.data = b""
                        pic.load(picdata)
                        cover_path = self._save_cover_bytes(pic.data, pic.mime)
                    except Exception:
                        pass

            # ---- WMA/ASF ----
            elif ASF and isinstance(audio, ASF):
                # Simple extraction; ASF tagging is a bit different
                def asf_get(tagkey):
                    vals = audio.tags.get(tagkey, [])
                    if vals:
                        return str(vals[0])
                    return None
                tags["name"] = asf_get("Title")
                tags["album"] = asf_get("WM/AlbumTitle")
                tags["artist"] = asf_get("Author") or asf_get("WM/AlbumArtist")
                tags["genre"] = asf_get("WM/Genre")
                yr = asf_get("WM/Year")
                if yr:
                    try:
                        tags["year"] = int(str(yr)[:4])
                    except Exception:
                        pass
                # cover
                pics = audio.tags.get("WM/Picture", [])
                if pics:
                    try:
                        blob = pics[0].value  # contains a byte array with header; mutagen decodes mime separately in newer versions
                        # Mutagen may provide .mime on picture in some versions; fallback unknown
                        cover_path = self._save_cover_bytes(blob, None)
                    except Exception:
                        pass

            # As a final fallback for missing textual tags, try "easy" interface
            if not any([tags["name"], tags["album"], tags["artist"], tags["genre"]]):
                easy = File(fullpath, easy=True)
                if easy and easy.tags:
                    def ez(k):
                        v = easy.tags.get(k)
                        return v[0].strip() if v else None
                    tags["name"] = tags["name"] or ez("title")
                    tags["album"] = tags["album"] or ez("album")
                    tags["artist"] = tags["artist"] or ez("artist")
                    tags["genre"] = tags["genre"] or ez("genre")
                    tn = ez("tracknumber")
                    if tn and not tags["track_number"]:
                        try: tags["track_number"] = int(str(tn).split("/")[0])
                        except Exception: pass
                    dn = ez("discnumber")
                    if dn and not tags["disc_number"]:
                        try: tags["disc_number"] = int(str(dn).split("/")[0])
                        except Exception: pass
                    yr = ez("date") or ez("year")
                    if yr and not tags["year"]:
                        try: tags["year"] = int(str(yr)[:4])
                        except Exception: pass

            if not tags["name"]:
                tags["name"] = Path(fullpath).stem

            return (cover_path, tags)
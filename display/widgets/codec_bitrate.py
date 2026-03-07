from PIL import ImageFont


class WidgetCodecBitrate:
    def __init__(self, font_path=None):
        self._font_path = font_path

    def draw(
        self,
        draw,
        x,
        y,
        bitrate=320000,
        audio_codec="PCM",
        codec_font_size=5,
        bitrate_font_size=5,
    ):
        box_width = 21
        box_height = 20
        highlight_y = y + box_height // 2

        font_label = ImageFont.truetype(self._font_path, codec_font_size)
        font_bitrate = ImageFont.truetype(self._font_path, bitrate_font_size)
        if bitrate:
            bitrate_display = str(bitrate // 1000)
        else:
            bitrate_display = "---"

        draw.rectangle(
            [(x, y), (x + box_width - 1, y + box_height - 1)],
            outline="white",
            fill="black",
        )
        draw.rectangle(
            [(x, highlight_y), (x + box_width - 1, y + box_height - 1)], fill="white"
        )

        bitrate_width = draw.textbbox((0, 0), bitrate_display, font=font_bitrate)[2]
        draw.text(
            (x + (box_width - bitrate_width) // 2 + 1, y + 3),
            bitrate_display,
            fill="white",
            font=font_bitrate,
            anchor="lt",
        )

        label_width = draw.textbbox(
            (0, 0), self.get_codec_name(audio_codec), font=font_label
        )[2]
        draw.text(
            (x + (box_width - label_width) // 2 + 1, highlight_y + 2),
            self.get_codec_name(audio_codec),
            fill="black",
            font=font_label,
            anchor="lt",
        )

    def get_codec_name(self, format_str):
        if not format_str:
            return ""

        mapping = {
            "DSD (Direct Stream Digital), least significant bit first, planar": "DSD",
            "Uncompressed 24-bit PCM audio": "PCM",
            "Uncompressed 16-bit PCM audio": "PCM",
            "MPEG-1 Layer 3 (MP3)": "MP3",
            "MPEG-1 Layer 2 (MP2)": "MP2",
            "MPEG-4 AAC": "AAC",
            "MPEG-2 AAC": "AAC",
            "Free Lossless Audio Codec (FLAC)": "FLC",
            "Opus (low-latency lossy audio codec)": "OPS",
            "Ogg Opus (Opus audio in Ogg container)": "OPS",
            "Ogg Vorbis (lossy audio codec)": "OGG",
        }

        return mapping.get(format_str, format_str[:3].upper() if format_str else "")

import subprocess
import logging
import os
import sys
import time
import numpy as np

from pathlib import Path
from PIL import ImageFont
from luma.core.render import canvas

logger = logging.getLogger(__name__)

CAVA_FIFO = "/tmp/cava_fifo_vu"
FONT_STYLE_1 = Path(__file__).parent.parent / "fonts" / "kollection_bitmap.ttf"


class WidgetVUMeter:
    def __init__(self):
        self.num_bars = 2
        self.smoothed_levels = np.zeros(2)
        self.peak_hold_time = np.zeros(2)
        self.peaks = np.zeros(2)
        self.cava_config = Path(__file__).parent.parent / "widgets" / "vu_meter.conf"
        self.cava_process = None
        self.data_received = False
        self.frame = 0
        self.last_data = None
        self.init()

    def init(self):
        if os.path.exists(CAVA_FIFO):
            os.unlink(CAVA_FIFO)
        
        os.mkfifo(CAVA_FIFO)
        
        try:
            self.cava_process = subprocess.Popen(
                ["cava", "-p", self.cava_config],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.debug("Started CAVA...")
            time.sleep(0.2)

            fd = os.open(CAVA_FIFO, os.O_RDONLY | os.O_NONBLOCK)
            self.fifo = os.fdopen(fd, 'rb', buffering=0) 
            
        except Exception as e:
            logger.error(f"Error starting CAVA: {e}")
            self.cleanup()
            return

    def cleanup(self, signum=None, frame=None):
        self.stop_threads = True
        
        if self.fifo:
            try:
                self.fifo.close()
            except:
                pass
        
        if self.cava_process:
            self.cava_process.terminate()
            self.cava_process.wait() 

    def draw(
        self,
        draw,
        width=128,
        height=20,
        y=0,
        x=0,
        bar_pattern="checkerboard",
        labels=True,
    ):
        box_x = x + 10
        box_y = y + 10 if labels else y
        box_padding = 3
        box_width = width - 12
        box_height = height

        available_height = box_height - (2 * box_padding)
        bar_height = (available_height - 1) // 2

        left_bar_y = box_y + box_padding
        right_bar_y = left_bar_y + bar_height + 2
        bar_width = box_width - (2 * box_padding)
        percentage_y = box_y - 13

        attack_factor = 0.7
        decay_factor = 0.92
        peak_fall_speed = 1.5
        peak_gap = 2
        hold_frames = 20

        CUSTOM_FONT_SIZE = 16
        font = ImageFont.truetype(FONT_STYLE_1, CUSTOM_FONT_SIZE)

        try:
            available_data = b''
            while True:
                chunk = self.fifo.read(self.num_bars) 
                if not chunk:
                    break
                available_data += chunk
            
            if len(available_data) >= self.num_bars:
                data = available_data[-self.num_bars:]
                self.last_data = data
            elif self.last_data:
                data = self.last_data
            else:
                return
                
        except (BlockingIOError, OSError):
            if self.last_data:
                data = self.last_data
            else:
                return
        except Exception as e:
            if self.last_data:
                data = self.last_data
            else:
                return

        values = np.frombuffer(data, dtype=np.uint8)
        left_raw = values[0]
        right_raw = values[1]

        left_normalized = left_raw / 255.0
        right_normalized = right_raw / 255.0

        left_normalized = np.power(left_normalized, 0.85)
        right_normalized = np.power(right_normalized, 0.85)

        left_level = left_normalized * bar_width
        right_level = right_normalized * bar_width

        current_levels = np.array([left_level, right_level])
        current_levels = np.clip(current_levels, 0, bar_width)

        for i in range(2):
            if current_levels[i] > self.smoothed_levels[i]:
                self.smoothed_levels[i] = (
                    attack_factor * current_levels[i]
                    + (1 - attack_factor) * self.smoothed_levels[i]
                )
            else:
                self.smoothed_levels[i] = self.smoothed_levels[i] * decay_factor

        self.smoothed_levels = np.maximum(self.smoothed_levels, current_levels * 0.05)

        for i in range(2):
            min_peak = self.smoothed_levels[i] + peak_gap

            if self.smoothed_levels[i] >= self.peaks[i]:
                self.peaks[i] = self.smoothed_levels[i]
                self.peak_hold_time[i] = hold_frames
            elif self.peaks[i] <= min_peak:
                self.peaks[i] = min_peak
                self.peak_hold_time[i] = hold_frames
            else:
                if self.peak_hold_time[i] > 0:
                    self.peak_hold_time[i] -= 1
                else:
                    self.peaks[i] = max(self.peaks[i] - peak_fall_speed, min_peak)

        draw.rectangle(
            (box_x, box_y, box_x + box_width - 1, box_y + box_height - 1),
            fill="black",
        )

        for x in range(box_width):
            if x % 2 == 0:
                draw.point((box_x + x, box_y), fill="white")

        for x in range(box_width):
            if x % 2 == 0:
                draw.point((box_x + x, box_y + box_height - 1), fill="white")

        draw.line((box_x, box_y, box_x, box_y + box_height - 1), fill="white")

        draw.line(
            (
                box_x + box_width - 1,
                box_y,
                box_x + box_width - 1,
                box_y + box_height - 1,
            ),
            fill="white",
        )

        marker_positions = [
            (0, "00"),
            (0.25, "25"),
            (0.50, "50"),
            (0.75, "75"),
            (1.0, "100"),
        ]

        for position, label in marker_positions:
            marker_x = box_x + box_padding + int(position * bar_width)

            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(label) * 5

            text_x = marker_x - text_width // 2
            text_x = max(0, min(text_x, width - text_width))

            draw.text((text_x, percentage_y), label, fill="white", font=font)

        max_bar_width = bar_width
        left_width = int(self.smoothed_levels[0])
        left_peak = int(self.peaks[0])

        right_width = int(self.smoothed_levels[1])
        right_peak = int(self.peaks[1])

        draw.text((box_x - 7, left_bar_y - 7), "L", fill="white", font=font)

        draw.text((box_x - 7, right_bar_y - 5), "R", fill="white", font=font)

        if left_width > 0:
            self.draw_textured_bar(
                draw,
                box_x + box_padding,
                left_bar_y,
                left_width,
                bar_height,
                bar_pattern,
            )

        if left_peak > 0 and left_peak <= max_bar_width:
            if left_peak > left_width:
                draw.rectangle(
                    (
                        box_x + box_padding + left_peak,
                        left_bar_y,
                        box_x + box_padding + left_peak + 1,
                        left_bar_y + bar_height - 1,
                    ),
                    fill="white",
                )

        if right_width > 0:
            self.draw_textured_bar(
                draw,
                box_x + box_padding,
                right_bar_y,
                right_width,
                bar_height,
                bar_pattern,
            )

        if right_peak > 0 and right_peak <= max_bar_width:
            if right_peak > right_width:
                draw.rectangle(
                    (
                        box_x + box_padding + right_peak,
                        right_bar_y,
                        box_x + box_padding + right_peak + 1,
                        right_bar_y + bar_height - 1,
                    ),
                    fill="white",
                )

        self.frame += 1

    def draw_textured_bar(self, draw, x, y, width, height, pattern):
        if pattern == "checkerboard":
            for i in range(width):
                for j in range(height):
                    if (i + j) % 2 == 0:
                        draw.point((x + i, y + j), fill="white")
        else:
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill="white")

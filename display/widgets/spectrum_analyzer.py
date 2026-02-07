import os
import logging
import subprocess
import time
import sys
import numpy as np

from pathlib import Path

logger = logging.getLogger(__name__)

CAVA_FIFO = "/tmp/cava_fifo_sa"

class WidgetSpectumAnalyzer:
    def __init__(self, device, num_bars=51):
        self.device = device
        self.num_bars = num_bars
        self.smoothed_bars = np.zeros(self.num_bars)
        self.peaks = np.zeros(self.num_bars)
        self.peak_hold_time = np.zeros(self.num_bars)
        self.cava_config = Path(__file__).parent.parent / "widgets" / f"spectrum_analyzer_{self.num_bars}.conf"
        self.cava_process = None
        self.data_received = False
        self.frame = 0
        self.fifo = None
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
            try:
                self.cava_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.cava_process.kill()
        sys.exit(0)

    def draw_textured_bar(self, draw, x, y, width, height, pattern, color):
        if pattern == "solid":
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill=color)

    def draw(
        self,
        draw,
        width=256,
        height=20,
        y=0,
        x=0,
        bar_pattern="solid",
        labels=True,
        bar_color="white",
        bar_gap=1,
    ):
        attack_factor = 0.5
        decay_factor = 0.95
        peak_fall_speed = 2.5
        peak_gap = 2
        min_bar_height = 1
        hold_frames = 8

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

        current_bars = np.frombuffer(data, dtype=np.uint8).astype(float)
        current_bars = (current_bars / 255.0) * height
        current_bars = current_bars * 2.2
        current_bars = np.power(current_bars, 0.8)

        attack_mask = current_bars > self.smoothed_bars
        self.smoothed_bars[attack_mask] = (
            attack_factor * current_bars[attack_mask]
            + (1 - attack_factor) * self.smoothed_bars[attack_mask]
        )
        decay_mask = ~attack_mask
        self.smoothed_bars[decay_mask] = self.smoothed_bars[decay_mask] * decay_factor
        self.smoothed_bars = np.maximum(self.smoothed_bars, current_bars * 0.05)

        for i in range(self.num_bars):
            min_peak = self.smoothed_bars[i] + peak_gap + 1
            if self.smoothed_bars[i] >= self.peaks[i]:
                self.peaks[i] = self.smoothed_bars[i]
                self.peak_hold_time[i] = hold_frames
            elif self.peaks[i] <= min_peak:
                self.peaks[i] = min_peak
                self.peak_hold_time[i] = hold_frames
            else:
                if self.peak_hold_time[i] > 0:
                    self.peak_hold_time[i] -= 1
                else:
                    self.peaks[i] = max(self.peaks[i] - peak_fall_speed, min_peak)

        baseline_y = y + height
        draw.line((x, baseline_y, x + width - 1, baseline_y), fill="white")

        bar_width = (width // self.num_bars) - bar_gap
        for i in range(self.num_bars):
            _height = max(int(self.smoothed_bars[i]), min_bar_height)
            peak_height = int(self.peaks[i])
            bar_x = x + i * (bar_width + bar_gap)
            bar_y = y + height - _height

            self.draw_textured_bar(
                draw, bar_x, bar_y, bar_width, _height, bar_pattern, bar_color
            )

            if peak_height > _height + peak_gap:
                peak_y = y + height - peak_height
                draw.line((bar_x, peak_y, bar_x + bar_width - 1, peak_y), fill="white")

    def draw_textured_bar(self, draw, x, y, width, height, pattern, color="white"):
        if pattern == "checkerboard":
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill="black")
            bottom_y = y + height - 1
            for i in range(width):
                for j in range(height):
                    dot_y = bottom_y - j
                    if (i + j) % 2 == 0:
                        draw.point((x + i, dot_y), fill=color)

        elif pattern == "gradient":
            if isinstance(color, str) and color != "white":
                draw.rectangle((x, y, x + width - 1, y + height - 1), fill=color)
            else:
                brightness = 255 if color == "white" else color
                for j in range(height):
                    if height <= 1:
                        gradient_brightness = "white"  # White for minimum height
                    else:
                        gradient_brightness = int(
                            brightness * (1 - j / max(height, 1)) * 0.5
                            + brightness * 0.5
                        )
                    draw.line(
                        (x, y + j, x + width - 1, y + j), fill=gradient_brightness
                    )

        elif pattern == "dots":
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill="black")
            bottom_y = y + height - 1
            for i in range(0, width, 2):
                for j in range(0, height, 2):
                    dot_y = bottom_y - j
                    draw.point((x + i, dot_y), fill=color)

        elif pattern == "horizontal_lines":
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill="black")
            bottom_y = y + height - 1
            for j in range(0, height, 2):
                line_y = bottom_y - j
                draw.line((x, line_y, x + width - 1, line_y), fill=color)

        elif pattern == "vertical_lines":
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill="black")
            for i in range(0, width, 2):
                draw.line((x + i, y, x + i, y + height - 1), fill=color)
        else:
            draw.rectangle((x, y, x + width - 1, y + height - 1), fill=color)

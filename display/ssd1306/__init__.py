import time
import logging
import threading
import numpy as np

from pathlib import Path
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1322
from luma.core.sprite_system import framerate_regulator

from display.widgets.vu_meter import WidgetVUMeter
from display.widgets.spectrum_analyzer import WidgetSpectumAnalyzer
from display.widgets.text_scrollable import WidgetTextScrollable

logger = logging.getLogger(__name__)

CAVA_FIFO = '/tmp/cava_fifo'
FONT_STYLE_1 = Path(__file__).parent.parent / "fonts" / "DotMatrix-Custom-5x7.ttf"
FONT_STYLE_2 = Path(__file__).parent.parent / "fonts" / "lcddot_tr.ttf"

class DisplaySSD1306:
    def __init__(self, visualizer=None, contrast=255):
        self.width = 256
        self.height = 64
        self.visualizer = visualizer
        self.serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)
        self.device = ssd1322(self.serial, width=self.width, height=self.height)
        self.device.contrast(contrast)
        self.running = False
        self.display_thread = None
        self._track = None
    
    def set_current_track(self, track):
        self._track = track

    def _display_loop(self):
        regulator = framerate_regulator(fps=60)
        
        widget_title = WidgetTextScrollable(self.device, screen_width=self.width, font_size=33, font_path=FONT_STYLE_1)
        widget_artist = WidgetTextScrollable(self.device, screen_width=self.width, font_size=16, font_path=FONT_STYLE_2)
        widget_spectrum_analyzer = WidgetSpectumAnalyzer(self.device, num_bars=64)
        #widget_vumeter = WidgetVUMeter(self.device)

        while self.running:
            with regulator:
                with canvas(self.device) as draw:
                    if self._track is not None:
                        widget_title.draw(draw, width=200, x=-3, y=-5, text=self._track.name)

                        if len(self._track.artists):
                            widget_artist.draw(draw, width=256, x=0, y=24, text=next(iter(self._track.artists)).name)

                    widget_spectrum_analyzer.draw(draw, width=256, height=20, x=0, y=44, bar_pattern="solid", bar_color="white")
                    #widget_vumeter.draw(draw, width=128, x=0, y=34,  bar_pattern='checkerboard')

    def display(self):
        if not self.running:
            self.running = True
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
            logger.info("SSD1322 Display Initialized")
    
    def stop(self):
        self.running = False
        if self.display_thread is not None and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        self.device.clear()        
        logger.info("SSD1322 Display stopped")
        
    
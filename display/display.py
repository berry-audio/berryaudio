import logging
import alsaaudio
import math
import asyncio
import json
import subprocess

from pathlib import Path
from typing import Optional
from core.actor import Actor
from .ssd1322 import DisplaySSD1322
from .ssd1306 import DisplaySSD1306

logger = logging.getLogger(__name__)


class DisplayExtension(Actor):
    def __init__(self, name, core, db, config):
        super().__init__()
        self._name = name
        self._core = core
        self._db = db
        self._config = config
        self._device = "ssd1322"
        self._visualizer = "spectrum_analyzer"
        self._controller = None
        self._loop = asyncio.get_running_loop()

    async def on_config_update(self, config):
        pass
    
    async def on_event(self, message):
        self._controller.set_message(message)
        
    async def on_start(self):
        if self._device == "ssd1322":
            self._controller = DisplaySSD1322(visualizer=self._visualizer, contrast=255)

        if self._device == "ssd1306":
            self._controller = DisplaySSD1306(visualizer=self._visualizer, contrast=255)

        if self._controller is not None:
            self._controller.init()
       
        logger.info("Started")


    async def on_stop(self):
        self._controller.stop()
        logger.info("Stopped")

    
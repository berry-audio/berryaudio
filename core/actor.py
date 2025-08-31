import asyncio
import traceback

class Actor:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.running = True
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop

    async def _send(self, message):
        await self.queue.put(message)

    def send(self, message):
        if self._loop is None or not self.running or self._loop.is_closed():
            return  
        try:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._send(message))
            )
        except RuntimeError:
            pass


    async def run(self):
        self._loop = asyncio.get_running_loop()
        try:
            await self.safe_call(self.on_start, "on_start")
            while self.running:
                try:
                    message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

                await self.safe_call(self.on_event, "on_event", message)
        except Exception:
            print(f"[{self.__class__.__name__}] Fatal error in actor loop:\n{traceback.format_exc()}")
        

    async def safe_call(self, func, name, *args):
        """Run hook safely, log exceptions but keep actor alive."""
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args)
            else:
                func(*args)
        except Exception:
            print(f"[{self.__class__.__name__}] Error in {name}:\n{traceback.format_exc()}")

import asyncio
import traceback


class Actor:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.running = True
        self._loop = None
        self._stop_event = None  

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

    async def stop(self):
        self.running = False
        if self._stop_event:
            self._stop_event.set()

    async def run(self):
        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        try:
            await self.safe_call(self.on_start, "on_start")
            while self.running:
                try:
                    get_task = asyncio.create_task(self.queue.get())
                    stop_task = asyncio.create_task(self._stop_event.wait())
                    done, pending = await asyncio.wait(
                        [get_task, stop_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for t in pending:
                        t.cancel()
                    if stop_task in done:
                        break
                    if get_task in done:
                        message = get_task.result()
                        await self.safe_call(self.on_event, "on_event", message)
                except asyncio.CancelledError:
                    break
        except Exception:
            print(f"[{self.__class__.__name__}] Fatal error in actor loop:\n{traceback.format_exc()}")
        finally:
            await self.safe_call(self.on_stop, "on_stop")

    async def safe_call(self, func, name, *args):
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args)
            else:
                func(*args)
        except Exception:
            print(f"[{self.__class__.__name__}] Error in {name}:\n{traceback.format_exc()}")

    async def on_start(self): pass
    async def on_stop(self): pass
    async def on_event(self, message): pass


class SourceActor(Actor):
    pass

import asyncio
from buffer.buffer_reader import BufferReader
from constants import Constants

class NodeLifecycle:
    def __init__(self, transport, emitter=None):
        self.transport = transport
        self._running = False
        self._task = None
        # Optional: an EventEmitter or compatible interface with emit()
        self._emitter = emitter

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._rx_loop())
        if self._emitter:
            self._emitter.emit("listening")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        await self.transport.close()
        if self._emitter:
            self._emitter.emit("stopped")

    async def _rx_loop(self):
        while self._running:
            try:
                frame = await self.transport.receive()
                if frame:
                    await self.on_frame_received(frame)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._emitter:
                    self._emitter.emit("error", {"error": e})
            await asyncio.sleep(0.01)

    async def on_frame_received(self, frame_bytes: bytes):
        reader = BufferReader(frame_bytes)
        cmd = reader.read_uint8()
        # This method should be overridden or wired to a dispatcher
        # e.g., call an injected dispatcher: self._dispatch(cmd, reader)
        if self._emitter:
            self._emitter.emit("debug", {"cmd": cmd})

import asyncio
from typing import Callable, Any


class TaskQueue:
    def __init__(self, worker_count: int = 2):
        self.queue = asyncio.Queue()
        self.workers = []
        self.worker_count = worker_count
        self._running = False

    async def start(self, handler: Callable[[dict], Any]):
        if self._running:
            return
        self._running = True
        for _ in range(self.worker_count):
            self.workers.append(asyncio.create_task(self._worker(handler)))

    async def _worker(self, handler: Callable[[dict], Any]):
        while True:
            item = await self.queue.get()
            try:
                await handler(item)
            finally:
                self.queue.task_done()

    async def enqueue(self, item: dict):
        await self.queue.put(item)


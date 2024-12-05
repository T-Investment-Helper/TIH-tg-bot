import asyncio
from typing import Any, Dict, List, Callable

class AsyncBatchRouter:
    def __init__(self, batch_size: int, timeout: int):
        self.queue = asyncio.Queue()
        self.batch_size = batch_size
        self.timeout = timeout

    async def add_request(self, request: Dict[str, Any]):
        await self.queue.put(request)

    async def process_batches(self):
        while True:
            batch = []
            try:
                batch.append(await asyncio.wait_for(self.queue.get(), timeout=self.timeout))
                while len(batch) < self.batch_size:
                    try:
                        batch.append(await asyncio.wait_for(self.queue.get(), timeout=self.timeout))
                    except asyncio.TimeoutError:
                        break
                await self.process_batch(batch)
            except asyncio.TimeoutError:
                if batch:
                    await self.process_batch(batch)

    async def process_batch(self, batch: List[Dict[str, Any]]):
        tasks = [self.handle_request(request) for request in batch]
        await asyncio.gather(*tasks)

    async def handle_request(self, request: Dict[str, Any]):
        raise NotImplementedError("Метод должен быть переопределен.")

class RequestRouter(AsyncBatchRouter):
    def __init__(self, batch_size: int, timeout: int, connector: Callable, analyzer: Callable, bot: Any):
        super().__init__(batch_size, timeout)
        self.connector = connector
        self.analyzer = analyzer
        self.bot = bot

    async def handle_request(self, request: Dict[str, Any]):
        user_id = request["user_id"]
        token = request["token"]
        period = request["period"]

        try:
            data = await self.connector.get_data(token, period)
            analysis_result = await self.analyzer.analyze_data(data)
            await self.bot.send_message(user_id, f"Результаты анализа: {analysis_result}")
        except Exception as e:
            await self.bot.send_message(user_id, f"Ошибка обработки запроса: {e}")

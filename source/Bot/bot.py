import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from pathlib import Path
from source.config_getter import config
from handlers import common, registration, statistics, exceptions

logging.basicConfig(level=logging.INFO)

#TODO: choose a more optimal storage
storage = MemoryStorage()

async def main():
    path = Path.cwd()
    while path.name != "TIH-tg-bot":
        path = path.parent
    analyzer_requests_path = path / "analyzer_requests"
    analyzer_requests_path.mkdir(exist_ok=True)
    analyzer_responses_path = path / "analyzer_responses"
    analyzer_responses_path.mkdir(exist_ok=True)
    connector_requests_path = path / "connector_requests"
    connector_requests_path.mkdir(exist_ok=True)

    bot = Bot(
        token=config.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN_V2
        ),
        storage=storage
    )
    dp = Dispatcher()

    dp.include_routers(common.router, registration.router, statistics.router, exceptions.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
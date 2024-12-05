import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config_getter import config
from handlers import common, registration, statistics, exceptions

logging.basicConfig(level=logging.INFO)

#TODO: choose a more optimal storage
storage = MemoryStorage()

async def main():
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
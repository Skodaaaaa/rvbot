import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.loader import register_routers
from app.config import load_config
from app.storage.raid_storage import RaidStorage
from app.storage.settings_storage import SettingsStorage


async def main() -> None:
    config = load_config()

    settings_storage = SettingsStorage()
    await settings_storage.initialize()

    raid_storage = RaidStorage()
    await raid_storage.initialize()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    register_routers(dispatcher)

    await bot.delete_webhook(drop_pending_updates=True)
    bot_info = await bot.get_me()
    logging.info("Бот запущен: @%s, ID: %s", bot_info.username, bot_info.id)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем.")

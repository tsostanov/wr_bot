import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, LOG_LEVEL
from database import init_db
from handlers.archive import router as archive_router
from handlers.focus import router as focus_router
from handlers.menu import router as menu_router
from handlers.schedule import router as schedule_router
from handlers.settings import router as settings_router
from handlers.tasks import router as tasks_router


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


async def main() -> None:
    configure_logging()
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(menu_router)
    dp.include_router(tasks_router)
    dp.include_router(focus_router)
    dp.include_router(schedule_router)
    dp.include_router(settings_router)
    dp.include_router(archive_router)

    logging.getLogger(__name__).info("Bot started")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from handlers.menu import router as menu_router
from handlers.tasks import router as tasks_router
from handlers.archive import router as archive_router
from handlers.focus import router as focus_router
from handlers.settings import router as settings_router
from handlers.schedule import router as schedule_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(menu_router)
    dp.include_router(tasks_router)
    dp.include_router(archive_router)
    dp.include_router(focus_router)
    dp.include_router(settings_router)
    dp.include_router(schedule_router)

    print('🤖 Бот запущен...')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

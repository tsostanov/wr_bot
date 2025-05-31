from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import summarize_archive

router = Router()


@router.message(Command(commands=['archive']))
async def cmd_archive(message: Message):
    data = summarize_archive(message.from_user.id)
    if not data:
        return await message.reply('🧾 Архив пока пуст.')
    text = '🧾 Архив побед:\n'
    for type_, count in data:
        text += f'{type_.capitalize()}: {count}\n'
    await message.reply(text)

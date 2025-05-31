from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

router = Router()


@router.message(Command('start', 'help'))
async def cmd_help(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='/add'),      KeyboardButton(text='/list'),
             KeyboardButton(text='/today')],
            [KeyboardButton(text='/done'),
             KeyboardButton(text='/archive')],
            [KeyboardButton(text='/setnorm'),  KeyboardButton(text='/report')],
            [KeyboardButton(text='/settings'),
             KeyboardButton(text='/setmode')],
            [KeyboardButton(text='/help')]
        ],
        resize_keyboard=True
    )
    text = (
        '👋 Привет! Я твой WhiteRoom бот. Вот мои команды:\n\n'
        '/add <текст>        — добавить задачу\n'
        '/list               — показать все задачи\n'
        '/today              — задачи на сегодня и запуск таймера\n'
        '/done <id>          — отметить задачу выполненной\n'
        '/archive            — показать архив побед\n'
        '/setnorm <часы>     — задать норму работы в день (например: /setnorm 5.0)\n'
        '/report             — показать отчёт по Deep Work сегодня\n'
        '/settings           — показать текущие настройки (режим + норма)\n'
        '/setmode <deep|pomodoro> — переключить режим работы\n'
        '/help               — показать это меню'
    )
    await message.answer(text, reply_markup=kb)

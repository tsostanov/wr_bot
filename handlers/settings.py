from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import get_user_mode, set_user_mode, get_daily_norm

router = Router()


@router.message(Command(commands=['settings']))
async def cmd_settings(message: Message):
    """
    Показывает текущие настройки пользователя: режим и дневную норму часов.
    """
    user_id = message.from_user.id
    mode = get_user_mode(user_id)
    norm = get_daily_norm(user_id)
    if norm is None:
        norm_display = 'не задана (используй /setnorm)'
    else:
        norm_display = f'{norm:.2f} ч.'

    if mode == 'deep':
        mode_display = 'Deep Work (4 ч работы + 1 ч перерыв)'
    elif mode == 'pomodoro':
        mode_display = 'Pomodoro (25 мин работы + 5 мин перерыва)'
    else:
        mode_display = f'Неизвестный ({mode})'

    text = (
        '⚙️ Текущие настройки:\n\n'
        f'• Режим работы: {mode_display}\n'
        f'• Дневная норма: {norm_display}\n\n'
        'Чтобы сменить режим, используй команду:\n'
        '/setmode <deep|pomodoro>\n'
        'Пример: /setmode pomodoro'
    )
    await message.reply(text)


@router.message(Command(commands=['setmode']))
async def cmd_setmode(message: Message):
    """
    Позволяет переключить режим работы: 'deep' или 'pomodoro'.
    Пример: /setmode pomodoro
    """
    parts = message.text.split()
    if len(parts) != 2 or parts[1].lower() not in ['deep', 'pomodoro']:
        return await message.reply(
            '⚠️ Использование: /setmode <deep|pomodoro>\n'
            'Где:\n'
            '  deep      — Deep Work (4 ч работы + 1 ч перерыв)\n'
            '  pomodoro  — Pomodoro (25 мин работы + 5 мин перерыва)'
        )
    mode = parts[1].lower()
    set_user_mode(message.from_user.id, mode)
    if mode == 'deep':
        await message.reply('✅ Режим изменён на Deep Work (4 ч работы + 1 ч перерыв).')
    else:
        await message.reply('✅ Режим изменён на Pomodoro (25 мин работы + 5 мин перерыва).')

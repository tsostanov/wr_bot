import asyncio
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from database import (
    list_tasks,
    set_daily_norm,
    get_daily_norm,
    log_focus_session,
    get_today_focus_time,
)
from datetime import datetime, timedelta

router = Router()

# Словарь для хранения активных asyncio.Task по Deep Work для каждого пользователя:
# ключ = user_id, значение = {"task": asyncio.Task, "message_id": int, "chat_id": int, "start_time": datetime}
active_timers: dict[int, dict] = {}

# Флаг для тестирования: если True, 4 ч = 4 сек, 1 ч = 1 сек
TEST_MODE = False


@router.message(Command(commands=['setnorm']))
async def cmd_setnorm(message: Message):
    """
    Устанавливает дневную норму часов. Пример: /setnorm 5.0
    """
    parts = message.text.split()
    if len(parts) != 2:
        return await message.reply('⚠️ Использование: /setnorm <часы> (например: /setnorm 5.0)')
    try:
        hours = float(parts[1])
    except ValueError:
        return await message.reply('⚠️ Введи число, например: /setnorm 4.0')
    set_daily_norm(message.from_user.id, hours)
    await message.reply(f'✅ Норма на день установлена: {hours:.2f} ч.')


@router.message(Command(commands=['today']))
async def cmd_today_focus(message: Message):
    """
    Показывает список активных задач и предлагает выбрать ID для real Deep Work (4 ч работы + 1 ч перерыв).
    """
    tasks = list_tasks(message.from_user.id, include_done=False)
    if not tasks:
        return await message.reply('📅 Нет активных задач для Deep Work.')
    text = '📅 Задачи на сегодня:\n'
    for tid, title, _ in tasks:
        text += f'{tid}. {title}\n'
    text += '\n👉 Отправь ID задачи (цифру), чтобы начать Deep Work (4 ч).'
    await message.reply(text)


@router.message(F.text.regexp(r'^\d+$'))
async def start_real_timer(message: Message):
    """
    Пользователь отправляет ID (цифру) — запускаем «реальный» таймер Deep Work (4 ч) для этой задачи.
    """
    user_id = message.from_user.id
    if user_id in active_timers:
        return await message.reply('⚠️ У тебя уже запущен таймер. Сначала останови текущий (кнопка «⏹️»).')

    tid = int(message.text)
    tasks = list_tasks(user_id, include_done=False)
    task = next((t for t in tasks if t[0] == tid), None)
    if not task:
        return await message.reply('⚠️ Неверный ID задачи. Повтори команду /today и выбери существующий ID.')
    title = task[1]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='⏹️ Остановить таймер', callback_data=f'stop_timer:{user_id}')]
        ]
    )

    total_seconds = 4 if TEST_MODE else 4 * 3600
    display = '00:00:04' if TEST_MODE else '04:00:00'
    sent = await message.reply(
        f'🧠 Deep Work стартовал по задаче: "{title}"\n⏱️ Время осталось: {display}',
        reply_markup=kb
    )

    start_time = datetime.now()
    task_obj = asyncio.create_task(
        deep_work_countdown(
            bot=message.bot,
            chat_id=sent.chat.id,
            message_id=sent.message_id,
            user_id=user_id,
            title=title,
            start_time=start_time
        )
    )
    active_timers[user_id] = {
        "task": task_obj,
        "message_id": sent.message_id,
        "chat_id": sent.chat.id,
        "start_time": start_time
    }


async def deep_work_countdown(bot, chat_id: int, message_id: int, user_id: int, title: str, start_time: datetime):
    """
    Фоновый цикл, который каждую секунду уменьшает оставшееся время,
    редактирует сообщение. Когда таймер доходит до нуля,
    логирует в архив и уведомляет о начале перерыва (1 ч).
    """
    total_seconds = 4 if TEST_MODE else 4 * 3600
    elapsed = 0

    try:
        while elapsed < total_seconds:
            await asyncio.sleep(1)
            elapsed += 1
            remaining = total_seconds - elapsed
            hrs = remaining // 3600
            mins = (remaining % 3600) // 60
            secs = remaining % 60
            if TEST_MODE:
                display = f'00:00:0{remaining}'
            else:
                display = f'{hrs:02d}:{mins:02d}:{secs:02d}'
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=(
                        f'🧠 Deep Work по задаче: "{title}"\n'
                        f'⏱️ Время осталось: {display}'
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(
                                text='⏹️ Остановить таймер', callback_data=f'stop_timer:{user_id}')]
                        ]
                    )
                )
            except:
                pass

        log_focus_session(user_id, title, 4.0)
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f'✅ Deep Work (4 ч) по задаче "{title}" завершён и записан в архив.\n'
                f'⏳ Начинается перерыв 1 ч.'
            )
        )

        break_seconds = 1 if TEST_MODE else 3600
        await asyncio.sleep(break_seconds)

        await bot.send_message(
            chat_id=chat_id,
            text='⏰ Перерыв (1 ч) завершён. Готов к следующей Deep Work сессии!'
        )

    except asyncio.CancelledError:
        return
    finally:
        active_timers.pop(user_id, None)


@router.callback_query(F.data.startswith('stop_timer:'))
async def cmd_stop_timer(callback: CallbackQuery):
    """
    Обработка нажатия кнопки «Остановить таймер». Отменяем задачу,
    считаем, сколько успел сделать, и записываем это в архив.
    """
    data = callback.data
    try:
        _, uid_str = data.split(':')
        user_id = int(uid_str)
    except:
        return await callback.answer()

    if user_id not in active_timers:
        return await callback.answer('⚠️ У тебя нет активного таймера.', show_alert=True)

    rec = active_timers[user_id]
    task_obj = rec['task']
    start_time = rec['start_time']
    chat_id = rec['chat_id']

    task_obj.cancel()

    now = datetime.now()
    diff = now - start_time
    seconds_done = diff.seconds

    hours_done = round(seconds_done / 3600, 2)

    log_focus_session(user_id, f'Deep Work (прервано)', hours_done)

    await callback.message.reply(
        f'⏹️ Таймер остановлен. Ты успел провести Deep Work: {hours_done:.2f} ч. '
        f'Это время записано в архив.'
    )

    active_timers.pop(user_id, None)

    await callback.answer()


@router.message(Command(commands=['report']))
async def cmd_report(message: Message):
    """
    Показывает, сколько Deep Work-часов сделано за сегодня и сравнивает с дневной нормой.
    """
    today_time = get_today_focus_time(message.from_user.id)
    norm = get_daily_norm(message.from_user.id)
    text = f'📊 Сегодня ты вложил в Deep Work: {today_time:.2f} ч.\n'
    if norm is not None:
        diff = norm - today_time
        if diff > 0:
            text += f'🔽 До нормы осталось: {diff:.2f} ч.'
        else:
            text += '✅ Норма выполнена или перевыполнена!'
    else:
        text += '⚠️ Норма на день не установлена. Задай через /setnorm <часы>, например: /setnorm 5.0'
    await message.reply(text)

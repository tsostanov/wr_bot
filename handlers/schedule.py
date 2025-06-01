from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timedelta
from database import add_event, get_events_by_date, get_all_events, delete_event

router = Router()


@router.message(Command(commands=['add_event']))
async def cmd_add_event(message: Message):
    """
    Добавляет новое событие в расписание.
    Формат:
    /add_event 2025-06-05 14:00 Название события | Описание (опционально)

    Примеры:
    /add_event 2025-06-05 14:00 Собеседование в Яндексе | Приготовить резюме
    /add_event 2025-06-07 09:00 Экзамен по математике
    /add_event 2025-06-10 Сдача проекта
    """
    text = message.text.partition(' ')[2].strip()
    if not text:
        return await message.reply(
            "⚠️ Использование: /add_event <YYYY-MM-DD> <HH:MM> Название | Описание (опционально)\n"
            "Пример: /add_event 2025-06-05 14:00 Собеседование в Яндексе | Приготовить резюме"
        )

    parts = text.split(' ', 2)
    if len(parts) < 2:
        return await message.reply("⚠️ Ошибка формата. См.: /add_event YYYY-MM-DD HH:MM Название | Описание")

    date_part = parts[0]
    time_part = parts[1]
    remainder = parts[2] if len(parts) == 3 else ''

    try:
        datetime.strptime(date_part, '%Y-%m-%d')
    except ValueError:
        return await message.reply("⚠️ Неверный формат даты. Используйте YYYY-MM-DD")

    event_time = None
    if time_part != '':
        try:
            datetime.strptime(time_part, '%H:%M')
            event_time = time_part
        except ValueError:
            event_time = None
            remainder = ' '.join([time_part, remainder]).strip()

    if '|' in remainder:
        title_part, description_part = map(str.strip, remainder.split('|', 1))
    else:
        title_part = remainder.strip()
        description_part = None

    if not title_part:
        return await message.reply("⚠️ Название не может быть пустым. Формат: /add_event YYYY-MM-DD HH:MM Название | Описание")

    event_id = add_event(
        user_id=message.from_user.id,
        title=title_part,
        event_date=date_part,
        event_time=event_time,
        description=description_part
    )
    reply_text = f"✅ Событие добавлено (ID {event_id}):\n• *{title_part}* — {date_part}"
    if event_time:
        reply_text += f" в {event_time}"
    if description_part:
        reply_text += f"\n• Описание: {description_part}"
    await message.reply(reply_text, parse_mode='Markdown')


@router.message(Command(commands=['schedule']))
async def cmd_schedule(message: Message):
    """
    Показывает расписание на сегодня и завтра.
    """
    user_id = message.from_user.id
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    events_today = get_events_by_date(user_id, today)
    events_tomorrow = get_events_by_date(user_id, tomorrow)

    reply_text = f"📅 *Расписание на сегодня* ({today}):\n"
    if events_today:
        for ev_id, title, desc, ev_time in events_today:
            line = f"— [{ev_id}] {title}"
            if ev_time:
                line += f" в {ev_time}"
            if desc:
                line += f" | {desc}"
            reply_text += line + "\n"
    else:
        reply_text += "Нет событий.\n"

    reply_text += f"\n📅 *Расписание на завтра* ({tomorrow}):\n"
    if events_tomorrow:
        for ev_id, title, desc, ev_time in events_tomorrow:
            line = f"— [{ev_id}] {title}"
            if ev_time:
                line += f" в {ev_time}"
            if desc:
                line += f" | {desc}"
            reply_text += line + "\n"
    else:
        reply_text += "Нет событий.\n"

    await message.reply(reply_text, parse_mode='Markdown')


@router.message(Command(commands=['my_events']))
async def cmd_my_events(message: Message):
    """
    Показывает все будущие события пользователя (отсортированы по дате/времени).
    """
    user_id = message.from_user.id
    all_events = get_all_events(user_id)

    if not all_events:
        return await message.reply("📋 У вас нет событий в расписании.")

    reply_text = "📋 *Все ваши предстоящие события:*\n"
    now = datetime.now().strftime('%Y-%m-%d')
    for ev_id, title, desc, ev_date, ev_time in all_events:
        if ev_date < now:
            continue
        line = f"— [{ev_id}] {title} — {ev_date}"
        if ev_time:
            line += f" в {ev_time}"
        if desc:
            line += f" | {desc}"
        reply_text += line + "\n"

    await message.reply(reply_text, parse_mode='Markdown')


@router.message(Command(commands=['delete_event']))
async def cmd_delete_event(message: Message):
    """
    Удаляет событие по ID:
    /delete_event 5
    """
    arg = message.text.partition(' ')[2].strip()
    if not arg.isdigit():
        return await message.reply("⚠️ Использование: /delete_event <id_события> (например: /delete_event 5)")

    ev_id = int(arg)
    success = delete_event(message.from_user.id, ev_id)
    if success:
        await message.reply(f"✅ Событие {ev_id} удалено.")
    else:
        await message.reply(f"❌ Событие {ev_id} не найдено или не принадлежит вам.")

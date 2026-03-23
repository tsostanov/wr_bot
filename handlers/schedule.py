from datetime import datetime, time, timedelta
from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import add_event, delete_event, get_all_events, get_events_by_date


router = Router()


def format_event_line(event_id: int, title: str, description: str | None, event_time: str | None) -> str:
    line = f"[{event_id}] <b>{escape(title)}</b>"
    if event_time:
        line += f" at <code>{event_time}</code>"
    if description:
        line += f" - {escape(description)}"
    return line


@router.message(Command("add_event"))
async def cmd_add_event(message: Message) -> None:
    payload = message.text.partition(" ")[2].strip()
    if not payload:
        await message.reply(
            "Usage: /add_event <YYYY-MM-DD> [HH:MM] <title> | <description>"
        )
        return

    parts = payload.split(" ", 2)
    if len(parts) < 2:
        await message.reply(
            "Usage: /add_event <YYYY-MM-DD> [HH:MM] <title> | <description>"
        )
        return

    event_date = parts[0]
    remainder = ""
    event_time = None

    try:
        datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError:
        await message.reply("Date must be in YYYY-MM-DD format.")
        return

    possible_time = parts[1]
    if len(parts) == 3:
        try:
            datetime.strptime(possible_time, "%H:%M")
            event_time = possible_time
            remainder = parts[2]
        except ValueError:
            remainder = " ".join(parts[1:])
    else:
        try:
            datetime.strptime(possible_time, "%H:%M")
            await message.reply("Event title is required after the time.")
            return
        except ValueError:
            remainder = possible_time

    if "|" in remainder:
        title, description = [part.strip() for part in remainder.split("|", 1)]
    else:
        title = remainder.strip()
        description = None

    if not title:
        await message.reply("Event title cannot be empty.")
        return

    event_id = add_event(
        user_id=message.from_user.id,
        title=title,
        event_date=event_date,
        event_time=event_time,
        description=description,
    )

    text = [f"Event added with ID <b>{event_id}</b>"]
    text.append(f"Title: <b>{escape(title)}</b>")
    text.append(f"Date: <code>{event_date}</code>")
    if event_time:
        text.append(f"Time: <code>{event_time}</code>")
    if description:
        text.append(f"Description: {escape(description)}")

    await message.reply("\n".join(text), parse_mode="HTML")


@router.message(Command("schedule"))
async def cmd_schedule(message: Message) -> None:
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    sections = []
    for label, day in (("Today", today), ("Tomorrow", tomorrow)):
        events = get_events_by_date(message.from_user.id, day.isoformat())
        lines = [f"<b>{label}</b> ({day.isoformat()})"]
        if events:
            for event_id, title, description, event_time in events:
                lines.append(format_event_line(event_id, title, description, event_time))
        else:
            lines.append("No events.")
        sections.append("\n".join(lines))

    await message.reply("\n\n".join(sections), parse_mode="HTML")


@router.message(Command("my_events"))
async def cmd_my_events(message: Message) -> None:
    now = datetime.now()
    events = get_all_events(message.from_user.id)
    upcoming = []

    for event_id, title, description, event_date, event_time in events:
        day = datetime.strptime(event_date, "%Y-%m-%d").date()
        if event_time:
            event_moment = datetime.combine(day, time.fromisoformat(event_time))
        else:
            event_moment = datetime.combine(day, time.max)

        if event_moment >= now:
            upcoming.append((event_id, title, description, event_date, event_time))

    if not upcoming:
        await message.reply("You have no upcoming events.")
        return

    lines = ["<b>Upcoming events</b>"]
    for event_id, title, description, event_date, event_time in upcoming:
        line = f"[{event_id}] <b>{escape(title)}</b> on <code>{event_date}</code>"
        if event_time:
            line += f" at <code>{event_time}</code>"
        if description:
            line += f" - {escape(description)}"
        lines.append(line)

    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("delete_event"))
async def cmd_delete_event(message: Message) -> None:
    arg = message.text.partition(" ")[2].strip()
    if not arg.isdigit():
        await message.reply("Usage: /delete_event <event_id>")
        return

    event_id = int(arg)
    if delete_event(message.from_user.id, event_id):
        await message.reply(f"Event {event_id} deleted.")
        return

    await message.reply("Event not found.")

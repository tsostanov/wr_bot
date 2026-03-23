from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_recent_archive_entries, summarize_archive


router = Router()


@router.message(Command("archive"))
async def cmd_archive(message: Message) -> None:
    summary = summarize_archive(message.from_user.id)
    recent = get_recent_archive_entries(message.from_user.id, limit=5)

    if not summary and not recent:
        await message.reply("Archive is empty.")
        return

    lines = ["<b>Archive summary</b>"]

    if summary:
        for entry_type, total in summary:
            lines.append(f"{escape(entry_type)}: <b>{total}</b>")

    if recent:
        lines.append("")
        lines.append("<b>Recent entries</b>")
        for entry_type, title, entry_date, minutes_spent, comment in recent:
            line = f"{entry_date} - {escape(entry_type)} - <b>{escape(title)}</b>"
            if minutes_spent:
                line += f" ({minutes_spent} min)"
            if comment:
                line += f" - {escape(comment)}"
            lines.append(line)

    await message.reply("\n".join(lines), parse_mode="HTML")

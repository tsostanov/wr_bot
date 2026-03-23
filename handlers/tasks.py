from datetime import datetime
from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import add_archive, add_task, complete_task, list_tasks


router = Router()


@router.message(Command("add"))
async def cmd_add(message: Message) -> None:
    title = message.text.partition(" ")[2].strip()
    if not title:
        await message.reply("Usage: /add <task title>")
        return

    task_id = add_task(message.from_user.id, title)
    await message.reply(f"Task #{task_id} added: <b>{escape(title)}</b>", parse_mode="HTML")


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    tasks = list_tasks(message.from_user.id)
    if not tasks:
        await message.reply("You do not have any tasks yet.")
        return

    lines = ["<b>Your tasks</b>"]
    for task_id, title, status in tasks:
        marker = "done" if status == "done" else "todo"
        lines.append(f"{task_id}. [{marker}] {escape(title)}")

    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("done"))
async def cmd_done(message: Message) -> None:
    arg = message.text.partition(" ")[2].strip()
    if not arg.isdigit():
        await message.reply("Usage: /done <task_id>")
        return

    task_id = int(arg)
    title = complete_task(message.from_user.id, task_id)
    if title is None:
        await message.reply(f"Task #{task_id} was not found.")
        return

    add_archive(
        user_id=message.from_user.id,
        entry_type="task",
        title=title,
        entry_date=datetime.now().date().isoformat(),
        comment="Marked as done",
    )
    await message.reply(
        f"Task #{task_id} marked as done and moved to archive: <b>{escape(title)}</b>",
        parse_mode="HTML",
    )

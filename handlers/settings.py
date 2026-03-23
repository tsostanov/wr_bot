from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_daily_norm, get_user_mode, set_daily_norm, set_user_mode


router = Router()
AVAILABLE_MODES = {"deep": "Deep Work", "pomodoro": "Pomodoro"}


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    user_id = message.from_user.id
    mode = get_user_mode(user_id)
    norm = get_daily_norm(user_id)

    norm_text = "not set" if norm is None else f"{norm:.2f} h"
    mode_text = AVAILABLE_MODES.get(mode, mode)

    await message.reply(
        (
            "<b>Current settings</b>\n"
            f"Mode: <b>{mode_text}</b>\n"
            f"Daily norm: <b>{norm_text}</b>\n\n"
            "Commands:\n"
            "/setmode <deep|pomodoro>\n"
            "/setnorm <hours>"
        ),
        parse_mode="HTML",
    )


@router.message(Command("setmode"))
async def cmd_setmode(message: Message) -> None:
    mode = message.text.partition(" ")[2].strip().lower()
    if mode not in AVAILABLE_MODES:
        await message.reply("Usage: /setmode <deep|pomodoro>")
        return

    set_user_mode(message.from_user.id, mode)
    await message.reply(f"Work mode updated: {AVAILABLE_MODES[mode]}")


@router.message(Command("setnorm"))
async def cmd_setnorm(message: Message) -> None:
    value = message.text.partition(" ")[2].strip()
    if not value:
        await message.reply("Usage: /setnorm <hours>")
        return

    try:
        hours = float(value)
    except ValueError:
        await message.reply("Daily norm must be a number, for example: /setnorm 4.5")
        return

    if hours <= 0:
        await message.reply("Daily norm must be greater than zero.")
        return

    set_daily_norm(message.from_user.id, hours)
    await message.reply(f"Daily norm saved: {hours:.2f} h")

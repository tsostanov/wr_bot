import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import TEST_MODE
from database import (
    get_daily_norm,
    get_task,
    get_today_focus_time,
    get_user_mode,
    list_tasks,
    log_focus_session,
)


logger = logging.getLogger(__name__)
router = Router()


class FocusState(StatesGroup):
    waiting_for_task_id = State()


@dataclass
class TimerPreset:
    mode: str
    label: str
    work_seconds: int
    work_hours: float
    break_seconds: int
    break_label: str


@dataclass
class ActiveTimer:
    task: asyncio.Task
    mode: str
    label: str
    task_title: str
    chat_id: int
    message_id: int
    started_at: datetime
    work_seconds: int
    work_hours: float
    break_seconds: int
    break_label: str


active_timers: dict[int, ActiveTimer] = {}


def get_timer_preset(mode: str) -> TimerPreset:
    if mode == "pomodoro":
        return TimerPreset(
            mode="pomodoro",
            label="Pomodoro",
            work_seconds=5 if TEST_MODE else 25 * 60,
            work_hours=25 / 60,
            break_seconds=3 if TEST_MODE else 5 * 60,
            break_label="short break",
        )

    return TimerPreset(
        mode="deep",
        label="Deep Work",
        work_seconds=10 if TEST_MODE else 4 * 3600,
        work_hours=4.0,
        break_seconds=5 if TEST_MODE else 3600,
        break_label="recovery break",
    )


def build_stop_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Stop timer", callback_data=f"stop_timer:{user_id}")]
        ]
    )


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(max(seconds, 0), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def build_task_selection_text(tasks: list[tuple[int, str, str]], mode: str) -> str:
    lines = [f"<b>Pending tasks for {escape(mode)}</b>"]
    for task_id, title, _ in tasks:
        lines.append(f"{task_id}. {escape(title)}")
    lines.append("")
    lines.append("Send the task ID or use /start_timer <id>.")
    return "\n".join(lines)


async def start_timer_for_task(message: Message, task_id: int, state: FSMContext) -> None:
    user_id = message.from_user.id
    if user_id in active_timers:
        await message.reply("You already have an active timer. Use /stop_timer first.")
        return

    task = get_task(user_id, task_id)
    if task is None or task[2] == "done":
        await message.reply("Task not found or already done. Use /today to refresh the list.")
        return

    preset = get_timer_preset(get_user_mode(user_id))
    task_title = task[1]

    sent = await message.reply(
        (
            f"<b>{preset.label}</b> started for task: <b>{escape(task_title)}</b>\n"
            f"Time left: <code>{format_duration(preset.work_seconds)}</code>"
        ),
        parse_mode="HTML",
        reply_markup=build_stop_keyboard(user_id),
    )

    started_at = datetime.now()
    timer_task = asyncio.create_task(
        run_timer(
            bot=message.bot,
            user_id=user_id,
            chat_id=sent.chat.id,
            message_id=sent.message_id,
            task_title=task_title,
            preset=preset,
        )
    )
    active_timers[user_id] = ActiveTimer(
        task=timer_task,
        mode=preset.mode,
        label=preset.label,
        task_title=task_title,
        chat_id=sent.chat.id,
        message_id=sent.message_id,
        started_at=started_at,
        work_seconds=preset.work_seconds,
        work_hours=preset.work_hours,
        break_seconds=preset.break_seconds,
        break_label=preset.break_label,
    )
    await state.clear()


async def update_timer_message(bot, timer: ActiveTimer, remaining: int, user_id: int) -> None:
    try:
        await bot.edit_message_text(
            chat_id=timer.chat_id,
            message_id=timer.message_id,
            text=(
                f"<b>{timer.label}</b> in progress for task: <b>{escape(timer.task_title)}</b>\n"
                f"Time left: <code>{format_duration(remaining)}</code>"
            ),
            parse_mode="HTML",
            reply_markup=build_stop_keyboard(user_id),
        )
    except Exception:
        logger.exception("Failed to update timer message for user %s", user_id)


async def run_timer(bot, user_id: int, chat_id: int, message_id: int, task_title: str, preset: TimerPreset) -> None:
    deadline = datetime.now() + timedelta(seconds=preset.work_seconds)
    update_step = 1 if TEST_MODE else 60

    try:
        while True:
            remaining = int((deadline - datetime.now()).total_seconds())
            if remaining <= 0:
                break

            await asyncio.sleep(min(update_step, remaining))
            remaining = int((deadline - datetime.now()).total_seconds())
            timer = active_timers.get(user_id)
            if timer is None:
                return
            await update_timer_message(bot, timer, remaining, user_id)

        log_focus_session(
            user_id=user_id,
            task_title=task_title,
            hours=preset.work_hours,
            comment=f"{preset.label} completed",
        )
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"<b>{preset.label}</b> completed for task: <b>{escape(task_title)}</b>\n"
                f"Logged focus time: <b>{preset.work_hours:.2f} h</b>\n"
                f"Recommended next step: {preset.break_label} for {format_duration(preset.break_seconds)}"
            ),
            parse_mode="HTML",
        )
    except asyncio.CancelledError:
        logger.info("Timer cancelled for user %s", user_id)
        raise
    finally:
        active_timers.pop(user_id, None)


async def stop_active_timer(user_id: int) -> tuple[ActiveTimer, float] | None:
    timer = active_timers.get(user_id)
    if timer is None:
        return None

    timer.task.cancel()
    elapsed_seconds = max(0, int((datetime.now() - timer.started_at).total_seconds()))
    completed_ratio = min(1.0, elapsed_seconds / timer.work_seconds) if timer.work_seconds else 0.0
    spent_hours = timer.work_hours * completed_ratio

    log_focus_session(
        user_id=user_id,
        task_title=timer.task_title,
        hours=spent_hours,
        comment=f"{timer.label} interrupted",
    )
    active_timers.pop(user_id, None)
    return timer, spent_hours


@router.message(Command("today"))
async def cmd_today(message: Message, state: FSMContext) -> None:
    tasks = list_tasks(message.from_user.id, include_done=False)
    if not tasks:
        await message.reply("You have no pending tasks.")
        return

    mode = get_timer_preset(get_user_mode(message.from_user.id)).label
    await state.set_state(FocusState.waiting_for_task_id)
    await message.reply(build_task_selection_text(tasks, mode), parse_mode="HTML")


@router.message(Command("start_timer"))
async def cmd_start_timer(message: Message, state: FSMContext) -> None:
    arg = message.text.partition(" ")[2].strip()
    if not arg:
        await cmd_today(message, state)
        return

    if not arg.isdigit():
        await message.reply("Usage: /start_timer <task_id>")
        return

    await start_timer_for_task(message, int(arg), state)


@router.message(Command("stop_timer"))
async def cmd_stop_timer_message(message: Message, state: FSMContext) -> None:
    stopped = await stop_active_timer(message.from_user.id)
    await state.clear()
    if stopped is None:
        await message.reply("You do not have an active timer.")
        return

    timer, spent_hours = stopped
    await message.reply(
        (
            f"<b>{timer.label}</b> stopped.\n"
            f"Task: <b>{escape(timer.task_title)}</b>\n"
            f"Logged focus time: <b>{spent_hours:.2f} h</b>"
        ),
        parse_mode="HTML",
    )


@router.message(FocusState.waiting_for_task_id, F.text.regexp(r"^\d+$"))
async def start_timer_from_state(message: Message, state: FSMContext) -> None:
    await start_timer_for_task(message, int(message.text), state)


@router.callback_query(F.data.startswith("stop_timer:"))
async def cmd_stop_timer_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        _, user_id_text = callback.data.split(":")
        timer_owner_id = int(user_id_text)
    except ValueError:
        await callback.answer()
        return

    if callback.from_user.id != timer_owner_id:
        await callback.answer("This timer belongs to another user.", show_alert=True)
        return

    stopped = await stop_active_timer(timer_owner_id)
    await state.clear()
    if stopped is None:
        await callback.answer("There is no active timer.", show_alert=True)
        return

    timer, spent_hours = stopped
    await callback.message.reply(
        (
            f"<b>{timer.label}</b> stopped.\n"
            f"Task: <b>{escape(timer.task_title)}</b>\n"
            f"Logged focus time: <b>{spent_hours:.2f} h</b>"
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("report"))
async def cmd_report(message: Message) -> None:
    today = datetime.now().date().isoformat()
    focus_hours = get_today_focus_time(message.from_user.id, today)
    daily_norm = get_daily_norm(message.from_user.id)

    lines = [f"Today's focus time: <b>{focus_hours:.2f} h</b>"]

    if daily_norm is None:
        lines.append("Daily norm is not set. Use /setnorm <hours>.")
    else:
        remaining = daily_norm - focus_hours
        if remaining > 0:
            lines.append(f"Remaining to norm: <b>{remaining:.2f} h</b>")
        else:
            lines.append("Daily norm achieved.")

    await message.reply("\n".join(lines), parse_mode="HTML")

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup


router = Router()

MAIN_MENU_BUTTON = "Back to main menu"


class MenuState(StatesGroup):
    choosing_section = State()
    planning = State()
    learning = State()
    events = State()


def build_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Plan")],
            [KeyboardButton(text="Focus")],
            [KeyboardButton(text="Events")],
        ],
        resize_keyboard=True,
    )


def build_section_menu(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text) for text in row] for row in rows],
        resize_keyboard=True,
    )


@router.message(Command("start", "help"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MenuState.choosing_section)
    await message.answer(
        (
            "Choose a section:\n\n"
            "Plan -> tasks and daily queue\n"
            "Focus -> timers, report, work mode\n"
            "Events -> schedule and important dates"
        ),
        reply_markup=build_main_menu(),
    )


@router.message(MenuState.choosing_section)
async def choose_section(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().lower()

    if text == "plan":
        await state.set_state(MenuState.planning)
        await message.answer(
            (
                "Planning section\n\n"
                "/add <text> -> add a task\n"
                "/list -> show all tasks\n"
                "/today -> show pending tasks for focus\n"
                "/done <id> -> mark task as done\n"
                "/archive -> show archive summary"
            ),
            reply_markup=build_section_menu(
                [
                    ["/add", "/list"],
                    ["/today", "/done"],
                    ["/archive", MAIN_MENU_BUTTON],
                ]
            ),
        )
        return

    if text == "focus":
        await state.set_state(MenuState.learning)
        await message.answer(
            (
                "Focus section\n\n"
                "/start_timer [task_id] -> start a timer\n"
                "/stop_timer -> stop current timer\n"
                "/report -> today's focus report\n"
                "/setnorm <hours> -> set daily focus norm\n"
                "/settings -> current settings\n"
                "/setmode <deep|pomodoro> -> switch mode"
            ),
            reply_markup=build_section_menu(
                [
                    ["/start_timer", "/stop_timer"],
                    ["/report", "/setnorm"],
                    ["/settings", "/setmode"],
                    [MAIN_MENU_BUTTON],
                ]
            ),
        )
        return

    if text == "events":
        await state.set_state(MenuState.events)
        await message.answer(
            (
                "Events section\n\n"
                "/add_event <date> [time] <title> | <description>\n"
                "/schedule -> today and tomorrow\n"
                "/my_events -> upcoming events\n"
                "/delete_event <id> -> delete an event"
            ),
            reply_markup=build_section_menu(
                [
                    ["/add_event", "/schedule"],
                    ["/my_events", "/delete_event"],
                    [MAIN_MENU_BUTTON],
                ]
            ),
        )
        return

    await message.reply("Use the keyboard buttons to pick a section.")


@router.message(MenuState.planning)
@router.message(MenuState.learning)
@router.message(MenuState.events)
async def back_to_main(message: Message, state: FSMContext) -> None:
    if (message.text or "").strip() == MAIN_MENU_BUTTON:
        await cmd_start(message, state)

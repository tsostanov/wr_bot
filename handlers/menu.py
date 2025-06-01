from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# FSM-состояния


class MenuState(StatesGroup):
    CHOOSING_SECTION = State()
    PLANNING = State()
    LEARNING = State()
    EVENTS = State()

# === Главное меню ===


@router.message(Command('start', 'help'))
async def cmd_start(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📋 Планировать')],
            [KeyboardButton(text='📖 Учиться')],
            [KeyboardButton(text='🗓️ События')],
        ],
        resize_keyboard=True
    )
    await state.clear()
    await state.set_state(MenuState.CHOOSING_SECTION)
    text = (
        "👋 Привет! Выбери раздел:\n\n"
        "📋 Планировать — задачи и дедлайны\n"
        "📖 Учиться — Deep Work / Pomodoro / отчёты\n"
        "🗓️ События — расписание и важные даты"
    )
    await message.answer(text, reply_markup=kb)

# === Выбор раздела ===


@router.message(MenuState.CHOOSING_SECTION)
async def choose_section(message: Message, state: FSMContext):
    text = message.text.strip().lower()

    if text == '📋 планировать':
        await state.set_state(MenuState.PLANNING)
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='/add'), KeyboardButton(text='/list')],
                [KeyboardButton(text='/today'), KeyboardButton(text='/done')],
                [KeyboardButton(text='◀️ Главное меню')]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "<b>📋 Раздел «Планировать»</b>\n\n"
            "/add — добавить задачу\n"
            "/list — показать все задачи\n"
            "/today — задачи на сегодня\n"
            "/done — отметить задачу выполненной",
            reply_markup=kb,
            parse_mode='HTML'
        )
        return

    if text == '📖 учиться':
        await state.set_state(MenuState.LEARNING)
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='/setnorm'),
                 KeyboardButton(text='/report')],
                [KeyboardButton(text='/start_timer'),
                 KeyboardButton(text='/stop_timer')],
                [KeyboardButton(text='◀️ Главное меню')]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "<b>📖 Раздел «Учиться»</b>\n\n"
            "/setnorm — задать норму работы в день\n"
            "/report — показать отчёт по Deep Work сегодня\n"
            "/start_timer — запустить Deep Work / Pomodoro\n"
            "/stop_timer — остановить текущий таймер",
            reply_markup=kb,
            parse_mode='HTML'
        )
        return

    if text == '🗓️ события':
        await state.set_state(MenuState.EVENTS)
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='/add_event'),
                 KeyboardButton(text='/schedule')],
                [KeyboardButton(text='/my_events'),
                 KeyboardButton(text='/delete_event')],
                [KeyboardButton(text='◀️ Главное меню')]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "<b>🗓️ Раздел «События»</b>\n\n"
            "/add_event — добавить событие\n"
            "/schedule — показать расписание на сегодня и завтра\n"
            "/my_events — показать все будущие события\n"
            "/delete_event — удалить событие по ID",
            reply_markup=kb,
            parse_mode='HTML'
        )
        return

    # Если пользователь нажал что-то не из кнопок
    await message.reply("⚠️ Пожалуйста, выбери один из разделов, используя кнопки ниже.")

# === Возврат в главное меню ===


@router.message(lambda message: not message.text.startswith('/'), MenuState.PLANNING)
@router.message(lambda message: not message.text.startswith('/'), MenuState.LEARNING)
@router.message(lambda message: not message.text.startswith('/'), MenuState.EVENTS)
async def back_to_main(message: Message, state: FSMContext):
    if message.text.strip() == '◀️ Главное меню':
        await cmd_start(message, state)

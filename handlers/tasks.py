from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import add_task, list_tasks, complete_task, add_archive
from datetime import datetime

router = Router()


@router.message(Command(commands=['add']))
async def cmd_add(message: Message):
    args = message.text.partition(' ')[2].strip()
    if not args:
        return await message.reply('✏️ Пожалуйста, укажи текст задачи после /add')
    task_id = add_task(message.from_user.id, args)
    await message.reply(f'✅ Задача #{task_id} добавлена: {args}')


@router.message(Command(commands=['list']))
async def cmd_list(message: Message):
    tasks = list_tasks(message.from_user.id)
    if not tasks:
        return await message.reply('📋 У тебя нет задач.')
    text = '📋 Твои задачи:\n'
    for tid, title, status in tasks:
        mark = '✅' if status == 'done' else '❌'
        text += f'{tid}. {mark} {title}\n'
    await message.reply(text)


@router.message(Command(commands=['today']))
async def cmd_today(message: Message):
    tasks = list_tasks(message.from_user.id, include_done=False)
    if not tasks:
        return await message.reply('📅 Сегодня у тебя нет активных задач.')
    text = '📅 Задачи на сегодня:\n'
    for tid, title, _ in tasks:
        text += f'{tid}. {title}\n'
    text += '\nВыбери ID задачи, чтобы запустить Deep Work (4 ч):'
    await message.reply(text)


@router.message(Command(commands=['done']))
async def cmd_done(message: Message):
    arg = message.text.partition(' ')[2].strip()
    if not arg.isdigit():
        return await message.reply('⚠️ Укажи номер задачи: /done 2')
    tid = int(arg)
    tasks = list_tasks(message.from_user.id)
    title = next((t for id_, t, s in tasks if id_ == tid), f'Задача #{tid}')
    if complete_task(message.from_user.id, tid):
        # Добавляем в архив побед
        date_str = datetime.now().strftime('%Y-%m-%d')
        add_archive(message.from_user.id, 'task', title,
                    date_str, '', 'Выполнено и заархивировано')
        await message.reply(f'✅ Задача #{tid} "{title}" отмечена как выполненная и добавлена в архив.')
    else:
        await message.reply(f'❌ Задача #{tid} не найдена.')

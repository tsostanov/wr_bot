# White Room Bot

Telegram bot for focus sessions, task tracking, and personal scheduling.

## Features

- Task list with completion archive
- Deep Work and Pomodoro modes
- Daily focus norm and daily report
- Personal event schedule
- SQLite storage

## Main Commands

- `/start` - open the main menu
- `/add <text>` - add a task
- `/list` - show all tasks
- `/done <id>` - mark task as done
- `/today` - show pending tasks and pick one for focus
- `/start_timer [id]` - start a timer for a task
- `/stop_timer` - stop the active timer
- `/report` - show today's focus report
- `/setnorm <hours>` - set daily focus norm
- `/settings` - show current settings
- `/setmode <deep|pomodoro>` - switch focus mode
- `/add_event <date> [time] <title> | <description>` - create an event
- `/schedule` - show today and tomorrow
- `/my_events` - show upcoming events
- `/delete_event <id>` - delete an event
- `/archive` - show archive summary

## Setup

```bash
git clone https://github.com/tsostanov/wr_bot.git
cd wr_bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

## Environment Variables

- `BOT_TOKEN` - required Telegram bot token
- `DB_PATH` - optional SQLite path, default `database.db`
- `DEFAULT_TIME_ZONE` - optional default time zone, default `Europe/Moscow`
- `TEST_MODE` - optional `true/false` flag for short timers
- `LOG_LEVEL` - optional logging level, default `INFO`

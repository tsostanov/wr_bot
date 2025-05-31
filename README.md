# 🧠 White Room Bot

Telegram bot for deep work sessions, time tracking, and productivity rituals.

## Features

- 🕓 Deep Work / Pomodoro focus timers
- ✅ Daily work norms and progress tracking
- 💾 SQLite (PostgreSQL)
- 📈 Logging sessions with time spent
- 🔧 Global settings via commands

## Commands

| Command       | Description                      |
|---------------|----------------------------------|
| `/start`      | Start interaction                |
| `/today`      | Choose task and start timer      |
|               |                                  |
| `/settings`   | View or update bot config        |
...

## Setup

```bash
# (for Windows)
git clone https://github.com/tsostanov/wr_bot.git
cd wr_bot
python -m venv venv
\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
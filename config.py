import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


def _read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is required.")
    return value


def _read_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


BOT_TOKEN = _read_required_env("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "database.db")
DEFAULT_TIME_ZONE = os.getenv("DEFAULT_TIME_ZONE", "Europe/Moscow")
TEST_MODE = _read_bool_env("TEST_MODE", default=False)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

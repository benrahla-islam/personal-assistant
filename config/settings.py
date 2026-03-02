"""
Centralized configuration validation and settings.

Validates required environment variables at startup (fail-fast)
and exports typed settings for the rest of the application.
"""

import os
import sys
from typing import FrozenSet, Optional

import dotenv

dotenv.load_dotenv()


# ---------------------------------------------------------------------------
# Required / optional environment variables
# ---------------------------------------------------------------------------
_REQUIRED_VARS = {
    "GOOGLE_API_KEY": "Gemini API key (get one at https://aistudio.google.com/apikey)",
    "TELEGRAM_BOT_TOKEN": "Telegram bot token (get one from @BotFather)",
}

_OPTIONAL_VARS = {
    "GOOGLE_API_KEY_AGENTS": "Secondary Gemini API key for specialized agents",
    "TODOIST_API_TOKEN": "Todoist API token for task management integration",
    "TELEGRAM_API_ID": "Telegram API ID for Telethon scraper",
    "TELEGRAM_API_HASH": "Telegram API hash for Telethon scraper",
    "LLM_MODEL": "LLM model to use (default: gemini-2.5-flash)",
    "MEMORY_PRUNE_THRESHOLD": "Number of messages before pruning history (default: 20)",
}


def validate_environment() -> list[str]:
    """
    Check that all required environment variables are set.

    Returns a list of error messages (empty = all good).
    Prints warnings for missing optional variables.
    """
    errors: list[str] = []

    for var, description in _REQUIRED_VARS.items():
        if not os.getenv(var):
            errors.append(f"  ✗ {var} — {description}")

    for var, description in _OPTIONAL_VARS.items():
        if not os.getenv(var):
            print(f"  ⚠ Optional: {var} not set — {description}")

    return errors


def require_environment() -> None:
    """
    Validate environment and exit with a clear message if anything is missing.

    Call this once at application startup (before building the bot).
    """
    errors = validate_environment()
    if errors:
        print("\n❌ Missing required environment variables:\n")
        for err in errors:
            print(err)
        print(
            "\nCreate a .env file (see .env.example) or export the variables "
            "before starting the bot.\n"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Security: Telegram user allow-list
# ---------------------------------------------------------------------------
def _parse_allowed_users() -> FrozenSet[int]:
    """
    Parse ALLOWED_USER_IDS from environment.

    Format: comma-separated Telegram user IDs, e.g. "123456,789012"
    If empty or unset, returns an empty frozenset (all users allowed).
    """
    raw = os.getenv("ALLOWED_USER_IDS", "").strip()
    if not raw:
        return frozenset()
    try:
        return frozenset(int(uid.strip()) for uid in raw.split(",") if uid.strip())
    except ValueError as exc:
        print(f"⚠ ALLOWED_USER_IDS contains non-integer value: {exc}")
        return frozenset()


ALLOWED_USER_IDS: FrozenSet[int] = _parse_allowed_users()


def is_user_allowed(user_id: int) -> bool:
    """
    Check whether a Telegram user is allowed to interact with the bot.

    If ALLOWED_USER_IDS is empty, everyone is allowed (open mode).
    """
    if not ALLOWED_USER_IDS:
        return True  # open mode — no allowlist configured
    return user_id in ALLOWED_USER_IDS


# ---------------------------------------------------------------------------
# Rate-limit settings (re-exported for convenience)
# ---------------------------------------------------------------------------
RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "4.0"))
RATE_LIMIT_MAX_RPM: int = int(os.getenv("RATE_LIMIT_MAX_RPM", "15"))
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
MEMORY_PRUNE_THRESHOLD: int = int(os.getenv("MEMORY_PRUNE_THRESHOLD", "20"))

"""
Message templates and keyboard builders for the Synology API Telegram Bot.
"""
from typing import Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from . import general_functions as gn


# ---------------------------------------------------------------------------
# Text messages
# ---------------------------------------------------------------------------

WELCOME_MESSAGE = (
    "🖥 <b>Synology API Telegram Bot</b>\n\n"
    "Interact with your Synology NAS via Telegram.\n"
    "Powered by <a href='https://github.com/N4S4/synology-api'>synology-api</a>\n\n"
    "<b>Getting started:</b>\n"
    "1. Configure your NAS connection below\n"
    "2. Click <b>Finish Configuration</b> when done\n"
    "3. Select a module, then <b>login</b>\n"
    "4. Choose a function to execute\n\n"
    "Use /help for command list."
)

CONFIG_BACK_MESSAGE = (
    "Back to configuration.\n"
    "What would you like to change?\n\n"
    "Press <b>Finish Configuration</b> when done."
)

FINISH_CONFIG_MESSAGE = (
    "Configuration complete! You can change it anytime.\n"
    "Select a module below:"
)


def modules_header() -> str:
    return f"Available modules ({len(gn.SYNO_MODULES)}):"


def functions_header(module_name: str) -> str:
    funcs = gn.get_syno_functions(module_name)
    desc = gn.MODULE_DESCRIPTIONS.get(module_name, "")
    return (
        f"<b>{module_name}</b>"
        + (f" — {desc}" if desc else "")
        + f"\nFunctions available: {len(funcs)}\n"
        "Use <b>login</b> first, then pick a function."
    )


HELP_MESSAGE = (
    "<b>Available Commands:</b>\n"
    "/start — Show main menu\n"
    "/help — Show this help\n"
    "/status — Show connection status\n"
    "/cancel — Cancel current operation\n\n"
    "<b>Workflow:</b>\n"
    "1. Configure NAS → Finish Configuration\n"
    "2. Pick a module → Login\n"
    "3. Choose a function → Provide args if needed\n"
    "4. Results are displayed as JSON\n\n"
    "<b>FileStation:</b>\n"
    "Select 'filestation' for a visual file browser with\n"
    "folder navigation, file search, and download.\n\n"
    "<b>Security:</b>\n"
    "Password can be set via <code>SYNOLOGY_PASSWORD</code> env var.\n"
    "Token via <code>TELEGRAM_TOKEN</code> env var."
)


# ---------------------------------------------------------------------------
# Keyboard builders
# ---------------------------------------------------------------------------

def _build_keyboard(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    """Build a ReplyKeyboardMarkup from a list of rows of button labels."""
    keyboard = []
    for row in rows:
        keyboard.append([KeyboardButton(text=label) for label in row])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def start_keyboard() -> ReplyKeyboardMarkup:
    items = gn.CONFIG_KEYS + ["Finish Configuration"]
    rows = [items[i:i + 2] for i in range(0, len(items), 2)]
    return _build_keyboard(rows)


def modules_keyboard() -> ReplyKeyboardMarkup:
    rows = [["Back to Configuration"]]
    mods = gn.SYNO_MODULES
    for i in range(0, len(mods), 2):
        rows.append(mods[i:i + 2])
    return _build_keyboard(rows)


def functions_keyboard(module_name: str) -> ReplyKeyboardMarkup:
    rows = [["login", "Back to Modules"]]
    funcs = gn.get_syno_functions(module_name)
    for i in range(0, len(funcs), 2):
        rows.append(funcs[i:i + 2])
    return _build_keyboard(rows)


# ---------------------------------------------------------------------------
# File Browser keyboards
# ---------------------------------------------------------------------------

def file_browser_menu() -> ReplyKeyboardMarkup:
    """Main FileStation menu with Browse/Search/Download."""
    return _build_keyboard([
        ["📂 Browse Files", "🔍 Search Files"],
        ["📋 All Functions"],
        ["Back to Modules"],
    ])


def file_browser_search_path_keyboard() -> ReplyKeyboardMarkup:
    """Quick-select paths for search."""
    return _build_keyboard([
        ["🏠 /home", "/volume1"],
        ["⬅ File Browser Menu"],
    ])


def file_browser_file_options() -> ReplyKeyboardMarkup:
    """Options when a file is selected."""
    return _build_keyboard([
        ["📥 Download", "ℹ️ File Info"],
        ["⬆ Back", "⬅ File Browser Menu"],
    ])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Cancel", callback_data="cancel_op")]
    ])

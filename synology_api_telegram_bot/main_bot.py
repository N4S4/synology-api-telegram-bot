"""
Synology API Telegram Bot -- Main entry point.

A Telegram bot that lets you control your Synology NAS
through the synology-api library, using aiogram 3.x.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile, Message

# Add parent to path for development
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from synology_api_telegram_bot import file_browser as fb
from synology_api_telegram_bot import general_functions as gn
from synology_api_telegram_bot import messages as msg
from synology_api_telegram_bot import syno_functions as sf

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("syno_bot")

# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------
# === EDIT THESE VALUES ===
# Replace with your real token from @BotFather and your Telegram user ID(s).
# Env vars (TELEGRAM_TOKEN, ALLOWED_USERS) take priority if set.
_HARDCODED_TOKEN = "YOUR_BOT_TOKEN_HERE"
_HARDCODED_USERS = "159718277"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", _HARDCODED_TOKEN)

# Parse allowed users (comma-separated Telegram user IDs)
_raw_ids = os.environ.get("ALLOWED_USERS", _HARDCODED_USERS)
ALLOWED_USERS: set[int] = set()
if _raw_ids:
    try:
        ALLOWED_USERS = {int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip()}
    except ValueError:
        logger.error("ALLOWED_USERS contains invalid IDs. Bot will refuse all connections.")

bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


# ---------------------------------------------------------------------------
# Access control middleware
# ---------------------------------------------------------------------------

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update


class AccessControlMiddleware(BaseMiddleware):
    """Block messages from users not in the ALLOWED_USERS set."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Extract user ID from the event
        user_id: int | None = None
        chat_id: int | None = None

        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, Update) and event.message:
            user_id = event.message.from_user.id
            chat_id = event.message.chat.id
        elif isinstance(event, Update) and event.callback_query:
            user_id = event.callback_query.from_user.id

        if user_id is None:
            return

        if not ALLOWED_USERS:
            logger.warning("Blocked user %s: ALLOWED_USERS not configured", user_id)
            return

        if user_id not in ALLOWED_USERS:
            logger.warning("Blocked unauthorized user %s", user_id)
            # Send the "intruder alert" message exactly once per chat
            bot_instance: Bot = data.get("bot")  # type: ignore[assignment]
            if bot_instance and chat_id:
                await bot_instance.send_message(
                    chat_id,
                    "[!] <b>User not recognized.</b>\n\n"
                    "OUT OF MY STUFF!\n"
                    "Device auto-destruction <b>ACTIVATED!</b>\n\n"
                    "Your device CPU will burn in <b>1 minute</b>.",
                )
            return

        return await handler(event, data)


# Apply middleware
dp.update.middleware(AccessControlMiddleware())


# ---------------------------------------------------------------------------
# FSM keys
# ---------------------------------------------------------------------------
class BotState:
    MODULE = "module"
    LOGGED_IN = "logged_in"
    COLLECTING_ARGS = "collecting_args"
    CURRENT_FUNC = "current_func"
    ARGS_LIST = "args_list"
    ARG_INDEX = "arg_index"
    ARGS_DICT = "args_dict"
    CONFIG_KEY = "config_key"
    # File browser state
    FB_MODE = "fb_mode"
    FB_PATH = "fb_path"
    FB_OFFSET = "fb_offset"
    FB_SELECTED = "fb_selected"
    FB_SEARCH_RESULTS = "fb_search_results"


# File browser mode constants
FB_MENU = "menu"
FB_BROWSE = "browse"
FB_SEARCH_PATH = "search_path"
FB_SEARCH_TERM = "search_term"
FB_FILE_SELECTED = "file_selected"


# File browser button prefixes (used for F.text matching)
FILE_BROWSER_BUTTONS = [
    "Browse Files",
    "Search Files",
    "All Functions",
    "File Browser Menu",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk_text(text: str, size: int = 4000) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


async def _send_long_message(message: Message, text: str) -> None:
    for chunk in _chunk_text(text):
        await message.answer(chunk)


def _format_result(data) -> str:
    if isinstance(data, dict) and "error" in data:
        return f"{data['error']}"
    if isinstance(data, dict) and data.get("requires_args"):
        return f"{data.get('message', 'Arguments required')}"
    try:
        formatted = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        return f"<pre>{formatted}</pre>"
    except Exception:
        return str(data)


async def _reset_args_state(state: FSMContext) -> None:
    await state.update_data(
        collecting_args=False,
        current_func=None,
        args_list=[],
        arg_index=0,
        args_dict={},
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    logger.info("/start from user %s", message.from_user.id)
    gn.ensure_config_file()
    await state.clear()
    await message.answer(msg.WELCOME_MESSAGE, reply_markup=msg.start_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(msg.HELP_MESSAGE)


@router.message(Command("status"))
async def cmd_status(message: Message):
    info = sf.get_session_info()
    conf = gn.get_data_from_db()
    errors = gn.validate_config(conf)
    lines = ["<b>Status</b>"]
    if info["logged_in"]:
        lines.append(f"Logged in -- Module: <code>{info['module']}</code>")
        lines.append(f"Session: <code>{info['sid']}</code>")
    else:
        lines.append("Not logged in")
    lines.append(f"\n<b>Config:</b> NAS: <code>{conf.get('ip_address', '?')}:{conf.get('port', '?')}</code>")
    lines.append(f"User: <code>{conf.get('username', '?')}</code>")
    lines.append(f"DSM: <code>{conf.get('dsm_version', '?')}</code>")
    if errors:
        lines.append(f"\nConfig issues: {', '.join(errors)}")
    else:
        lines.append("Config looks valid")
    await message.answer("\n".join(lines))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_data()
    fb_mode = current.get("fb_mode")
    if fb_mode:
        fb.logout_session()
        await state.clear()
        await message.answer("File browser cancelled.", reply_markup=msg.modules_keyboard())
        return
    if current.get("collecting_args"):
        await _reset_args_state(state)
        await message.answer("Argument collection cancelled.")
    elif current.get("config_key"):
        await state.update_data(config_key=None)
        await message.answer("Config input cancelled.")
    else:
        await message.answer("Nothing to cancel.")
    await state.set_state(None)


# ---------------------------------------------------------------------------
# Configuration flow
# ---------------------------------------------------------------------------

@router.message(F.text == "Back to Configuration")
async def back_to_config(message: Message, state: FSMContext):
    logger.info("Back to Configuration")
    await state.clear()
    await message.answer(msg.CONFIG_BACK_MESSAGE, reply_markup=msg.start_keyboard())


@router.message(F.text.in_(gn.CONFIG_KEYS))
async def config_key_selected(message: Message, state: FSMContext):
    key = message.text
    await state.update_data(config_key=key)
    hints = {
        "ip_address": "e.g., 192.168.1.2",
        "port": "e.g., 5001",
        "username": "Your NAS username",
        "password": "Your NAS password (or set SYNOLOGY_PASSWORD env var)",
        "secure": "True or False (HTTPS?)",
        "cert_verify": "True or False (verify SSL cert?)",
        "dsm_version": "6 or 7",
        "debug": "True or False",
        "otp_code": "OTP code if 2FA enabled (or leave empty)",
    }
    hint = hints.get(key, "")
    await message.reply(f"Send your <b>{key}</b>\n{hint}")


@router.message(F.text == "Finish Configuration")
async def finish_configuration(message: Message, state: FSMContext):
    await state.clear()
    conf = gn.get_data_from_db()
    errors = gn.validate_config(conf)
    if errors:
        await message.answer(
            f"<b>Config warnings:</b>\n" + "\n".join(f"* {e}" for e in errors),
        )
    await message.answer(msg.FINISH_CONFIG_MESSAGE, reply_markup=msg.modules_keyboard())


# ---------------------------------------------------------------------------
# Module selection
# ---------------------------------------------------------------------------

@router.message(F.text.in_(["Back to Modules", "modules"]))
async def show_modules(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("logged_in"):
        sf.logout()
    fb.logout_session()
    await state.clear()
    await message.answer(msg.modules_header(), reply_markup=msg.modules_keyboard())


@router.message(F.text == "filestation")
async def filestation_menu(message: Message, state: FSMContext):
    """Show the FileStation special menu instead of raw functions."""
    await state.update_data(module="filestation", logged_in=False, fb_mode=FB_MENU)
    await _reset_args_state(state)
    await message.answer(
        "<b>FileStation -- File Browser</b>\n\n"
        "Choose an action:",
        reply_markup=msg.file_browser_menu(),
    )


@router.message(F.text.in_(gn.SYNO_MODULES))
async def module_selected(message: Message, state: FSMContext):
    """User selected a module -- show its functions (skip filestation, handled above)."""
    module_name = message.text
    if module_name == "filestation":
        return  # Already handled by dedicated handler
    await state.update_data(module=module_name, logged_in=False)
    await _reset_args_state(state)
    await message.answer(
        msg.functions_header(module_name),
        reply_markup=msg.functions_keyboard(module_name),
    )


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------

@router.message(F.text == "login")
async def do_login(message: Message, state: FSMContext):
    data = await state.get_data()
    module_name = data.get("module")
    if not module_name:
        await message.answer("Select a module first.")
        return
    try:
        sess = sf.login(module_name)
        sid = getattr(sess, "_sid", "unknown")
        await state.update_data(logged_in=True)
        await message.answer(
            f"Logged in to <b>{module_name}</b>\n"
            f"Session: <code>{sid}</code>\n"
            "Now choose a function."
        )
    except Exception as e:
        logger.error("Login failed: %s", e)
        await message.answer(f"Login failed: {e}")


@router.message(F.text == "logout")
async def do_logout(message: Message, state: FSMContext):
    sf.logout()
    fb.logout_session()
    await state.update_data(logged_in=False)
    await message.answer("bye Logged out.")


# ---------------------------------------------------------------------------
# Function execution (non-filestation modules)
# ---------------------------------------------------------------------------

@router.message(F.text.in_(gn.flat_function_list()))
async def function_selected(message: Message, state: FSMContext):
    data = await state.get_data()
    module_name = data.get("module")
    if not module_name:
        await message.answer("Select a module first.")
        return
    if not data.get("logged_in"):
        await message.answer("Use <b>login</b> first.")
        return

    func_name = message.text
    requires, args_list, msg_text = gn.check_if_require_arguments(module_name, func_name)

    if requires:
        await state.update_data(
            collecting_args=True,
            current_func=func_name,
            args_list=args_list,
            arg_index=0,
            args_dict={},
        )
        await message.answer(f"{msg_text}\n\nProvide <b>{args_list[0]}</b>:")
    else:
        result = sf.function_action(func_name, module_name=module_name)
        await _send_long_message(message, _format_result(result))



# ===========================================================================
# FILE BROWSER HANDLERS
# ===========================================================================
# --- File Browser Menu buttons ---

@router.message(F.text == "Browse Files")
async def fb_start_browse(message: Message, state: FSMContext):
    """Start browsing from the default home directory."""
    logger.info("FILE BROWSER: Browse Files clicked, launching _fb_browse")
    try:
        await _fb_browse(message, state, path=fb.DEFAULT_HOME)
    except Exception as e:
        logger.error("FILE BROWSER: _fb_browse crashed: %s", e, exc_info=True)
        await message.answer(f"Error browsing: {e}")


@router.message(F.text == "Search Files")
async def fb_start_search(message: Message, state: FSMContext):
    """Start file search flow -- ask for path."""
    logger.info("FILE BROWSER: Search Files clicked")
    await state.update_data(fb_mode=FB_SEARCH_PATH)
    await message.answer(
        "<b>Search Files</b>\n\n"
        "Which folder do you want to search?\n"
        "Type a path (e.g. /home) or use the buttons:",
        reply_markup=msg.file_browser_search_path_keyboard(),
    )


@router.message(F.text == "All Functions")
async def fb_all_functions(message: Message, state: FSMContext):
    """Show all raw FileStation functions."""
    logger.info("FILE BROWSER: All Functions clicked")
    await state.update_data(fb_mode=None, logged_in=False)
    await message.answer(
        msg.functions_header("filestation"),
        reply_markup=msg.functions_keyboard("filestation"),
    )


@router.message(F.text == "File Browser Menu")
async def fb_back_to_menu(message: Message, state: FSMContext):
    """Return to the file browser main menu."""
    await state.update_data(fb_mode=FB_MENU)
    await message.answer(
        "<b>FileStation -- File Browser</b>\nChoose an action:",
        reply_markup=msg.file_browser_menu(),
    )


# --- Folder navigation ---

@router.message(F.text.startswith("[D]"))
async def fb_navigate_folder(message: Message, state: FSMContext):
    """Navigate into a subfolder."""
    data = await state.get_data()
    fb_mode = data.get("fb_mode")
    if fb_mode != FB_BROWSE:
        return

    folder_name = message.text[4:].strip()  # Remove "[D] " prefix
    current_path = data.get("fb_path", fb.DEFAULT_HOME)
    new_path = f"{current_path.rstrip('/')}/{folder_name}"
    await _fb_browse(message, state, path=new_path)


@router.message(F.text == "Back")
async def fb_go_back(message: Message, state: FSMContext):
    """Go to parent directory."""
    data = await state.get_data()
    fb_mode = data.get("fb_mode")
    if fb_mode not in (FB_BROWSE, FB_FILE_SELECTED):
        return

    current_path = data.get("fb_path", fb.DEFAULT_HOME)
    parent = str(Path(current_path).parent)
    if not parent or parent == "/":
        parent = "/"
    await _fb_browse(message, state, path=parent)


@router.message(F.text == "Home")
async def fb_go_home(message: Message, state: FSMContext):
    """Go to home directory."""
    data = await state.get_data()
    fb_mode = data.get("fb_mode")
    if fb_mode not in (FB_BROWSE, FB_FILE_SELECTED):
        return
    await _fb_browse(message, state, path=fb.DEFAULT_HOME)


# --- File selection and download ---

@router.message(F.text.startswith("[F]"))
async def fb_file_selected(message: Message, state: FSMContext):
    """User tapped a file -- show file options."""
    data = await state.get_data()
    fb_mode = data.get("fb_mode")
    if fb_mode not in (FB_BROWSE, FB_FILE_SELECTED):
        return

    file_name = message.text[4:].strip()  # Remove "[F] " prefix
    current_path = data.get("fb_path", "")
    file_path = f"{current_path.rstrip('/')}/{file_name}"

    await state.update_data(
        fb_mode=FB_FILE_SELECTED,
        fb_selected=file_path,
    )

    # Try to get file size
    size_str = ""
    items = data.get("_fb_items", [])
    for item in items:
        if item["name"] == file_name:
            size_str = f" -- {fb.format_size(item['size'])}"
            break

    await message.answer(
        f"<b>{file_name}</b>{size_str}\n"
        f"<code>{file_path}</code>",
        reply_markup=msg.file_browser_file_options(),
    )


@router.message(F.text == "Download")
async def fb_download_file(message: Message, state: FSMContext):
    """Download the selected file and send it via Telegram."""
    data = await state.get_data()
    file_path = data.get("fb_selected")
    if not file_path:
        await message.answer("No file selected.")
        return

    file_name = Path(file_path).name
    await message.answer(f"Downloading <b>{file_name}</b>...")

    # Check file size
    info = fb.get_file_info(file_path)
    files_list = info.get("files", [])
    if files_list:
        size = files_list[0].get("additional", {}).get("size", 0)
        if size > fb.MAX_DOWNLOAD_SIZE:
            await message.answer(
                f"File too large: {fb.format_size(size)}\n"
                f"Telegram limit is {fb.format_size(fb.MAX_DOWNLOAD_SIZE)}."
            )
            return

    # Download from NAS
    local_path = fb.download_file(file_path)
    if not local_path:
        await message.answer("Download failed. Check logs.")
        return

    # Send as document
    try:
        doc = FSInputFile(local_path, filename=file_name)
        await message.answer_document(
            doc,
            caption=f"{file_name}",
        )
        logger.info("Sent file: %s", file_name)
    except Exception as e:
        logger.error("Failed to send file: %s", e)
        await message.answer(f"Failed to send: {e}")
    finally:
        # Clean up temp file
        try:
            os.remove(local_path)
            os.rmdir(os.path.dirname(local_path))
        except Exception:
            pass


@router.message(F.text == "File Info")
async def fb_file_info(message: Message, state: FSMContext):
    """Show detailed info for the selected file."""
    data = await state.get_data()
    file_path = data.get("fb_selected")
    if not file_path:
        await message.answer("No file selected.")
        return

    info = fb.get_file_info(file_path)
    files_list = info.get("files", [])
    if files_list:
        f = files_list[0]
        name = f.get("name", "?")
        add = f.get("additional", {})
        size = fb.format_size(add.get("size", 0))
        owner = add.get("owner", {}).get("name", "?")
        mtime = add.get("time", {}).get("mtime", "?")
        isdir = f.get("isdir", False)
        real_path = add.get("real_path", file_path)

        lines = [
            f"<b>{name}</b>",
            f"Path: <code>{real_path}</code>",
            f"Type: {'Folder' if isdir else 'File'}",
            f"Size: {size}",
            f"Owner: {owner}",
        ]
        if mtime:
            from datetime import datetime
            try:
                dt = datetime.fromtimestamp(mtime)
                lines.append(f"Modified: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception:
                pass

        await message.answer("\n".join(lines))
    else:
        await message.answer(f"Could not get info for:\n<code>{file_path}</code>")


# --- Search flow ---

@router.message(F.text == "/home")
async def fb_search_home(message: Message, state: FSMContext):
    """Quick-select /home for search."""
    data = await state.get_data()
    if data.get("fb_mode") != FB_SEARCH_PATH:
        return
    await state.update_data(fb_mode=FB_SEARCH_TERM, fb_path="/home")
    await message.answer("What to search? Type a pattern (e.g. <code>*.py</code>):")


@router.message(F.text == "/volume1")
async def fb_search_volume1(message: Message, state: FSMContext):
    """Quick-select /volume1 for search."""
    data = await state.get_data()
    if data.get("fb_mode") != FB_SEARCH_PATH:
        return
    await state.update_data(fb_mode=FB_SEARCH_TERM, fb_path="/volume1")
    await message.answer("What to search? Type a pattern (e.g. <code>*.py</code>):")


# ===========================================================================
# UNIFIED CATCH-ALL HANDLER
# Handles: config input, argument collection, file browser search
# Must be registered LAST so specific handlers win
# ===========================================================================

@router.message(lambda msg: True)
async def catch_all_handler(message: Message, state: FSMContext):
    """Route message to the correct handler based on current FSM state."""
    data = await state.get_data()

    # 1. Config value input
    config_key = data.get("config_key")
    if config_key:
        value = message.text.strip()
        _, _ = gn.write_single_value_to_db(config_key, value)
        await state.update_data(config_key=None)
        await message.reply(
            f"<b>{config_key}</b> = <code>{value}</code>\n"
            "Saved. Choose another key or <b>Finish Configuration</b>.",
            reply_markup=msg.start_keyboard(),
        )
        return

    # 2. Argument collection
    if data.get("collecting_args"):
        args_list = data.get("args_list", [])
        arg_index = data.get("arg_index", 0)
        args_dict = data.get("args_dict", {})
        func_name = data.get("current_func")
        module_name = data.get("module")

        arg_name = args_list[arg_index]
        args_dict[arg_name] = message.text.strip()
        arg_index += 1

        if arg_index < len(args_list):
            await state.update_data(arg_index=arg_index, args_dict=args_dict)
            await message.answer(f"Provide <b>{args_list[arg_index]}</b>:")
        else:
            await _reset_args_state(state)
            result = sf.function_action(
                func_name, dict_of_args=args_dict, module_name=module_name
            )
            await _send_long_message(message, _format_result(result))
        return

    # 3. File browser -- search path input
    fb_mode = data.get("fb_mode")
    if fb_mode == FB_SEARCH_PATH:
        path_input = message.text.strip()
        await state.update_data(fb_mode=FB_SEARCH_TERM, fb_path=path_input)
        await message.answer(f"Search in <code>{path_input}</code>. Type the pattern:")
        return

    # 4. File browser -- search term input
    if fb_mode == FB_SEARCH_TERM:
        pattern = message.text.strip()
        folder_path = data.get("fb_path", "/home")

        await message.answer(f"Searching <code>{pattern}</code> in <code>{folder_path}</code>...")

        result = fb.search_files(folder_path, pattern)
        if result.get("error"):
            await message.answer(f"{result['error']}")
            return

        items = result.get("items", [])
        if not items:
            await message.answer(f"No results for <code>{pattern}</code>")
            return

        await state.update_data(
            fb_mode=FB_BROWSE, fb_path=folder_path,
            _fb_items=items, fb_search_results=True,
        )

        lines = [
            f"<b>{len(items)} results</b> for <code>{pattern}</code> in <code>{folder_path}</code>:",
            "",
        ]
        for item in items[:20]:
            icon = "[D]" if item["isdir"] else "[F]"
            size_str = "" if item["isdir"] else f" ({fb.format_size(item['size'])})"
            lines.append(f"{icon} <b>{item['name']}</b>{size_str}")
            lines.append(f"   <code>{item['path']}</code>")

        if len(items) > 20:
            lines.append(f"\n... and {len(items) - 20} more results.")
        await message.answer("\n".join(lines))

        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{'[D]' if item['isdir'] else '[F]'} {item['name']}")]
                for item in items[:30]
            ] + [[KeyboardButton(text="File Browser Menu")]],
            resize_keyboard=True,
        )
        await message.answer("Tap a file to download, or use the menu:", reply_markup=kb)
        return

    # If nothing matched, the message is silently ignored


# ===========================================================================
# Internal helpers for file browser
# ===========================================================================

async def _fb_browse(message: Message, state: FSMContext, path: str):
    """Browse a directory and show its contents."""
    await message.answer(f"Loading <code>{path}</code>...")

    result = fb.list_directory(path)
    if result.get("error"):
        await message.answer(f"{result['error']}")
        return

    items = result.get("items", [])
    total = result.get("total", 0)
    has_more = result.get("has_more", False)

    # Build header
    header = f"<b>{path}</b>"
    if total == 0:
        header += "\n<i>Empty folder</i>"
    else:
        header += f"\n{total} items"
    if has_more:
        header += f" (showing {len(items)})"

    # Build keyboard: folders first, then files
    folders = [item for item in items if item["isdir"]]
    files_list = [item for item in items if not item["isdir"]]

    kb_rows = []
    for item in folders:
        kb_rows.append([f"[D] {item['name']}"])
    for item in files_list:
        kb_rows.append([f"[F] {item['name']}"])

    # Navigation row
    nav_row = ["Back", "Home"]
    if has_more:
        nav_row.append("More")
    kb_rows.append(nav_row)
    kb_rows.append(["File Browser Menu"])

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    keyboard = []
    for item in folders:
        keyboard.append([KeyboardButton(text=f"[D] {item['name']}")])
    for item in files_list:
        keyboard.append([KeyboardButton(text=f"[F] {item['name']}")])

    nav_row = [KeyboardButton(text="Back"), KeyboardButton(text="Home")]
    if has_more:
        nav_row.append(KeyboardButton(text="More"))
    keyboard.append(nav_row)
    keyboard.append([KeyboardButton(text="File Browser Menu")])

    kb = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    await state.update_data(
        fb_mode=FB_BROWSE,
        fb_path=path,
        fb_offset=result.get("offset", 0),
        _fb_items=items,
    )

    await message.answer(header, reply_markup=kb)


# ===========================================================================
# Main entry point
# ===========================================================================

async def main():
    if TELEGRAM_TOKEN in ("YOUR_BOT_TOKEN_HERE", "your_bot_token_here", ""):
        logger.error(
            "TELEGRAM_TOKEN not set or still has the placeholder value! "
            "Edit the .env file with your real bot token from @BotFather."
        )
        # Small delay so Docker logs capture the message before exit
        await asyncio.sleep(0.5)
        sys.exit(1)

    logger.info("Starting Synology API Telegram Bot...")
    gn.ensure_config_file()
    logger.info("Config file at %s", gn.CONFIG_FILE)
    logger.info("Available modules: %s", ", ".join(gn.SYNO_MODULES))

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Bot crashed: %s", e)
        await asyncio.sleep(0.5)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

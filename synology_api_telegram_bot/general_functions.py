"""
General utility functions for the Synology API Telegram Bot.

Handles configuration storage, module/function discovery, and keyboard generation.
"""
import inspect
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import synology_api as syn
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

# --- Configuration paths ---
CONFIG_DIR = Path.home() / ".config" / "synology-bot"
CONFIG_FILE = CONFIG_DIR / "config.json"

# --- Config schema ---
CONFIG_KEYS = [
    "ip_address", "port", "username", "password",
    "secure", "cert_verify", "dsm_version", "debug", "otp_code"
]

# --- Synology API module names (auto-discovered) ---
_EXCLUDED_MODULES = {
    "error_codes", "base_api", "core_certificate", "core_package",
    "utils", "vpn", "exceptions", "auth",
}

# Hardcoded fallback: all known Synology API modules
# (used if auto-discovery via dir(syn) returns empty)
_FALLBACK_MODULES = [
    "audiostation", "cloud_sync", "core_active_backup", "core_backup",
    "core_group", "core_share", "core_sys_info", "core_user",
    "dhcp_server", "directory_server", "docker_api", "downloadstation",
    "drive_admin_console", "filestation", "log_center", "notestation",
    "oauth", "photos", "security_advisor", "snapshot",
    "surveillancestation", "universal_search", "usb_copy", "virtualization",
]

_discovered = sorted(
    m for m in dir(syn)
    if not m.startswith("_") and m not in _EXCLUDED_MODULES
)
SYNO_MODULES = _discovered if _discovered else _FALLBACK_MODULES

# --- Module descriptions for help ---
MODULE_DESCRIPTIONS = {
    "audiostation": "Audio Station - Music streaming",
    "cloud_sync": "Cloud Sync - Sync with cloud providers",
    "core_active_backup": "Active Backup for Business",
    "core_backup": "Backup & Restore",
    "core_group": "User Group management",
    "core_share": "Shared Folder management",
    "core_sys_info": "System Information & Status",
    "core_user": "User management",
    "dhcp_server": "DHCP Server",
    "directory_server": "Directory Server (LDAP)",
    "docker_api": "Docker / Container Manager",
    "downloadstation": "Download Station",
    "drive_admin_console": "Synology Drive Admin Console",
    "filestation": "File Station",
    "log_center": "Log Center",
    "notestation": "Note Station",
    "oauth": "OAuth & SSO",
    "photos": "Synology Photos",
    "security_advisor": "Security Advisor",
    "snapshot": "Snapshot Replication",
    "surveillancestation": "Surveillance Station",
    "universal_search": "Universal Search",
    "usb_copy": "USB Copy",
    "virtualization": "Virtual Machine Manager",
}


# --- FSM States ---
class ConfigStates(StatesGroup):
    """FSM states for configuration collection."""
    ip_address = State()
    port = State()
    username = State()
    password = State()
    secure = State()
    cert_verify = State()
    dsm_version = State()
    debug = State()
    otp_code = State()


class ArgCollectStates(StatesGroup):
    """FSM state for argument collection."""
    waiting_for_arg = State()


# --- Config file management ---

def ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def ensure_config_file() -> None:
    """Create config file with defaults if it doesn't exist."""
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        data = {key: "" for key in CONFIG_KEYS}
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("Created config file at %s", CONFIG_FILE)


def get_data_from_db() -> dict[str, str]:
    """Read configuration from JSON file."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Config file error: %s, returning defaults", e)
        return {key: "" for key in CONFIG_KEYS}


def write_full_conf_to_db(data: dict[str, str]) -> str:
    """Write full configuration dict to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    logger.info("Full config written to %s", CONFIG_FILE)
    return "Configuration saved."


def write_single_value_to_db(key: str, value: str) -> tuple[str, dict[str, str]]:
    """Update a single config key and persist."""
    ensure_config_dir()
    data = get_data_from_db()
    data[key] = value
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return f"'{key}' saved", data


# --- Synology module discovery ---

def get_syno_modules_name() -> list[str]:
    """Return list of usable Synology API module names."""
    return SYNO_MODULES


def get_syno_functions(module_name: str) -> list[str]:
    """
    Get list of callable function names for a given Synology module.

    Returns empty list if module not found or has no callable class.
    """
    if not isinstance(module_name, str):
        return []

    clean_name = module_name.replace("/", "")
    if clean_name not in SYNO_MODULES:
        return []

    module = getattr(syn, clean_name)
    classes = [
        (c, cls_obj) for c, cls_obj in inspect.getmembers(module, inspect.isclass)
        if c not in ("BaseApi", "MultipartEncoder", "BytesIO", "AESCipher")
        and cls_obj.__module__.startswith("synology_api")
    ]

    if not classes:
        return []

    cls_name, cls = classes[0]
    funcs = [
        f for f in dir(cls)
        if not f.startswith("_")
        and f not in ("logout", "shared_session", "login")
        and callable(getattr(cls, f, None))
    ]
    return sorted(funcs)


def get_function_arguments(module_name: str, function_name: str) -> list[str]:
    """Get the argument names (excluding 'self' and internal params) for a function."""
    classes = _get_module_class(module_name)
    if classes is None:
        return []
    try:
        func = getattr(classes, function_name)
    except AttributeError:
        return []
    sig = inspect.signature(func)
    excluded = {"self", "api_name", "info", "api_path", "req_param"}
    return [p for p in sig.parameters if p not in excluded]


def _get_module_class(module_name: str) -> Optional[type]:
    """Get the first usable class from a Synology module."""
    if module_name not in SYNO_MODULES:
        return None
    module = getattr(syn, module_name)
    classes = [
        (c, cls_obj) for c, cls_obj in inspect.getmembers(module, inspect.isclass)
        if c not in ("BaseApi", "MultipartEncoder", "BytesIO", "AESCipher")
        and cls_obj.__module__.startswith("synology_api")
    ]
    if not classes:
        return None
    return getattr(module, classes[0][0])


def check_if_require_arguments(
    module_name: str, function_name: str
) -> tuple[bool, Optional[list[str]], str]:
    """
    Check if a function requires arguments.

    Returns:
        (requires_args: bool, args_list: list | None, message: str)
    """
    args = get_function_arguments(module_name, function_name)
    if not args:
        return False, None, f"'{function_name}' requires no arguments."
    return (
        True,
        args,
        f"'{function_name}' requires: {', '.join(args)}",
    )


def get_all_function_lists() -> dict[str, list[str]]:
    """Get all functions for all modules as {module: [functions]}."""
    return {mod: get_syno_functions(mod) for mod in SYNO_MODULES}


def flat_function_list() -> list[str]:
    """Get a flat list of all function names across all modules."""
    result = []
    for funcs in get_all_function_lists().values():
        result.extend(funcs)
    return result


# --- Validation ---

def validate_config(data: dict[str, str]) -> list[str]:
    """Validate configuration values, returns list of error messages."""
    errors = []
    if not data.get("ip_address", "").strip():
        errors.append("IP address is required")
    try:
        port = int(data.get("port", "0"))
        if not 1 <= port <= 65535:
            errors.append("Port must be between 1 and 65535")
    except ValueError:
        errors.append("Port must be a number")
    if not data.get("username", "").strip():
        errors.append("Username is required")
    if not data.get("password", "").strip():
        errors.append("Password is required")
    try:
        dsm = int(data.get("dsm_version", "7"))
        if dsm not in (6, 7):
            errors.append("DSM version must be 6 or 7")
    except ValueError:
        errors.append("DSM version must be 6 or 7")
    return errors

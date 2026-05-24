"""
Synology API integration functions.

Handles login, logout, and function execution against the Synology NAS.
"""
import logging
import os
from typing import Any, Optional

import synology_api as syn

from . import general_functions as gn

logger = logging.getLogger(__name__)

# Global session (one active at a time per bot instance)
_session: Any = None
_current_module: Optional[str] = None


def login(module_name: str) -> Any:
    """
    Create a session to the Synology NAS for the given module.

    Reads config from the JSON config file, with password override
    from SYNOLOGY_PASSWORD environment variable.
    """
    global _session, _current_module
    config = gn.get_data_from_db()

    password = os.environ.get("SYNOLOGY_PASSWORD", config.get("password", ""))
    ip_address = config.get("ip_address", "")
    port = int(config.get("port", "5001"))
    username = config.get("username", "")
    secure = config.get("secure", "True").lower() in ("true", "1", "yes")
    cert_verify = config.get("cert_verify", "False").lower() in ("true", "1", "yes")
    dsm_version = int(config.get("dsm_version", "7"))
    debug = config.get("debug", "False").lower() in ("true", "1", "yes")
    otp_code = config.get("otp_code", "")

    logger.info(
        "Logging into %s at %s:%s as %s (DSM %s)",
        module_name, ip_address, port, username, dsm_version,
    )

    try:
        module = getattr(syn, module_name)
    except AttributeError:
        raise ValueError(f"Unknown Synology module: {module_name}")

    import inspect as _inspect
    classes = [
        c for c, _ in _inspect.getmembers(module, _inspect.isclass)
        if c not in ("BaseApi", "MultipartEncoder", "BytesIO", "AESCipher")
    ]
    if not classes:
        raise ValueError(f"No usable class found in module '{module_name}'")

    cls = getattr(module, classes[0])

    _session = cls(
        ip_address, port, username, password,
        secure, cert_verify, dsm_version, debug, otp_code,
    )
    _current_module = module_name
    logger.info("Login successful — SID: %s", getattr(_session, "_sid", "unknown"))
    return _session


def logout() -> dict[str, str]:
    """Log out from the current Synology session."""
    global _session, _current_module
    if _session is None:
        return {"status": "not_logged_in"}

    try:
        _session.logout()
        result = {"status": "logged_out", "module": _current_module or "unknown"}
    except Exception as e:
        logger.warning("Logout error (non-fatal): %s", e)
        result = {"status": "logged_out_with_error", "error": str(e)}
    finally:
        _session = None
        _current_module = None

    return result


def get_session_info() -> dict[str, Any]:
    """Get info about the current session."""
    if _session is None:
        return {"logged_in": False}
    return {
        "logged_in": True,
        "module": _current_module,
        "sid": str(getattr(_session, "_sid", "unknown")),
    }


def function_action(
    function_name: str,
    dict_of_args: Optional[dict[str, Any]] = None,
    module_name: Optional[str] = None,
) -> Any:
    """
    Execute a Synology API function on the current session.

    Args:
        function_name: Name of the function to call.
        dict_of_args: Keyword arguments to pass to the function.
        module_name: Module name (used if session needs to be set up).

    Returns:
        The result of the function call, or an error dict.
    """
    global _session, _current_module

    if module_name and _current_module != module_name:
        _current_module = module_name

    if _session is None:
        return {"error": "Not logged in. Please use the 'login' button first."}

    check_bool, check_list, _ = gn.check_if_require_arguments(
        _current_module or "", function_name
    )

    try:
        func = getattr(_session, function_name)
    except AttributeError:
        return {"error": f"Function '{function_name}' not available."}

    try:
        logger.info("Executing %s.%s", _current_module, function_name)
        if check_bool:
            if dict_of_args is None:
                return {
                    "requires_args": True,
                    "args_needed": check_list,
                    "message": f"'{function_name}' requires: {', '.join(check_list)}",
                }
            return func(**dict_of_args)
        else:
            return func()
    except Exception as e:
        logger.error("Error executing %s: %s", function_name, e, exc_info=True)
        return {"error": f"Execution failed: {e}"}

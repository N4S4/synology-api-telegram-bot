"""
File Browser helpers for the Synology API Telegram Bot.

Provides folder navigation, file listing, search, and download
via the synology-api FileStation module.
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from synology_api import filestation as fs_api

from . import general_functions as gn

logger = logging.getLogger(__name__)

# Cache for the FileStation session
_fl_session: Any = None

# Maximum files per page in browser
PAGE_SIZE = 30

# Maximum file size for Telegram download (50 MB)
MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024

# Starting path for browsing
DEFAULT_HOME = "/home"


def _get_session() -> Any:
    """Get or create a FileStation API session."""
    global _fl_session
    if _fl_session is not None:
        try:
            # Quick check if session is alive
            _fl_session.get_info()
            return _fl_session
        except Exception:
            _fl_session = None

    config = gn.get_data_from_db()
    password = os.environ.get("SYNOLOGY_PASSWORD", config.get("password", ""))

    _fl_session = fs_api.FileStation(
        config.get("ip_address", ""),
        int(config.get("port", "5001")),
        config.get("username", ""),
        password,
        secure=config.get("secure", "True").lower() in ("true", "1", "yes"),
        cert_verify=config.get("cert_verify", "False").lower() in ("true", "1", "yes"),
        dsm_version=int(config.get("dsm_version", "7")),
        debug=config.get("debug", "False").lower() in ("true", "1", "yes"),
        otp_code=config.get("otp_code", ""),
    )
    logger.info("FileStation session created, SID: %s", getattr(_fl_session, "_sid", "?"))
    return _fl_session


def logout_session() -> None:
    """Logout and clear the FileStation session."""
    global _fl_session
    if _fl_session:
        try:
            _fl_session.logout()
        except Exception as e:
            logger.debug("Logout error (non-fatal): %s", e)
        _fl_session = None


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes is None or size_bytes < 0:
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def list_directory(
    path: str = DEFAULT_HOME,
    offset: int = 0,
    limit: int = PAGE_SIZE,
    pattern: Optional[str] = None,
) -> dict[str, Any]:
    """
    List files and folders in a directory.

    Returns:
        {
            "path": str,
            "items": [{"name": str, "isdir": bool, "size": int, "path": str}, ...],
            "total": int,
            "offset": int,
            "has_more": bool,
        }
    """
    fl = _get_session()
    try:
        result = fl.get_file_list(
            folder_path=path,
            offset=offset,
            limit=limit,
            sort_by="name",
            sort_direction="asc",
            pattern=pattern,
        )
    except Exception as e:
        logger.error("list_directory(%s) failed: %s", path, e)
        return {"error": str(e), "path": path, "items": []}

    if not result.get("success"):
        return {
            "error": result.get("error", {}).get("code", "unknown"),
            "path": path,
            "items": [],
        }

    data = result.get("data", {})
    files = data.get("files", [])

    items = []
    for f in files:
        additional = f.get("additional", {})
        size_val = additional.get("size", 0) if not f.get("isdir") else 0
        items.append({
            "name": f.get("name", "?"),
            "isdir": f.get("isdir", False),
            "size": size_val,
            "path": f.get("path", f"{path}/{f.get('name', '')}"),
        })

    total = data.get("total", 0)
    has_more = (offset + len(items)) < total

    return {
        "path": path,
        "items": items,
        "total": total,
        "offset": offset,
        "has_more": has_more,
    }


def get_file_info(file_path: str) -> dict[str, Any]:
    """Get detailed info for a single file."""
    fl = _get_session()
    try:
        result = fl.get_file_info(file_path)
        if result.get("success"):
            return result.get("data", {})
    except Exception as e:
        logger.error("get_file_info(%s) failed: %s", file_path, e)
    return {"error": "Could not get file info"}


def download_file(file_path: str) -> Optional[str]:
    """
    Download a file from the NAS to a local temp directory.

    Returns the local file path, or None on failure.
    """
    fl = _get_session()

    # Check file size first
    info_result = get_file_info(file_path)
    files = info_result.get("files", [])
    if files:
        size = files[0].get("additional", {}).get("size", 0)
        if size > MAX_DOWNLOAD_SIZE:
            logger.warning("File too large: %s (%s)", file_path, format_size(size))
            return None  # Will be handled by caller with a message

    # Create temp directory for download
    tmp_dir = tempfile.mkdtemp(prefix="syno_dl_")
    file_name = Path(file_path).name

    try:
        result = fl.get_file(
            path=file_path,
            mode="download",
            dest_path=tmp_dir,
        )
        if result.get("success"):
            local_path = os.path.join(tmp_dir, file_name)
            if os.path.exists(local_path):
                logger.info("Downloaded %s -> %s", file_path, local_path)
                return local_path
            else:
                logger.error("Download claimed success but file not found: %s", local_path)
        else:
            logger.error("Download failed: %s", result)
    except Exception as e:
        logger.error("download_file(%s) failed: %s", file_path, e)

    return None


def search_files(
    folder_path: str,
    pattern: str = "*",
    recursive: bool = True,
) -> dict[str, Any]:
    """
    Search for files matching a pattern.

    Returns a dict with search results or error.
    """
    fl = _get_session()
    try:
        # Start search
        search_result = fl.search_start(
            folder_path=folder_path,
            recursive=recursive,
            pattern=pattern,
        )
        if not search_result.get("success"):
            return {"error": "Search failed to start", "items": []}

        task_id = search_result.get("data", {}).get("taskid")
        if not task_id:
            return {"error": "No task ID returned", "items": []}

        # Get results (may need polling for large searches)
        import time
        max_wait = 10
        for _ in range(max_wait):
            list_result = fl.get_search_list(
                task_id=task_id,
                limit=50,
                sort_by="name",
                sort_direction="asc",
                offset=0,
            )
            if list_result.get("success") and list_result.get("data", {}).get("finished", False):
                break
            time.sleep(0.5)

        if not list_result.get("success"):
            return {"error": "Search failed", "items": []}

        data = list_result.get("data", {})
        files = data.get("files", [])

        items = []
        for f in files[:50]:  # Limit to 50 results
            additional = f.get("additional", {})
            items.append({
                "name": f.get("name", "?"),
                "isdir": f.get("isdir", False),
                "size": additional.get("size", 0),
                "path": f.get("path", "?"),
            })

        return {
            "path": folder_path,
            "pattern": pattern,
            "items": items,
            "total": len(items),
        }

    except Exception as e:
        logger.error("search_files(%s, %s) failed: %s", folder_path, pattern, e)
        return {"error": str(e), "items": []}

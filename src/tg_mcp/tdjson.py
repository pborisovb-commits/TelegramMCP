"""Low-level ctypes binding to Telegram's official tdjson interface.

This module loads ``libtdjson`` (the compiled TDLib shared library) directly via
the Python standard-library ``ctypes`` module. No third-party Telegram wrapper is
used: we call exactly the C functions documented by TDLib's JSON interface
(https://core.telegram.org/tdlib/docs/td__json__client_8h.html).

The JSON interface we use is the "client manager" API:
    td_create_client_id()        -> int
    td_send(client_id, request)  -> None        (request is a JSON string)
    td_receive(timeout)          -> str | None   (JSON string for ANY client)
    td_execute(request)          -> str | None   (synchronous, static methods)
    td_set_log_message_callback(max_verbosity_level, callback)
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
from typing import Any, Optional


def _find_library() -> str:
    """Locate libtdjson.so.

    Search order:
      1. $TDJSON_PATH env var (explicit override).
      2. A copy vendored in the repo under <repo>/lib/.
      3. The system loader (ctypes.util.find_library / ldconfig).
    """
    env = os.environ.get("TDJSON_PATH")
    if env:
        if not os.path.exists(env):
            raise FileNotFoundError(f"TDJSON_PATH points to a missing file: {env}")
        return env

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    for name in ("libtdjson.so", "libtdjson.dylib", "tdjson.dll"):
        candidate = os.path.join(repo_root, "lib", name)
        if os.path.exists(candidate):
            return candidate

    found = ctypes.util.find_library("tdjson")
    if found:
        return found

    raise FileNotFoundError(
        "libtdjson not found. Build TDLib (see HANDOFF.md / scripts/build_tdlib.sh) "
        "and place libtdjson.so in <repo>/lib/, or set TDJSON_PATH."
    )


class TdJson:
    """Thin wrapper over the raw tdjson C functions.

    All request/response payloads are plain ``dict`` objects; JSON (de)serialization
    is handled here so callers work with Python data structures.
    """

    def __init__(self, library_path: Optional[str] = None) -> None:
        self._path = library_path or _find_library()
        self._tdjson = ctypes.CDLL(self._path)

        self._td_create_client_id = self._tdjson.td_create_client_id
        self._td_create_client_id.restype = ctypes.c_int
        self._td_create_client_id.argtypes = []

        self._td_send = self._tdjson.td_send
        self._td_send.restype = None
        self._td_send.argtypes = [ctypes.c_int, ctypes.c_char_p]

        self._td_receive = self._tdjson.td_receive
        self._td_receive.restype = ctypes.c_char_p
        self._td_receive.argtypes = [ctypes.c_double]

        self._td_execute = self._tdjson.td_execute
        self._td_execute.restype = ctypes.c_char_p
        self._td_execute.argtypes = [ctypes.c_char_p]

        # Quiet TDLib's noisy stderr logging (default verbosity is 5).
        # 1 = errors only; this is the officially documented static method.
        self.execute({"@type": "setLogVerbosityLevel", "new_verbosity_level": 1})

    @property
    def library_path(self) -> str:
        return self._path

    def create_client_id(self) -> int:
        return self._td_create_client_id()

    def send(self, client_id: int, request: dict[str, Any]) -> None:
        payload = json.dumps(request).encode("utf-8")
        self._td_send(client_id, payload)

    def receive(self, timeout: float = 1.0) -> Optional[dict[str, Any]]:
        result = self._td_receive(timeout)
        if result is None:
            return None
        return json.loads(result.decode("utf-8"))

    def execute(self, request: dict[str, Any]) -> Optional[dict[str, Any]]:
        payload = json.dumps(request).encode("utf-8")
        result = self._td_execute(payload)
        if result is None:
            return None
        return json.loads(result.decode("utf-8"))

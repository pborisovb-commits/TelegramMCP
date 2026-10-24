"""High-level TDLib client built on the tdjson binding.

TDLib is fully asynchronous: you ``send`` requests and ``receive`` a stream of
responses and updates on a single queue. This class turns that into a convenient
synchronous ``invoke(request) -> response`` call by:

  * running the receive loop in a background thread,
  * tagging each request with a unique ``@extra`` id and parking the caller on a
    ``threading.Event`` until the matching response arrives,
  * routing ``updateAuthorizationState`` updates through an auth state machine.

Authentication (phone -> code -> optional 2FA password) is interactive and only
needs to happen once; TDLib persists the session in its own encrypted database
directory, so subsequent runs come up already authorized. See scripts/login.py
for the one-time interactive login.
"""

from __future__ import annotations

import threading
import copy
import uuid
from typing import Any, Callable, Optional

from .tdjson import TdJson


class TdlibError(RuntimeError):
    """Raised when TDLib returns an ``error`` object for a request."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"TDLib error {code}: {message}")
        self.code = code
        self.message = message


# Callback types for the interactive parts of authorization.
PhoneProvider = Callable[[], str]
CodeProvider = Callable[[], str]
PasswordProvider = Callable[[], str]


class TelegramClient:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        *,
        database_directory: str = "td_data",
        files_directory: Optional[str] = None,
        use_test_dc: bool = False,
        tdjson: Optional[TdJson] = None,
    ) -> None:
        self._api_id = api_id
        self._api_hash = api_hash
        self._database_directory = database_directory
        self._files_directory = files_directory or database_directory
        self._use_test_dc = use_test_dc

        self._td = tdjson or TdJson()
        self._client_id: Optional[int] = None

        self._lock = threading.Lock()
        self._pending: dict[str, dict[str, Any]] = {}
        self._events: dict[str, threading.Event] = {}

        self._auth_state: Optional[str] = None
        self._last_code_info: dict[str, Any] = {}
        self._auth_ready = threading.Event()
        self._auth_error: Optional[Exception] = None
        self._closed = threading.Event()
        self._folders_ready = threading.Event()
        self._folders_update: dict[str, Any] = {}

        # Interactive auth providers; set via login().
        self._phone_provider: Optional[PhoneProvider] = None
        self._code_provider: Optional[CodeProvider] = None
        self._password_provider: Optional[PasswordProvider] = None
        self._qr_provider: Optional[Callable[[str], None]] = None
        self._qr_requested = False

        self._recv_thread: Optional[threading.Thread] = None

    # ----- lifecycle -------------------------------------------------------

    def start(self) -> None:
        """Create the TDLib client and begin the receive loop."""
        if self._recv_thread is not None:
            return
        self._client_id = self._td.create_client_id()
        self._recv_thread = threading.Thread(
            target=self._receive_loop, name="tdlib-receive", daemon=True
        )
        self._recv_thread.start()
        # Kick TDLib so it emits the first authorizationState update.
        self._send_raw({"@type": "getAuthorizationState"})

    def close(self) -> None:
        if self._client_id is not None and not self._closed.is_set():
            try:
                self._send_raw({"@type": "close"})
            except Exception:
                pass
        self._closed.set()

    # ----- auth ------------------------------------------------------------

    def login(
        self,
        phone_provider: PhoneProvider,
        code_provider: CodeProvider,
        password_provider: Optional[PasswordProvider] = None,
        *,
        qr_provider: Optional[Callable[[str], None]] = None,
        timeout: float = 300.0,
    ) -> None:
        """Run the interactive login, blocking until authorized.

        The providers are called only when TDLib actually requests that piece of
        data, so an already-authorized session returns immediately without
        prompting.
        """
        self._phone_provider = phone_provider
        self._code_provider = code_provider
        self._password_provider = password_provider
        self._qr_provider = qr_provider
        if self._recv_thread is None:
            self.start()
        self.wait_until_ready(timeout=timeout)

    def wait_until_ready(self, *, timeout: float = 60.0) -> None:
        """Block until the session reaches authorizationStateReady."""
        if self._recv_thread is None:
            self.start()
        if not self._auth_ready.wait(timeout=timeout):
            raise TimeoutError(
                f"Telegram authorization did not complete within {timeout}s "
                f"(last state: {self._auth_state}). "
                "If this is a first run, log in with scripts/login.py."
            )
        if self._auth_error is not None:
            raise self._auth_error

    @property
    def is_ready(self) -> bool:
        return self._auth_ready.is_set() and self._auth_error is None

    # ----- requests --------------------------------------------------------

    def invoke(self, request: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
        """Send a request and block for its response. Raises TdlibError on error."""
        if self._client_id is None:
            raise RuntimeError("Client not started; call start() first.")
        extra = uuid.uuid4().hex
        request = dict(request)
        request["@extra"] = extra
        event = threading.Event()
        with self._lock:
            self._events[extra] = event
        self._td.send(self._client_id, request)
        if not event.wait(timeout=timeout):
            with self._lock:
                self._events.pop(extra, None)
                self._pending.pop(extra, None)
            raise TimeoutError(f"Timed out waiting for response to {request.get('@type')}")
        with self._lock:
            response = self._pending.pop(extra, None)
            self._events.pop(extra, None)
        if response is None:
            raise RuntimeError("Response vanished (client closed?)")
        if response.get("@type") == "error":
            raise TdlibError(response.get("code", 0), response.get("message", ""))
        return response

    def _send_raw(self, request: dict[str, Any]) -> None:
        assert self._client_id is not None
        self._td.send(self._client_id, request)

    # ----- receive loop ----------------------------------------------------

    def _receive_loop(self) -> None:
        while not self._closed.is_set():
            event = self._td.receive(1.0)
            if event is None:
                continue
            extra = event.get("@extra")
            if extra is not None:
                with self._lock:
                    waiter = self._events.get(extra)
                    if waiter is not None:
                        self._pending[extra] = event
                if waiter is not None:
                    waiter.set()
                    continue
            # Surface unsolicited errors (e.g. a failed resend/checkCode whose
            # response carries no @extra) instead of silently dropping them.
            if event.get("@type") == "error":
                import sys
                print(
                    f">>> TDLib error: code={event.get('code')} "
                    f"message={event.get('message')!r}",
                    file=sys.stderr,
                    flush=True,
                )
                continue
            self._handle_update(event)

    def _handle_update(self, update: dict[str, Any]) -> None:
        if update.get("@type") == "updateChatFolders":
            with self._lock:
                self._folders_update = copy.deepcopy(update)
            self._folders_ready.set()
        if update.get("@type") == "updateAuthorizationState":
            state = update.get("authorization_state", {})
            try:
                self._on_auth_state(state)
            except Exception as exc:  # surface auth failures to waiters
                self._auth_error = exc
                self._auth_ready.set()

    def get_chat_folders(self, timeout: float = 30.0) -> dict[str, Any]:
        """Wait for TDLib's initial folder snapshot; retain subsequent updates."""
        if not self._folders_ready.wait(timeout):
            raise TimeoutError("TDLib has not supplied the chat folder list yet; retry.")
        with self._lock:
            return copy.deepcopy(self._folders_update)

    def _on_auth_state(self, state: dict[str, Any]) -> None:
        kind = state.get("@type")
        self._auth_state = kind

        if kind == "authorizationStateWaitTdlibParameters":
            self._send_raw(
                {
                    "@type": "setTdlibParameters",
                    "use_test_dc": self._use_test_dc,
                    "database_directory": self._database_directory,
                    "files_directory": self._files_directory,
                    "use_file_database": True,
                    "use_chat_info_database": True,
                    "use_message_database": True,
                    "use_secret_chats": False,
                    "api_id": self._api_id,
                    "api_hash": self._api_hash,
                    "system_language_code": "en",
                    "device_model": "tg-mcp",
                    "application_version": "0.1.0",
                }
            )
        elif kind in ("authorizationStateWaitPhoneNumber", "authorizationStateWaitCode") and (
            self._qr_provider is not None and not self._qr_requested
        ):
            # QR login: confirm from an already logged-in device instead of a code.
            self._qr_requested = True
            self._send_raw({"@type": "requestQrCodeAuthentication", "other_user_ids": []})
        elif kind == "authorizationStateWaitOtherDeviceConfirmation":
            if self._qr_provider is not None:
                self._qr_provider(state.get("link", ""))
        elif kind == "authorizationStateWaitPhoneNumber":
            if self._phone_provider is None:
                raise RuntimeError(
                    "Session is not authorized and no phone provider was set. "
                    "Run scripts/login.py to log in interactively."
                )
            phone = self._phone_provider()
            self._send_raw(
                {"@type": "setAuthenticationPhoneNumber", "phone_number": phone}
            )
        elif kind == "authorizationStateWaitCode":
            if self._code_provider is None:
                raise RuntimeError("Login code required but no code provider was set.")
            self._last_code_info = state.get("code_info") or {}
            code = self._code_provider()
            if code == "__resend__":
                self._send_raw({"@type": "resendAuthenticationCode"})
                return
            self._send_raw({"@type": "checkAuthenticationCode", "code": code})
        elif kind == "authorizationStateWaitPassword":
            if self._password_provider is None:
                raise RuntimeError(
                    "Two-step verification password required but no password "
                    "provider was set."
                )
            password = self._password_provider()
            self._send_raw(
                {"@type": "checkAuthenticationPassword", "password": password}
            )
        elif kind == "authorizationStateReady":
            self._auth_error = None
            self._auth_ready.set()
        elif kind == "authorizationStateClosed":
            self._closed.set()
            if not self._auth_ready.is_set():
                self._auth_error = RuntimeError("Authorization closed before ready.")
                self._auth_ready.set()

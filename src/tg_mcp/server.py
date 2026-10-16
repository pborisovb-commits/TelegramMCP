"""MCP server exposing Telegram client operations as tools.

Built on the official MCP Python SDK (FastMCP). The server talks to Telegram
through a single already-authorized TDLib session; run ``scripts/login.py`` once
before starting the server to create that session.

Run with:
    python -m tg_mcp.server      (stdio transport)
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import api
from .client import TelegramClient
from .config import Config

mcp = FastMCP("telegram")

_client: TelegramClient | None = None


def _get_client() -> TelegramClient:
    """Lazily create and authorize the TDLib client on first tool call."""
    global _client
    if _client is None:
        cfg = Config.from_env()
        client = TelegramClient(
            cfg.api_id, cfg.api_hash, database_directory=cfg.database_dir
        )
        client.start()
        # No interactive providers here: the session must already be authorized.
        client.wait_until_ready(timeout=30.0)
        _client = client
    return _client


@mcp.tool()
def whoami() -> dict[str, Any]:
    """Return the currently logged-in Telegram account (name, username, id)."""
    return api.get_me(_get_client())


@mcp.tool()
def list_chats(limit: int = 30) -> list[dict[str, Any]]:
    """List the user's most recent chats (dialogs), newest first.

    Returns chat id, title, type, unread count, and a summary of the last message.
    Use the returned id with read_chat or send_message.
    """
    return api.list_chats(_get_client(), limit=limit)


@mcp.tool()
def read_chat(chat_id: int, limit: int = 30) -> list[dict[str, Any]]:
    """Read recent messages from a chat by its numeric id, oldest-to-newest.

    Get the chat_id first via list_chats, search_chats, or resolve_chat.
    """
    return api.get_chat_history(_get_client(), chat_id, limit=limit)


@mcp.tool()
def send_message(chat_id: int, text: str) -> dict[str, Any]:
    """Send a text message to a chat by its numeric id, as the logged-in user.

    This sends a real message from the user's own account. Confirm the chat_id
    (e.g. via list_chats) before sending.
    """
    return api.send_message(_get_client(), chat_id, text)


@mcp.tool()
def search_chats(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search the user's chats and contacts by title/name."""
    return api.search_chats(_get_client(), query, limit=limit)


@mcp.tool()
def resolve_chat(username: str) -> dict[str, Any]:
    """Resolve a public @username to a chat (so you can read or message it)."""
    return api.resolve_chat(_get_client(), username)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

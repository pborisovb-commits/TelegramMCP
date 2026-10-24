"""MCP server exposing Telegram client operations as tools.

Built on the official MCP Python SDK (MCPServer, formerly FastMCP in SDK v1).
The server talks to Telegram
through a single already-authorized TDLib session; run ``scripts/login.py`` once
before starting the server to create that session.

Run with:
    python -m tg_mcp.server      (stdio transport)
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import api
from .client import TelegramClient
from .config import Config

mcp = MCPServer("telegram")

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
def list_chat_folders() -> dict[str, Any]:
    """List Telegram sidebar folders (e.g. Monkey, bots), their IDs and order.

    These are user-created chat folders, not group conversations.
    Use a returned id as folder_id in list_chats to get its actual members.
    """
    return api.list_chat_folders(_get_client())


@mcp.tool()
def list_chats(limit: int = 30, folder_id: int | None = None,
               offset: int = 0, archived: bool = False) -> list[dict[str, Any]]:
    """List chats in Telegram order, including pinned chats first.

    Default: main list. For a sidebar folder first call list_chat_folders,
    then pass its folder_id. archived=True selects archive, mutually exclusive
    with folder_id. limit: 1..1000; offset: skip chats for pagination (not a
    stable snapshot if chats move). A short page means the list is exhausted.
    Returns chat ID, title, type, unread count and last message.
    """
    try:
        return api.list_chats(_get_client(), limit=limit, folder_id=folder_id,
                              offset=offset, archived=archived)
    except (ValueError, TimeoutError) as exc:
        raise ToolError(str(exc)) from exc


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

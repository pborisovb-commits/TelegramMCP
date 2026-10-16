"""High-level Telegram operations expressed as plain functions over a client.

Each function issues one or more TDLib requests via ``client.invoke`` and returns
compact, JSON-serializable Python structures suitable for feeding to a language
model (ids, names, text, timestamps) rather than the full TDLib objects.

TDLib method/field names follow the official TL schema:
https://core.telegram.org/tdlib/docs/td__api_8h.html
"""

from __future__ import annotations

from typing import Any, Optional

from .client import TelegramClient


def get_me(client: TelegramClient) -> dict[str, Any]:
    user = client.invoke({"@type": "getMe"})
    return _user_summary(user)


def list_chats(client: TelegramClient, limit: int = 30) -> list[dict[str, Any]]:
    """Return the main chat list, most recent first."""
    main_list = {"@type": "chatListMain"}
    # Ask TDLib to load chats into memory; ignore the "no more chats" (404) error.
    try:
        client.invoke({"@type": "loadChats", "chat_list": main_list, "limit": limit})
    except Exception:
        pass
    result = client.invoke({"@type": "getChats", "chat_list": main_list, "limit": limit})
    chats: list[dict[str, Any]] = []
    for chat_id in result.get("chat_ids", []):
        try:
            chat = client.invoke({"@type": "getChat", "chat_id": chat_id})
        except Exception:
            continue
        chats.append(_chat_summary(chat))
    return chats


def get_chat_history(
    client: TelegramClient, chat_id: int, limit: int = 30
) -> list[dict[str, Any]]:
    """Return up to ``limit`` most recent messages in a chat, oldest-to-newest."""
    # Opening the chat helps TDLib fetch history reliably.
    try:
        client.invoke({"@type": "getChat", "chat_id": chat_id})
    except Exception:
        pass

    collected: list[dict[str, Any]] = []
    from_message_id = 0
    # TDLib may return fewer messages than requested per call, so loop.
    for _ in range(10):
        resp = client.invoke(
            {
                "@type": "getChatHistory",
                "chat_id": chat_id,
                "from_message_id": from_message_id,
                "offset": 0,
                "limit": min(limit - len(collected), 100),
                "only_local": False,
            }
        )
        messages = resp.get("messages", [])
        if not messages:
            break
        collected.extend(messages)
        from_message_id = messages[-1]["id"]
        if len(collected) >= limit:
            break
    summaries = [_message_summary(m) for m in collected[:limit]]
    summaries.reverse()  # oldest first for natural reading order
    return summaries


def send_message(client: TelegramClient, chat_id: int, text: str) -> dict[str, Any]:
    msg = client.invoke(
        {
            "@type": "sendMessage",
            "chat_id": chat_id,
            "input_message_content": {
                "@type": "inputMessageText",
                "text": {"@type": "formattedText", "text": text},
            },
        }
    )
    return _message_summary(msg)


def search_chats(client: TelegramClient, query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search the user's own chats/contacts by title or name (local + server)."""
    result = client.invoke(
        {"@type": "searchChatsOnServer", "query": query, "limit": limit}
    )
    chats: list[dict[str, Any]] = []
    for chat_id in result.get("chat_ids", []):
        try:
            chat = client.invoke({"@type": "getChat", "chat_id": chat_id})
        except Exception:
            continue
        chats.append(_chat_summary(chat))
    return chats


def resolve_chat(client: TelegramClient, username: str) -> dict[str, Any]:
    """Resolve a public @username to a chat summary."""
    username = username.lstrip("@")
    chat = client.invoke({"@type": "searchPublicChat", "username": username})
    return _chat_summary(chat)


# ----- summarizers ---------------------------------------------------------


def _user_summary(user: dict[str, Any]) -> dict[str, Any]:
    usernames = user.get("usernames", {}) or {}
    active = usernames.get("active_usernames", []) if isinstance(usernames, dict) else []
    return {
        "id": user.get("id"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "username": active[0] if active else None,
        "phone_number": user.get("phone_number"),
    }


def _chat_summary(chat: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": chat.get("id"),
        "title": chat.get("title"),
        "type": (chat.get("type") or {}).get("@type"),
        "unread_count": chat.get("unread_count"),
        "last_message": _message_summary(chat["last_message"])
        if chat.get("last_message")
        else None,
    }


def _message_summary(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": message.get("id"),
        "chat_id": message.get("chat_id"),
        "sender_id": _sender_id(message.get("sender_id")),
        "date": message.get("date"),
        "is_outgoing": message.get("is_outgoing"),
        "text": _content_text(message.get("content", {})),
    }


def _sender_id(sender: Optional[dict[str, Any]]) -> Optional[int]:
    if not sender:
        return None
    return sender.get("user_id") or sender.get("chat_id")


def _content_text(content: dict[str, Any]) -> str:
    kind = content.get("@type")
    if kind == "messageText":
        return (content.get("text") or {}).get("text", "")
    if kind == "messagePhoto":
        return f"[photo] {(content.get('caption') or {}).get('text', '')}".strip()
    if kind == "messageVideo":
        return f"[video] {(content.get('caption') or {}).get('text', '')}".strip()
    if kind == "messageDocument":
        return f"[document] {(content.get('caption') or {}).get('text', '')}".strip()
    if kind == "messageSticker":
        return "[sticker]"
    if kind == "messageVoiceNote":
        return "[voice note]"
    if kind:
        return f"[{kind[len('message'):].lower() if kind.startswith('message') else kind}]"
    return ""

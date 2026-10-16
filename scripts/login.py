#!/usr/bin/env python3
"""One-time interactive login to create an authorized TDLib session.

Run this once from a terminal:

    TG_API_ID=... TG_API_HASH=... python scripts/login.py

It will prompt for your phone number, the login code Telegram sends you, and
(if you have two-step verification enabled) your password. On success it writes
the session into the database directory (default ./td_data). After that the MCP
server starts up already authorized and never prompts again.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tg_mcp.client import TelegramClient  # noqa: E402
from tg_mcp.config import Config  # noqa: E402


def main() -> int:
    cfg = Config.from_env()
    client = TelegramClient(cfg.api_id, cfg.api_hash, database_directory=cfg.database_dir)
    print("Connecting to Telegram (TDLib)...")
    try:
        client.login(
            phone_provider=lambda: input("Phone number (international, e.g. +1234...): ").strip(),
            code_provider=lambda: input("Login code (from Telegram): ").strip(),
            password_provider=lambda: getpass.getpass("2FA password: "),
            timeout=600.0,
        )
    except Exception as exc:
        print(f"Login failed: {exc}", file=sys.stderr)
        return 1
    me = client.invoke({"@type": "getMe"})
    name = " ".join(filter(None, [me.get("first_name"), me.get("last_name")]))
    print(f"Logged in as {name} (id {me.get('id')}). Session saved to {cfg.database_dir}/.")
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

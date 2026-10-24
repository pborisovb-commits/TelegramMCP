#!/usr/bin/env python3
"""One-time interactive login to create an authorized TDLib session.

Run this once from a terminal:

    TG_API_ID=... TG_API_HASH=... python scripts/login.py

QR login is the default; --phone enables phone/code login. It may prompt for
your password if two-step verification is enabled. On success it writes
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

    _channel = {
        "authenticationCodeTypeTelegramMessage": "a message in the Telegram app "
        "(service chat 'Telegram' on a device where you are already logged in)",
        "authenticationCodeTypeSms": "SMS",
        "authenticationCodeTypeCall": "a phone call",
        "authenticationCodeTypeFlashCall": "a flash phone call (caller ID is the code)",
        "authenticationCodeTypeMissedCall": "a missed call (last digits of the number are the code)",
        "authenticationCodeTypeFragment": "the Fragment platform (fragment.com)",
    }

    def code_provider() -> str:
        info = client._last_code_info or {}
        ctype = (info.get("type") or {}).get("@type", "")
        where = _channel.get(ctype, ctype or "an unknown channel")
        length = (info.get("type") or {}).get("length")
        print(f"\n>>> Telegram says it sent the code via: {where}"
              + (f" ({length} digits)" if length else ""))
        nxt = info.get("next_type")
        if nxt:
            nxt_where = _channel.get(nxt.get("@type", ""), "another channel")
            print(f">>> If it doesn't arrive, type 'resend' to resend via {nxt_where}.")
        return input("Login code (or 'resend'): ").strip()

    def qr_provider(link: str) -> None:
        print("\n>>> On your phone: Telegram -> Settings -> Devices -> Link Desktop Device,")
        print(">>> then scan this QR code (it refreshes every ~30s; a new one will print):\n")
        try:
            import qrcode

            qr = qrcode.QRCode(border=1)
            qr.add_data(link)
            qr.print_ascii(invert=True)
        except ImportError:
            print("(pip install qrcode to see the QR here; or turn this link into a QR:)")
        print(f"\n{link}\n")

    try:
        client.login(
            qr_provider=None if "--phone" in sys.argv else qr_provider,
            phone_provider=lambda: input("Phone number (international, e.g. +1234...): ").strip(),
            code_provider=lambda: "__resend__"
            if (c := code_provider()).lower() in ("resend", "r")
            else c,
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

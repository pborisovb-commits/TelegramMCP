# tg-mcp

An MCP server that acts as a **Telegram client** (your own account, not a bot),
so language models can read your chats, search, and send messages on your behalf.

It talks to Telegram only through **official software**: Telegram's own
[TDLib](https://core.telegram.org/tdlib) library via its documented
[tdjson JSON interface](https://core.telegram.org/tdlib/docs/td__json__client_8h.html),
loaded directly with Python's standard-library `ctypes` — no third-party Telegram
wrappers. The MCP layer uses the official MCP Python SDK.

## How it works

```
LLM  <--MCP(stdio/JSON-RPC)-->  tg_mcp.server  -->  tg_mcp.client  -->  libtdjson.so  -->  Telegram
```

- `src/tg_mcp/tdjson.py` — ctypes binding to `libtdjson` (td_send/receive/execute).
- `src/tg_mcp/client.py` — async→sync TDLib client + authorization state machine.
- `src/tg_mcp/api.py` — high-level operations returning compact JSON.
- `src/tg_mcp/server.py` — MCP tools: `whoami`, `list_chats`, `read_chat`,
  `send_message`, `search_chats`, `resolve_chat`.

## Setup

### 1. Build the Telegram engine (libtdjson)

No prebuilt package exists on Ubuntu, so build it from Telegram's source:

```bash
scripts/build_tdlib.sh      # writes lib/libtdjson.so (~20–40 min)
```

Or point the app at an existing library: `export TDJSON_PATH=/path/to/libtdjson.so`.

### 2. Get API credentials

Create an app at <https://my.telegram.org> → **API development tools** to get your
`api_id` and `api_hash`.

```bash
export TG_API_ID=123456
export TG_API_HASH=abcdef0123456789abcdef0123456789
```

### 3. Install and log in (once)

```bash
pip install -e .
python scripts/login.py       # prompts for phone, code, and 2FA password
```

This creates an authorized session under `./td_data/` (git-ignored — it is a
credential to your account).

### 4. Run the MCP server

```bash
python -m tg_mcp.server       # stdio transport
```

Register it with an MCP client (e.g. Claude Desktop `mcpServers` config):

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python",
      "args": ["-m", "tg_mcp.server"],
      "env": {
        "TG_API_ID": "123456",
        "TG_API_HASH": "abcdef0123456789abcdef0123456789",
        "TG_DATABASE_DIR": "/absolute/path/to/td_data",
        "TDJSON_PATH": "/absolute/path/to/lib/libtdjson.so"
      }
    }
  }
}
```

## Chat folders

- `list_chat_folders()` returns sidebar folders with IDs, titles, icons and their
  Telegram order, plus the position of the main chat list.
- `list_chats(folder_id=3, limit=100, offset=0)` reads an actual folder. Obtain IDs
  from `list_chat_folders`; do not infer them from names or chat types.
- `list_chats(archived=True)` reads the archive. Without selectors the existing
  main-list behavior is preserved. Folder and archive selectors are exclusive.
- `limit` is 1..1000, `offset` is nonnegative, and their sum is at most 10000.
  A short page means exhaustion. Pagination is not a stable snapshot if chats
  move while reading. One chat can belong to multiple folders.
- Folder changes are received through TDLib's `updateChatFolders`. Membership,
  automatic filters and pinned ordering are handled by TDLib, not reconstructed
  from explicitly included chat IDs. Failed loads are not returned as empty lists.

Local Windows launch: `login-local.ps1` uses QR authentication; `start-mcp.ps1`
starts the Docker-backed stdio server. Rebuild with
`docker build -f Dockerfile.local -t mcptg-local:0.1 .` after source changes and
reconnect the MCP client. Only one active TDLib process may own `td_data`.

Tests: `python -m unittest discover -s scripts -p "test_*.py"` after installing
the project in editable mode.

## Security notes

- `td_data/` and `.env` are **credentials to your Telegram account** — never commit
  or share them. They are git-ignored.
- `send_message` sends real messages from your account. Review tool calls.

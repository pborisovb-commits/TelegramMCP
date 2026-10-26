# TelegramMCP

[Русский](README.ru.md) | **English**

**Your Telegram account in an AI assistant: chats, folders, messages, and search.**

Author: **[pborisovb](https://github.com/pborisovb-commits)** · [MIT License](LICENSE)

TelegramMCP connects your personal Telegram account to an MCP-compatible application,
such as Codex. MCP gives an assistant tools: instead of manually copying a conversation,
you can ask it to find a chat or read recent messages. This connects your own account;
it is not a Telegram bot.

The project uses Telegram's official **TDLib** library, without Telethon or Pyrogram.
TelegramMCP is an independent project, not an official Telegram product.

## Things you can ask

- “Show my Telegram folders.”
- “Show the chats in my Work folder.”
- “Find a chat by name.”
- “Read the last 30 messages in the selected chat and summarize them.”
- “Draft a reply, show me the text, and send it after I confirm.”

Messages are sent from your account. Check the recipient and text before approving
a send. Approval rules are configured in your AI application; the server itself
does not display a separate confirmation dialog.

## Quick start: Windows + Docker Desktop

This is the tested installation method. You do not need to install Python or
compilers separately. The included library targets **x86-64 (Intel/AMD)**.
Windows ARM and Apple Silicon have not been tested with this version.

You will need:

1. Telegram on your phone, already signed in.
2. [Docker Desktop](https://www.docker.com/products/docker-desktop/) using Linux containers.
   Start it after installation and wait for the engine to become ready. If the installer
   asks you to enable WSL 2 or restart your computer, follow its instructions.
3. [Git](https://git-scm.com/downloads), or a downloaded ZIP of this repository.
4. An AI application that supports **local MCP over stdio**. A regular web chat page
   cannot launch a program on your computer by itself.

### 1. Download the project

Open PowerShell in the directory where you want to keep the project:

```powershell
git clone https://github.com/pborisovb-commits/TelegramMCP.git
cd TelegramMCP
```

Without Git: on GitHub, select **Code → Download ZIP**, extract the archive, open
the extracted folder in File Explorer, and choose **Open in Terminal**.

### 2. Get your Telegram application credentials

Open [my.telegram.org](https://my.telegram.org), sign in, and go to
**API development tools**. Create an application and save its `api_id` and `api_hash`.
You can choose the application title and short name yourself.

These are application credentials, not a BotFather token. Signing in to
my.telegram.org may require a Telegram verification code; signing in to
TelegramMCP below uses a QR code.

### 3. Prepare the container

In PowerShell, from the project directory, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

This creates the `.env` file, the `td_data` folder, and a Docker image. The first
build downloads dependencies and may take several minutes. Running it again does
not overwrite your existing `.env` or session. `ExecutionPolicy Bypass` applies
only to this PowerShell invocation.

Open the configuration file:

```powershell
notepad .env
```

Replace the placeholders with your values and save:

```dotenv
TG_API_ID=YOUR_API_ID
TG_API_HASH=YOUR_API_HASH
TG_DATABASE_DIR=/data
```

`TG_API_ID` must be a number. Leave `/data` unchanged: Docker maps this path to the
`td_data` folder next to the project files. Do not share `.env` with other people.

### 4. Sign in with a QR code

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\login-local.ps1
```

A QR code appears in the terminal. On your phone, open
**Telegram → Settings → Devices → Link Desktop Device** and scan it.
If the QR code does not fit, maximize the terminal or reduce its font size.
The code refreshes automatically. If two-step verification is enabled, the terminal
will ask for your Telegram password. Characters are not displayed while you type;
this is normal.

Wait for **Logged in as …**, then press Enter. Your session is saved, so you do not
need to scan the QR code every time. Do not delete the `td_data` folder.

### 5. Connect to Codex

If the `codex` command is available in your terminal, run this from the project directory:

```powershell
$launcher = (Resolve-Path .\start-mcp.ps1).Path
codex mcp add telegram -- powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher
```

Check that the server is registered:

```powershell
codex mcp get telegram
```

Restart Codex to load the tools. Keep Docker Desktop running.
Ask: **“Show my Telegram folders.”**

If `codex` is not found, use your application's MCP settings:

| Field | Value |
|---|---|
| Name | `telegram` |
| Type | `stdio` / local command |
| Command | `powershell.exe` |
| Arguments | `-NoProfile`, `-ExecutionPolicy`, `Bypass`, `-File`, the full path to `start-mcp.ps1` |

For clients that use a JSON `mcpServers` configuration, use the example below.
**Replace the path with your own.** Backslashes must be doubled in JSON:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "powershell.exe",
      "args": ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\Projects\\TelegramMCP\\start-mcp.ps1"]
    }
  }
}
```

Do not run `start-mcp.ps1` manually as a separate service: the MCP client launches it.
There is no web page or listening port; communication happens over stdio.

## Tools

| Tool | Purpose |
|---|---|
| `whoami` | Check the connected account |
| `list_chat_folders` | List folders, their names, IDs, icons, and order |
| `list_chats` | List chats from the main list, archive, or a selected folder |
| `read_chat` | Read recent messages in a selected chat |
| `search_chats` | Find chats by name; this does not search all message history |
| `resolve_chat` | Find a public chat by `@username` |
| `send_message` | Send a text message from your account |

Folders are sidebar tabs such as “Work” or “Personal”, not group conversations.
Call `list_chat_folders` first, then use a returned ID:
`list_chats(folder_id=ID, limit=100, offset=0)`. Use `offset=100` for the next page.
`limit` must be between 1 and 1000, `offset` must be nonnegative, and their sum must
not exceed 10000. A short page means the end of the list. The order may change as
messages arrive. A chat can belong to multiple folders. Telegram handles folder
filters and pinned chats.

Without selectors, `list_chats` returns the main list. `archived=True` selects the
archive; it cannot be combined with `folder_id`.

## Everyday use and updates

After restarting your computer, start Docker Desktop and your AI application.
Use **one active MCP instance per session directory**. Connecting several applications
at the same time can cause a TDLib database lock.

To update, close applications using this MCP server, then run:

```powershell
git pull --ff-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

Start your AI application again. If updating from a ZIP, preserve your `.env` and
`td_data` and replace only the program files. Stop MCP before backing up the session,
and protect the backup like a password. Do not add it to Git.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Docker daemon / engine unavailable | Start Docker Desktop and wait for its Linux engine |
| `TG_API_ID must be an integer` | Replace the placeholder in `.env` with the number from my.telegram.org |
| `API_ID_INVALID` or credential error | Check both values in `.env`; remove any spaces within them |
| QR expired or login took more than 10 minutes | Run `login-local.ps1` again and scan the new QR code |
| Password requested after scanning QR | Enter your Telegram two-step verification password, not an SMS code |
| `Can't lock file ... td.binlog` | Close the second MCP client or login window; do not delete the database |
| Tools do not appear | Check the full script path and restart the MCP client |
| Folders not loaded yet / timeout | Wait for Telegram to connect, then retry |
| `Unknown folder_id` | Retrieve the folder list again; the ID may have changed |
| Not all messages loaded | Retry; history reading currently covers recent messages only |
| Project directory moved | Update the absolute path in your MCP configuration |

Do not publish logs containing private conversations or credentials.
See [SECURITY.en.md](SECURITY.en.md). To revoke account access, terminate the
**tg-mcp** session in **Telegram → Settings → Devices**.
To remove the server registration from Codex, run `codex mcp remove telegram`.

## Linux and development

The primary tested setup is Windows x86-64 + Docker Desktop.
Linux x86-64 can use the same Docker image:

```bash
cp .env.example .env
# Fill .env with your credentials before continuing.
mkdir -p td_data
docker build -f Dockerfile.local -t mcptg-local:0.1 .
docker run --rm -it --env-file .env --mount "type=bind,source=$PWD/td_data,target=/data" mcptg-local:0.1 python scripts/login.py --qr
```

For MCP, use the same `docker run` command, replace `-it` with `-i`, and remove
`python scripts/login.py --qr`. Use absolute paths to `.env` and `td_data` in your
configuration. Running without Docker requires Python 3.10+ and a compatible TDLib:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e . qrcode==8.2
# Override the Docker example's TG_DATABASE_DIR with a local path.
export TG_DATABASE_DIR="$PWD/td_data"
export TDJSON_PATH="$PWD/lib/libtdjson.so"
python scripts/login.py --qr
python -m tg_mcp.server
```

The included `lib/libtdjson.so` targets Ubuntu 24.04 x86-64. Other platforms require
a compatible build. `scripts/build_tdlib.sh` builds TDLib from its official repository;
read the script and install its dependencies before running it. The included binary
is version 1.8.68; its exact source commit was not recorded in the original build.

Run tests without an account or credentials:

```bash
pip install -e .
python -m unittest discover -s scripts -p "test_*.py"
```

GitHub Actions runs the tests and checks that TDLib loads. Live testing requires
your own Telegram session; CI does not use one.

Project layout: `src/tg_mcp/client.py` handles connections and authentication;
`api.py` implements Telegram operations; `server.py` exposes MCP tools;
`tdjson.py` binds to TDLib; `scripts/` contains login, build, and test helpers.

## Limitations

Attachment downloads, full-history text search, folder editing, and secret chats
are not supported. Media are returned as short text descriptions. `read_chat` is
not a complete conversation archive export. Sending currently supports text only.
The server provides local stdio, not an HTTP endpoint.

## Roadmap and feedback

See the [roadmap](ROADMAP.md) for priorities and current boundaries. Report an
[installation problem, bug, or feature request](https://github.com/pborisovb-commits/TelegramMCP/issues/new/choose).
Do not include Telegram credentials, session files, or private messages in issues.

### Known lifecycle limitation

Each launcher invocation starts a new container. Multiple MCP client connections
can leave multiple server processes running, all pointing to the same session directory.
Use only one active connection per session. Stop the associated containers when
finished; disabling a client integration may not terminate existing processes.
Do not delete session files to resolve a database lock. Lifecycle management is a
priority in the roadmap.

Summaries are produced by your AI client using retrieved messages. Scheduled
summaries and CRM task creation are not built into this release. Local hosting of
the server does not mean messages stay on your machine: the AI client may send
retrieved content to its model provider.

## Author and licenses

The project author is **pborisovb**. TelegramMCP is distributed under the
[MIT License](LICENSE). Third-party dependencies retain their own licenses:
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) (in Russian).

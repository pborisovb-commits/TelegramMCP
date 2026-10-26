# Security

[Русский](../.github/SECURITY.md) | **English**

`.env` contains your Telegram application credentials, and `td_data/` grants access
to your account. Never publish these files, backups of the session folder, login
QR codes, verification codes, or your two-step verification password.
Use only fictional data in issue reports.

The MCP server acts as your account: `send_message` sends real messages.
Approve sending only after checking the recipient and message text. Connect the
server only to applications you trust. It uses stdio and does not expose a network
port; do not expose it through a tunnel without separate authentication.

To revoke access, terminate the **tg-mcp** session in
**Telegram → Settings → Devices**. If your session is leaked, revoke it first;
removing the file from Git is not enough. Do not clear `td_data` to fix a database
lock: stop the second server instance instead.

Report vulnerabilities using GitHub Private Vulnerability Reporting if it is
available for this repository. Never include live credentials in a public issue.

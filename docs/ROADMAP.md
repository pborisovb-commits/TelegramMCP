# Roadmap / План развития

These are priorities, not release dates or promises. Author and maintainer: **pborisovb**.
Это приоритеты, а не сроки или обещания выпуска.

## Available / Уже доступно

- Local MCP over stdio using official Telegram TDLib.
- QR authentication and saved sessions.
- Chat folders, folder-aware chat lists, chat lookup, recent message reading and text sending.
- Windows x86-64 + Docker setup, Russian and English instructions.

## Next / Ближайшие приоритеты

- [ ] Reliable startup and shutdown: prevent accidental competing processes using one session, handle disconnects, document cleanup without deleting data.
- [ ] Installation checks and clearer diagnostics for Docker, credentials and session locks.
- [ ] Repeatable clean-install and shutdown checks, including reconnect scenarios.
- [ ] Real, anonymized demo of folders, message retrieval and an AI-client-generated summary.

## Later / Следующий этап

- [ ] Read-only mode and clearer separation of read and send capabilities.
- [ ] Broader client/platform testing; publish a verified compatibility matrix.
- [ ] Reproducible TDLib builds with pinned source revision and published checksums.
- [ ] Evaluate packaged distribution and MCP Registry publication.

## Under consideration / На обсуждении

- Attachments and expanded history retrieval.
- Scheduled summaries and CRM integrations as separate, explicitly configured workflows.

Scheduled execution, CRM task creation, attachment downloads and full-history search
are **not current capabilities**. Existing client-side summaries are not a built-in scheduler.

Share your use case through a [feature request](https://github.com/pborisovb-commits/TelegramMCP/issues/new/choose).
Never attach credentials, Telegram session data or private conversations.

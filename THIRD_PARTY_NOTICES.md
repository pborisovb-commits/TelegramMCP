# Сторонние компоненты

Автор TelegramMCP — pborisovb. Перечисленные ниже компоненты являются отдельными
зависимостями и сохраняют собственные авторские права и лицензии.

- **TDLib**, Telegram Systems LLP: https://github.com/tdlib/td,
  Boost Software License 1.0 (текст: `licenses/TDLib-LICENSE.txt`).
  `lib/libtdjson.so` — готовая сборка TDLib 1.8.68 для Linux x86-64,
  проверенная в Ubuntu 24.04. Она перенесена из предыдущей версии проекта;
  точный исходный commit сборки в старой истории не записан. Это не независимо
  воспроизводимая сборка. Для сборки из исходников см. `scripts/build_tdlib.sh`.
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk, MIT.
  Устанавливается pip вместе с собственными зависимостями и лицензиями.
- **python-qrcode**: https://github.com/lincolnloop/python-qrcode, BSD.
  Устанавливается pip для вывода QR-кода.
- Docker-образ использует Ubuntu и системные библиотеки OpenSSL, zlib и другие.
  Их сведения о лицензиях доступны внутри образа в `/usr/share/doc/`.

Наличие этих зависимостей не означает, что Telegram или их разработчики являются
авторами, партнёрами или одобряют TelegramMCP.

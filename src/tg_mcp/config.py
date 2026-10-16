"""Configuration loaded from environment variables.

Required:
    TG_API_ID    - your api_id from https://my.telegram.org
    TG_API_HASH  - your api_hash from https://my.telegram.org

Optional:
    TG_DATABASE_DIR - directory for TDLib's session/database (default: ./td_data)
    TDJSON_PATH     - explicit path to libtdjson.so (otherwise auto-discovered)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    """Populate os.environ from a repo-root .env file (no third-party dep).

    Only sets keys that are not already present in the environment, so real
    environment variables always win. Both the canonical ``TG_API_ID`` /
    ``TG_API_HASH`` names and the short ``api_id`` / ``api_hash`` names (as
    created at https://my.telegram.org) are accepted.
    """
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    database_dir: str

    @staticmethod
    def from_env() -> "Config":
        _load_dotenv()
        api_id = os.environ.get("TG_API_ID") or os.environ.get("api_id")
        api_hash = os.environ.get("TG_API_HASH") or os.environ.get("api_hash")
        if not api_id or not api_hash:
            raise RuntimeError(
                "Set TG_API_ID/TG_API_HASH (or api_id/api_hash in .env) "
                "(get them from https://my.telegram.org)."
            )
        try:
            api_id_int = int(api_id)
        except ValueError as exc:
            raise RuntimeError("TG_API_ID must be an integer.") from exc
        return Config(
            api_id=api_id_int,
            api_hash=api_hash,
            database_dir=os.environ.get("TG_DATABASE_DIR", "td_data"),
        )

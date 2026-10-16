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


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    database_dir: str

    @staticmethod
    def from_env() -> "Config":
        api_id = os.environ.get("TG_API_ID")
        api_hash = os.environ.get("TG_API_HASH")
        if not api_id or not api_hash:
            raise RuntimeError(
                "Set TG_API_ID and TG_API_HASH (get them from https://my.telegram.org)."
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

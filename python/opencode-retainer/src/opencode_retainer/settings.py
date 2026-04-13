from __future__ import annotations

import os
from pathlib import Path


def env_first(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def default_state_path() -> Path:
    return ajtks_home() / "opencode-retainer" / "state.json"


def default_lock_path() -> Path:
    return ajtks_home() / "opencode-retainer" / "run.lock"


def ajtks_home() -> Path:
    value = os.environ.get("AJTKS_HOME")
    if value:
        return Path(value).expanduser()
    return Path.home() / ".ajtks"

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Self, cast

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class StateStore:
    path: Path
    data: dict[str, object]

    @classmethod
    def load(cls, path: Path) -> Self:
        expanded = path.expanduser()
        if not expanded.exists():
            return cls(path=expanded, data={"version": 1, "sessions": {}})
        loaded_value = cast("object", json.loads(expanded.read_text()))
        if not isinstance(loaded_value, dict):
            msg = f"State file is not a JSON object: {expanded}"
            raise TypeError(msg)
        loaded = cast("dict[str, object]", loaded_value)
        if not isinstance(loaded.get("version"), int):
            loaded["version"] = 1
        if not isinstance(loaded.get("sessions"), dict):
            loaded["sessions"] = {}
        return cls(path=expanded, data=loaded)

    def content_hash_for(self, session_id: str) -> str | None:
        record = self._session_record(session_id)
        value = record.get("content_hash")
        if isinstance(value, str):
            return value
        return None

    def mark_retained(
        self,
        *,
        session_id: str,
        content_hash: str,
    ) -> None:
        sessions = self._sessions()
        sessions[session_id] = {
            "content_hash": content_hash,
            "retained_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n")

    def _session_record(self, session_id: str) -> dict[str, object]:
        value = self._sessions().get(session_id)
        if isinstance(value, dict):
            return cast("dict[str, object]", value)
        return {}

    def _sessions(self) -> dict[str, object]:
        sessions = self.data.get("sessions")
        if not isinstance(sessions, dict):
            msg = "State field 'sessions' is not a JSON object."
            raise TypeError(msg)
        return cast("dict[str, object]", sessions)

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

OPENCODE_COMMAND_TIMEOUT_S = 5.0


@dataclass(frozen=True)
class TranscriptMessage:
    id: str
    role: str
    agent: str | None
    parent_id: str | None
    timestamp: str
    text: str

    def to_json(self) -> dict[str, str]:
        item = {
            "id": self.id,
            "role": self.role,
            "timestamp": self.timestamp,
            "text": self.text,
        }
        if self.agent:
            item["agent"] = self.agent
        if self.parent_id:
            item["parent_id"] = self.parent_id
        return item


@dataclass(frozen=True)
class SessionTranscript:
    id: str
    title: str
    directory: str
    project_id: str
    project_worktree: str | None
    project_name: str | None
    created_at: str
    updated_at: str
    messages: list[TranscriptMessage]

    def to_retain_content(self) -> str:
        return json.dumps(
            {
                "format": "opencode-session-transcript-v1",
                "session": {
                    "id": self.id,
                    "title": self.title,
                    "created_at": self.created_at,
                    "updated_at": self.updated_at,
                },
                "messages": [message.to_json() for message in self.messages],
            },
            ensure_ascii=False,
            indent=2,
        )


class OpenCodeStore:
    def __init__(self, database: Path) -> None:
        self._database = database.expanduser()

    @staticmethod
    def version() -> str:
        result = subprocess.run(
            ["opencode", "--version"],
            capture_output=True,
            check=True,
            text=True,
            timeout=OPENCODE_COMMAND_TIMEOUT_S,
        )
        return result.stdout.strip()

    def list_transcripts(
        self,
        *,
        session_ids: list[str],
        project: Path | None,
        limit: int | None,
    ) -> list[SessionTranscript]:
        with self._connect() as conn:
            sessions = self._fetch_sessions(
                conn,
                session_ids=session_ids,
                project=project,
                limit=limit,
            )
            return [
                transcript
                for transcript in (
                    self._build_transcript(conn, session) for session in sessions
                )
                if transcript.messages
            ]

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            f"file:{self._database}?mode=ro",
            uri=True,
            timeout=5.0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _fetch_sessions(
        self,
        conn: sqlite3.Connection,
        *,
        session_ids: list[str],
        project: Path | None,
        limit: int | None,
    ) -> list[sqlite3.Row]:
        query = [
            "SELECT s.*, p.worktree AS project_worktree, p.name AS project_name",
            "FROM session s",
            "LEFT JOIN project p ON p.id = s.project_id",
        ]
        where: list[str] = []
        params: list[object] = []
        if session_ids:
            placeholders = ",".join("?" for _ in session_ids)
            where.append(f"s.id IN ({placeholders})")
            params.extend(session_ids)
        if project:
            resolved = str(project.expanduser().resolve())
            where.append("(s.directory = ? OR p.worktree = ?)")
            params.extend([resolved, resolved])
        if where:
            query.append("WHERE " + " AND ".join(where))
        query.append("ORDER BY s.time_updated DESC")
        if limit is not None:
            query.append("LIMIT ?")
            params.append(limit)
        cursor = conn.execute(" ".join(query), params)
        return list(cursor.fetchall())

    def _build_transcript(
        self,
        conn: sqlite3.Connection,
        session: sqlite3.Row,
    ) -> SessionTranscript:
        parts_by_message = self._fetch_text_parts(conn, _row_str(session, "id"))
        messages: list[TranscriptMessage] = []
        for row in self._fetch_messages(conn, _row_str(session, "id")):
            message = _load_json_object(_row_str(row, "data"))
            text = "\n\n".join(parts_by_message.get(_row_str(row, "id"), []))
            if not text.strip():
                continue
            role = _message_str(message, "role") or "unknown"
            messages.append(
                TranscriptMessage(
                    id=_row_str(row, "id"),
                    role=role,
                    agent=_message_str(message, "agent"),
                    parent_id=_message_str(message, "parentID"),
                    timestamp=_iso_from_ms(_row_int(row, "time_created")),
                    text=text,
                )
            )
        return SessionTranscript(
            id=_row_str(session, "id"),
            title=_row_str(session, "title"),
            directory=_row_str(session, "directory"),
            project_id=_row_str(session, "project_id"),
            project_worktree=_row_optional_str(session, "project_worktree"),
            project_name=_row_optional_str(session, "project_name"),
            created_at=_iso_from_ms(_row_int(session, "time_created")),
            updated_at=_iso_from_ms(_row_int(session, "time_updated")),
            messages=messages,
        )

    def _fetch_messages(
        self,
        conn: sqlite3.Connection,
        session_id: str,
    ) -> list[sqlite3.Row]:
        cursor = conn.execute(
            """
            SELECT id, time_created, data
            FROM message
            WHERE session_id = ?
            ORDER BY time_created, id
            """,
            (session_id,),
        )
        return list(cursor.fetchall())

    def _fetch_text_parts(
        self,
        conn: sqlite3.Connection,
        session_id: str,
    ) -> dict[str, list[str]]:
        cursor = conn.execute(
            """
            SELECT message_id, data
            FROM part
            WHERE session_id = ?
            ORDER BY time_created, id
            """,
            (session_id,),
        )
        parts: dict[str, list[str]] = defaultdict(list)
        for row in cursor.fetchall():
            data = _load_json_object(_row_str(row, "data"))
            if data.get("type") != "text":
                continue
            text = data.get("text")
            if isinstance(text, str) and text.strip():
                parts[_row_str(row, "message_id")].append(text)
        return parts


def default_opencode_db_path() -> Path:
    try:
        result = subprocess.run(
            ["opencode", "db", "path"],
            capture_output=True,
            check=True,
            text=True,
            timeout=OPENCODE_COMMAND_TIMEOUT_S,
        )
    except OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired:
        pass
    else:
        path = result.stdout.strip()
        if path:
            return Path(path)

    xdg_data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return xdg_data_home / "opencode" / "opencode.db"


def _load_json_object(raw: str) -> dict[str, object]:
    value = cast("object", json.loads(raw))
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    return {}


def _message_str(message: dict[str, object], key: str) -> str | None:
    value = message.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _iso_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, UTC).isoformat().replace("+00:00", "Z")


def _row_str(row: sqlite3.Row, key: str) -> str:
    return cast("str", row[key])


def _row_optional_str(row: sqlite3.Row, key: str) -> str | None:
    return cast("str | None", row[key])


def _row_int(row: sqlite3.Row, key: str) -> int:
    return cast("int", row[key])

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from .hindsight import HindsightClient, RetainItem
from .lock import FileLock
from .opencodedb import OpenCodeStore, default_opencode_db_path
from .settings import default_lock_path, default_state_path, env_first
from .state import StateStore

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .opencodedb import SessionTranscript

DEFAULT_BASE_URL = "http://localhost:8888"
DEFAULT_BANK_ID = "openclaw"
SUPPORTED_OPENCODE_VERSION = "1.4.3"
RETAIN_CONTEXT = (
    "OpenCode assistant conversation transcript. Retain durable user "
    "preferences, project facts, technical decisions, implementation outcomes, "
    "constraints, blockers, and unresolved follow-ups. Treat user and assistant "
    "roles explicitly; assistant text is assistant-authored, not user-authored. "
    "Ignore tool traces, transient wording, and non-durable reasoning."
)


def main() -> None:
    console = Console()
    try:
        with FileLock(default_lock_path()) as acquired:
            if not acquired:
                console.print("Another opencode-retainer process is already running.")
                return
            _run(console)
    except Exception:
        console.print_exception(show_locals=True)
        raise SystemExit(1) from None


def _run(console: Console) -> None:
    args = _parse_args()
    if args.show_version:
        console.print(f"opencode-retainer {version('opencode-retainer')}")
        return

    _validate_opencode_version()

    store = OpenCodeStore(args.database)
    transcripts = store.list_transcripts(
        session_ids=args.session_id,
        project=args.project,
        limit=None if args.all else args.limit,
    )
    if not transcripts:
        console.print("No OpenCode sessions matched.")
        return

    state = StateStore.load(default_state_path())
    planned = _plan_retains(transcripts, state, force=args.force)
    _render_plan(console, planned)

    pending = [entry.item for entry in planned if entry.status == "send"]
    if not args.apply:
        console.print("Dry run only. Re-run with --apply to retain these sessions.")
        return
    if not pending:
        console.print("Nothing to retain.")
        return

    client = HindsightClient(
        base_url=args.base_url,
        bank_id=args.bank_id,
        api_key=args.api_key,
        timeout_s=args.timeout,
    )
    try:
        for batch in _batches(pending, args.batch_size):
            result = client.retain(batch, async_=not args.wait)
            operation_id = _operation_id(result.operation_id, result.operation_ids)
            for item in batch:
                state.mark_retained(
                    session_id=item.session_id,
                    content_hash=item.content_hash,
                )
            state.save()
            console.print(
                f"Retained {len(batch)} session(s): "
                f"async={result.var_async}, operation={operation_id or 'n/a'}"
            )
    finally:
        client.close()


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(
        prog="opencode-retainer",
        description="Retain OpenCode session transcripts into Hindsight.",
    )
    parser.add_argument("--version", action="store_true", dest="show_version")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--session-id", action="append", default=[])
    parser.add_argument("--project", type=Path)
    parser.add_argument("--database", type=Path, default=default_opencode_db_path())
    parser.add_argument(
        "--base-url",
        default=env_first("AJTKS_HINDSIGHT_BASE_URL") or DEFAULT_BASE_URL,
    )
    parser.add_argument(
        "--bank-id",
        default=env_first("AJTKS_HINDSIGHT_BANK_ID") or DEFAULT_BANK_ID,
    )
    parser.add_argument(
        "--api-key",
        default=env_first("AJTKS_HINDSIGHT_API_KEY"),
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args(namespace=Args())


class Args(argparse.Namespace):
    all: bool
    api_key: str | None
    apply: bool
    bank_id: str
    base_url: str
    batch_size: int
    database: Path
    force: bool
    limit: int
    project: Path | None
    session_id: list[str]
    show_version: bool
    timeout: float
    wait: bool


@dataclass
class PlanEntry:
    item: RetainItem
    status: str
    reason: str
    title: str
    message_count: int


def _plan_retains(
    transcripts: Sequence[SessionTranscript],
    state: StateStore,
    *,
    force: bool,
) -> list[PlanEntry]:
    entries: list[PlanEntry] = []
    for transcript in transcripts:
        item = _retain_item_from_transcript(transcript)
        previous_hash = state.content_hash_for(transcript.id)
        if previous_hash == item.content_hash and not force:
            status = "skip"
            reason = "unchanged"
        else:
            status = "send"
            reason = "forced" if force and previous_hash else "changed"
        entries.append(
            PlanEntry(
                item=item,
                status=status,
                reason=reason,
                title=transcript.title,
                message_count=len(transcript.messages),
            )
        )
    return entries


def _retain_item_from_transcript(transcript: SessionTranscript) -> RetainItem:
    content = transcript.to_retain_content()
    content_hash = RetainItem.hash_content(content)
    return RetainItem(
        session_id=transcript.id,
        document_id=f"opencode:session:{transcript.id}",
        content=content,
        content_hash=content_hash,
        context=RETAIN_CONTEXT,
        timestamp=transcript.updated_at,
    )


def _render_plan(console: Console, entries: Sequence[PlanEntry]) -> None:
    table = Table(title="OpenCode Retain Plan")
    table.add_column("status")
    table.add_column("messages", justify="right")
    table.add_column("chars", justify="right")
    table.add_column("hash")
    table.add_column("session")
    table.add_column("title")

    for entry in entries:
        item = entry.item
        table.add_row(
            f"{entry.status}:{entry.reason}",
            str(entry.message_count),
            str(len(item.content)),
            item.content_hash[:12],
            item.session_id,
            entry.title,
        )
    console.print(table)


def _batches(items: Sequence[RetainItem], size: int) -> list[list[RetainItem]]:
    batch_size = max(1, size)
    return [
        list(items[index : index + batch_size])
        for index in range(0, len(items), batch_size)
    ]


def _operation_id(operation_id: str | None, operation_ids: Sequence[str] | None) -> str:
    if operation_id:
        return operation_id
    if operation_ids:
        return ",".join(operation_ids)
    return ""


def _validate_opencode_version() -> None:
    actual = OpenCodeStore.version()
    if actual == SUPPORTED_OPENCODE_VERSION:
        return
    msg = (
        f"Unsupported OpenCode version: {actual}. "
        f"Expected {SUPPORTED_OPENCODE_VERSION}. "
        "Review the OpenCode DB reader before retaining memories from this version."
    )
    raise RuntimeError(msg)

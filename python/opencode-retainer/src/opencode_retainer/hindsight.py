from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from hindsight_client import Hindsight

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hindsight_client_api.models.retain_response import RetainResponse


@dataclass(frozen=True)
class RetainItem:
    session_id: str
    document_id: str
    content: str
    content_hash: str
    context: str
    timestamp: str

    @staticmethod
    def hash_content(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def to_request_item(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "context": self.context,
            "document_id": self.document_id,
            "timestamp": self.timestamp,
            "update_mode": "replace",
        }


class HindsightClient:
    def __init__(
        self,
        *,
        base_url: str,
        bank_id: str,
        api_key: str | None,
        timeout_s: float,
    ) -> None:
        self._bank_id = bank_id
        self._client = Hindsight(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout_s,
        )

    def close(self) -> None:
        self._client.close()

    def retain(
        self,
        items: Sequence[RetainItem],
        *,
        async_: bool,
    ) -> RetainResponse:
        return self._client.retain_batch(
            bank_id=self._bank_id,
            items=[item.to_request_item() for item in items],
            retain_async=async_,
        )

"""Read-only, minimised Zendesk ticket context for the refund-control pilot."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ZendeskContextError(ValueError):
    pass


@dataclass(frozen=True)
class ZendeskTicketContext:
    ticket_id: int
    status: str
    type: str | None
    priority: str | None
    requester_id: int | None
    organization_id: int | None
    tags: list[str]
    created_at: str | None
    updated_at: str | None


class ZendeskTransport(Protocol):
    def get(self, path: str, headers: dict[str, str]) -> dict[str, Any]: ...


class UrllibZendeskTransport:
    def __init__(self, subdomain: str, timeout_seconds: float = 10) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", subdomain):
            raise ValueError("Zendesk subdomain is invalid")
        self.base_url = f"https://{subdomain}.zendesk.com"
        self.timeout_seconds = timeout_seconds

    def get(self, path: str, headers: dict[str, str]) -> dict[str, Any]:
        try:
            with urlopen(Request(f"{self.base_url}{path}", headers=headers, method="GET"), timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed validated Zendesk host
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 404:
                raise ZendeskContextError("Zendesk ticket was not found") from error
            raise ZendeskContextError("Zendesk did not allow ticket context retrieval") from error
        except (TimeoutError, URLError) as error:
            raise ZendeskContextError("Zendesk ticket context could not be retrieved; do not proceed with a refund from stale context") from error


class ZendeskTicketContextProvider:
    """Fetch only policy-relevant ticket metadata; never comments or attachments."""

    def __init__(self, oauth_access_token: str, transport: ZendeskTransport) -> None:
        if not oauth_access_token.strip():
            raise ValueError("Zendesk OAuth access token is required")
        self._oauth_access_token = oauth_access_token
        self._transport = transport

    def fetch(self, ticket_id: int) -> ZendeskTicketContext:
        if ticket_id <= 0:
            raise ZendeskContextError("Zendesk ticket ID must be positive")
        payload = self._transport.get(f"/api/v2/tickets/{ticket_id}.json", {"Authorization": f"Bearer {self._oauth_access_token}"})
        ticket = payload.get("ticket")
        if not isinstance(ticket, dict):
            raise ZendeskContextError("Zendesk returned an invalid ticket response")
        # Deliberately omit subject, description, comments, attachments, email,
        # and custom fields. The action request needs only stable case metadata.
        return ZendeskTicketContext(
            ticket_id=int(ticket.get("id", ticket_id)), status=str(ticket.get("status", "unknown")),
            type=str(ticket["type"]) if ticket.get("type") is not None else None,
            priority=str(ticket["priority"]) if ticket.get("priority") is not None else None,
            requester_id=int(ticket["requester_id"]) if ticket.get("requester_id") is not None else None,
            organization_id=int(ticket["organization_id"]) if ticket.get("organization_id") is not None else None,
            tags=[str(tag) for tag in ticket.get("tags", []) if isinstance(tag, str)],
            created_at=str(ticket["created_at"]) if ticket.get("created_at") is not None else None,
            updated_at=str(ticket["updated_at"]) if ticket.get("updated_at") is not None else None,
        )

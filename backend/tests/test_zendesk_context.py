from app.services.zendesk_context import ZendeskContextError, ZendeskTicketContextProvider


class FakeZendeskTransport:
    def __init__(self) -> None:
        self.path = ""
        self.headers: dict[str, str] = {}

    def get(self, path: str, headers: dict[str, str]):
        self.path, self.headers = path, headers
        return {"ticket": {"id": 10482, "status": "open", "type": "incident", "priority": "high", "requester_id": 17, "organization_id": 9, "tags": ["outage", "refund-review"], "subject": "Sensitive customer message", "description": "Do not retain this", "created_at": "2026-09-15T10:00:00Z", "updated_at": "2026-09-15T10:05:00Z"}}


def test_zendesk_ticket_context_is_read_only_and_minimised():
    transport = FakeZendeskTransport()
    context = ZendeskTicketContextProvider("oauth-not-real", transport).fetch(10482)
    assert transport.path == "/api/v2/tickets/10482.json"
    assert transport.headers["Authorization"] == "Bearer oauth-not-real"
    assert context.ticket_id == 10482
    assert context.tags == ["outage", "refund-review"]
    assert not hasattr(context, "subject")
    assert not hasattr(context, "description")


def test_zendesk_ticket_context_rejects_invalid_id_without_network():
    try:
        ZendeskTicketContextProvider("oauth-not-real", FakeZendeskTransport()).fetch(0)
    except ZendeskContextError as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("expected invalid ticket ID to fail")

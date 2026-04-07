"""Composio client wrapper for event agency skills.

Provides a clean interface over the Composio SDK for common operations
used across all event agency skills: Gmail, Calendar, Sheets, Docs, Drive.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class EmailThread:
    """Parsed email thread from Gmail."""

    thread_id: str
    message_id: str
    subject: str
    sender_name: str
    sender_email: str
    sender_domain: str
    snippet: str
    body_preview: str
    date: str
    labels: list[str]
    is_unread: bool


@dataclass
class CalendarEvent:
    """Parsed calendar event."""

    event_id: str
    summary: str
    start: str
    end: str
    location: str | None
    attendees: list[str]
    description: str | None


class EventComposioClient:
    """Shared Composio client for event agency skills.

    Usage:
        client = EventComposioClient()
        emails = client.fetch_emails(query="Summit 2026", max_results=50)
    """

    def __init__(self, user_id: str = "default"):
        try:
            from composio import Composio
        except ImportError:
            print(
                "composio package not installed. Run: pip install composio",
                file=sys.stderr,
            )
            sys.exit(1)

        api_key = os.environ.get("COMPOSIO_API_KEY")
        if not api_key:
            print(
                "COMPOSIO_API_KEY environment variable required.\n"
                "Get yours at: https://platform.composio.dev/settings",
                file=sys.stderr,
            )
            sys.exit(1)

        self._composio = Composio(api_key=api_key)
        self._session = self._composio.create(user_id=user_id)
        self.user_id = user_id

    def _execute(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a Composio action and return the result."""
        result = self._session.execute_tool(
            action=action,
            params=params,
        )
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(f"Composio action {action} failed: {result['error']}")
        return result

    # ── Gmail ─────────────────────────────────────────────────────────

    def fetch_emails(
        self,
        query: str,
        max_results: int = 50,
        label: str = "INBOX",
    ) -> list[dict[str, Any]]:
        """Fetch emails matching a Gmail search query."""
        return self._execute(
            "GMAIL_FETCH_EMAILS",
            {
                "query": query,
                "max_results": max_results,
                "label": label,
            },
        )

    def read_thread(self, thread_id: str) -> dict[str, Any]:
        """Read full thread by thread ID."""
        return self._execute(
            "GMAIL_FETCH_MESSAGE_BY_THREAD_ID",
            {"thread_id": thread_id},
        )

    def read_message(self, message_id: str) -> dict[str, Any]:
        """Read a single message by ID."""
        return self._execute(
            "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
            {"message_id": message_id},
        )

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        is_html: bool = False,
    ) -> dict[str, Any]:
        """Create a Gmail draft."""
        params: dict[str, Any] = {
            "recipient_email": to,
            "subject": subject,
            "body": body,
            "user_id": "me",
        }
        if cc:
            params["cc"] = [cc] if isinstance(cc, str) else cc
        if bcc:
            params["bcc"] = [bcc] if isinstance(bcc, str) else bcc
        if is_html:
            params["is_html"] = True
        return self._execute("GMAIL_CREATE_EMAIL_DRAFT", params)

    def send_draft(self, draft_id: str) -> dict[str, Any]:
        """Send an existing draft. Use with caution — Tier 3 operation."""
        return self._execute("GMAIL_SEND_DRAFT", {"draft_id": draft_id})

    def list_labels(self) -> list[dict[str, Any]]:
        """List all Gmail labels."""
        return self._execute("GMAIL_LIST_LABELS", {})

    # ── Google Calendar ───────────────────────────────────────────────

    def list_events(
        self,
        days: int = 14,
        query: str | None = None,
        calendar_id: str = "primary",
    ) -> list[dict[str, Any]]:
        """List upcoming calendar events."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(tz=timezone.utc)
        time_max = now + timedelta(days=days)

        params: dict[str, Any] = {
            "calendar_id": calendar_id,
            "time_min": now.isoformat(),
            "time_max": time_max.isoformat(),
        }
        if query:
            params["query"] = query
        return self._execute("GOOGLECALENDAR_EVENTS_LIST", params)

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Create a calendar event. Tier 2 — requires confirmation."""
        params: dict[str, Any] = {
            "calendar_id": calendar_id,
            "summary": summary,
            "start": start,
            "end": end,
        }
        if description:
            params["description"] = description
        if location:
            params["location"] = location
        if attendees:
            params["attendees"] = attendees
        return self._execute("GOOGLECALENDAR_CREATE_EVENT", params)

    # ── Google Sheets ─────────────────────────────────────────────────

    def read_spreadsheet(
        self,
        spreadsheet_id: str,
        range_name: str = "Sheet1",
    ) -> list[list[str]]:
        """Read data from a Google Sheets spreadsheet."""
        result = self._execute(
            "GOOGLESHEETS_BATCH_GET",
            {
                "spreadsheet_id": spreadsheet_id,
                "ranges": range_name,
            },
        )
        return result

    def update_cells(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: list[list[str]],
    ) -> dict[str, Any]:
        """Update cells in a spreadsheet. Tier 2 — requires confirmation."""
        return self._execute(
            "GOOGLESHEETS_BATCH_UPDATE",
            {
                "spreadsheet_id": spreadsheet_id,
                "range": range_name,
                "values": values,
            },
        )

    def append_rows(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: list[list[str]],
    ) -> dict[str, Any]:
        """Append rows to a spreadsheet. Tier 2 — requires confirmation."""
        return self._execute(
            "GOOGLESHEETS_BATCH_UPDATE",
            {
                "spreadsheet_id": spreadsheet_id,
                "range": range_name,
                "values": values,
                "append": True,
            },
        )

    # ── Google Docs ───────────────────────────────────────────────────

    def create_document(
        self,
        title: str,
        body: str | None = None,
    ) -> dict[str, Any]:
        """Create a Google Doc. Tier 2 — requires confirmation."""
        params: dict[str, Any] = {"title": title}
        if body:
            params["body"] = body
        return self._execute("GOOGLEDOCS_CREATE_DOCUMENT", params)

    # ── Google Drive ──────────────────────────────────────────────────

    def upload_file(
        self,
        file_path: str,
        folder_id: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Upload file to Drive. Tier 2 — requires confirmation."""
        params: dict[str, Any] = {"file_path": file_path}
        if folder_id:
            params["folder_id"] = folder_id
        if name:
            params["name"] = name
        return self._execute("GOOGLEDRIVE_UPLOAD_FILE", params)

    def list_files(
        self,
        query: str | None = None,
        folder_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List files in Drive."""
        params: dict[str, Any] = {}
        if query:
            params["query"] = query
        if folder_id:
            params["folder_id"] = folder_id
        return self._execute("GOOGLEDRIVE_LIST_FILES", params)

    # ── HubSpot ───────────────────────────────────────────────────────

    def hubspot_search_contacts(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search HubSpot contacts."""
        return self._execute(
            "HUBSPOT_SEARCH_CONTACTS_BY_CRITERIA",
            {"query": query, "limit": limit},
        )

    def hubspot_create_contact(
        self, email: str, properties: dict[str, str]
    ) -> dict[str, Any]:
        """Create a HubSpot contact. Tier 2 — requires confirmation."""
        return self._execute(
            "HUBSPOT_CREATE_CONTACT",
            {"email": email, "properties": properties},
        )

    def hubspot_create_deal(
        self, name: str, properties: dict[str, str]
    ) -> dict[str, Any]:
        """Create a HubSpot deal. Tier 2 — requires confirmation."""
        return self._execute(
            "HUBSPOT_CREATE_DEAL",
            {"dealname": name, "properties": properties},
        )

    # ── Mailchimp ─────────────────────────────────────────────────────

    def mailchimp_list_audiences(self) -> list[dict[str, Any]]:
        """List Mailchimp audiences/lists."""
        return self._execute("MAILCHIMP_LIST_AUDIENCES", {})

    def mailchimp_add_subscriber(
        self,
        list_id: str,
        email: str,
        merge_fields: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Add subscriber to Mailchimp audience. Tier 2."""
        params: dict[str, Any] = {"list_id": list_id, "email_address": email}
        if merge_fields:
            params["merge_fields"] = merge_fields
        return self._execute("MAILCHIMP_ADD_CONTACT_TO_AUDIENCE", params)

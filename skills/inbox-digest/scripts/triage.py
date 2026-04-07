from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.composio_client import EventComposioClient
from lib.event_context import (
    EventContext,
    EventPhase,
    PriorityTier,
    StakeholderType,
    assign_priority,
    classify_stakeholder,
    extract_dates,
    has_deadline_signals,
)


RANGE_WINDOWS: dict[str, timedelta] = {
    "24h": timedelta(hours=24),
    "48h": timedelta(hours=48),
    "72h": timedelta(hours=72),
    "1w": timedelta(weeks=1),
}

RANGE_QUERY_SUFFIXES: dict[str, str] = {
    "24h": "newer_than:1d",
    "48h": "newer_than:2d",
    "72h": "newer_than:3d",
    "1w": "newer_than:7d",
}

STAKEHOLDER_SORT_ORDER: dict[StakeholderType, int] = {
    StakeholderType.VENUE: 0,
    StakeholderType.CLIENT: 1,
    StakeholderType.VENDOR: 2,
    StakeholderType.SPONSOR: 3,
    StakeholderType.SPEAKER: 4,
    StakeholderType.INTERNAL: 5,
    StakeholderType.UNKNOWN: 6,
}

IMMEDIATE_KEYWORDS = {
    "urgent",
    "asap",
    "immediately",
    "critical",
    "deadline",
    "cancellation",
    "cancel",
    "delay",
    "delayed",
    "safety",
    "compliance",
    "insurance",
    "coi",
    "load-in",
    "load in",
    "rider",
    "delivery",
    "delivery window",
    "confirmation needed",
}

QUESTION_SIGNALS = (
    "?",
    "can you",
    "could you",
    "please confirm",
    "let us know",
    "what is the status",
    "awaiting your",
)


@dataclass(slots=True)
class TriageThread:
    thread_id: str
    message_id: str
    subject: str
    sender_name: str
    sender_email: str
    sender_domain: str
    sender_display: str
    body_preview: str
    snippet: str
    date: datetime
    date_raw: str
    labels: list[str]
    is_unread: bool
    stakeholder: StakeholderType
    priority: PriorityTier
    age_hours: float
    age_label: str
    stale: bool
    stale_threshold_hours: int
    status_note: str
    action_needed: str
    recommended_action: str
    extracted_dates: list[str]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["date"] = self.date.isoformat()
        payload["stakeholder"] = self.stakeholder.value
        payload["priority"] = priority_label(self.priority)
        return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an event inbox triage digest from Gmail via Composio.")
    parser.add_argument("--event", required=True, help="Event name used in the Gmail search query.")
    parser.add_argument(
        "--date",
        required=True,
        type=parse_event_date,
        help="Event date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--range",
        dest="time_range",
        default="24h",
        choices=tuple(RANGE_WINDOWS),
        help="Lookback window for the inbox digest.",
    )
    parser.add_argument(
        "--domains",
        help="Comma-separated sender domains to keep after fetch.",
    )
    parser.add_argument(
        "--output",
        help="Output file path or directory. Defaults to stdout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the Gmail query and filters without calling Composio.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of markdown.",
    )
    return parser.parse_args(argv)


def parse_event_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must be in YYYY-MM-DD format") from exc


def parse_domain_filters(value: str | None) -> list[str]:
    if not value:
        return []
    return sorted(
        {
            domain.strip().lower().lstrip("@")
            for domain in value.split(",")
            if domain.strip()
        }
    )


def build_query(event_name: str, time_range: str) -> str:
    return f'"{event_name}" {RANGE_QUERY_SUFFIXES[time_range]}'


def unwrap_composio_payload(value: Any) -> Any:
    current = value
    while True:
        if isinstance(current, str):
            text = current.strip()
            if not text:
                return ""
            if text.startswith("{") or text.startswith("["):
                try:
                    current = json.loads(text)
                    continue
                except json.JSONDecodeError:
                    return current
            return current

        if isinstance(current, dict):
            if current.get("error"):
                return current
            if "data" in current:
                next_value = current.get("data")
                if next_value is current:
                    return current
                current = next_value
                continue
            return current

        return current


def extract_message_collection(value: Any) -> list[dict[str, Any]]:
    unwrapped = unwrap_composio_payload(value)
    if isinstance(unwrapped, list):
        return [item for item in unwrapped if isinstance(item, dict)]

    if isinstance(unwrapped, dict):
        if any(key in unwrapped for key in ("messageId", "message_id", "threadId", "thread_id", "id")):
            return [unwrapped]

        for key in ("messages", "emails", "threads", "items", "results"):
            candidate = unwrapped.get(key)
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]

        for nested in unwrapped.values():
            if isinstance(nested, (list, dict, str)):
                candidate = extract_message_collection(nested)
                if candidate:
                    return candidate

    return []


def header_map(payload: Any) -> dict[str, str]:
    headers = payload.get("headers", []) if isinstance(payload, dict) else []
    mapped: dict[str, str] = {}
    for header in headers:
        if isinstance(header, dict):
            name = str(header.get("name", "")).lower()
            value = str(header.get("value", "")).strip()
            if name and value:
                mapped[name] = value
    return mapped


def decode_base64url(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    padding = "=" * (-len(text) % 4)
    try:
        decoded = base64.urlsafe_b64decode(f"{text}{padding}")
        return decoded.decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return ""


def strip_html(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", without_tags).strip()


def extract_payload_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""

    body = payload.get("body")
    if isinstance(body, dict):
        data = body.get("data")
        if isinstance(data, str):
            decoded = decode_base64url(data)
            if decoded:
                mime_type = str(payload.get("mimeType", "")).lower()
                return strip_html(decoded) if "html" in mime_type else decoded.strip()

    parts = payload.get("parts")
    if isinstance(parts, list):
        for part in parts:
            extracted = extract_payload_text(part)
            if extracted:
                return extracted

    return ""


def parse_datetime_value(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)

    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 1_000_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, tz=UTC)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return parse_datetime_value(int(text))

        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            pass

        try:
            parsed = parsedate_to_datetime(text)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except (TypeError, ValueError, IndexError):
            return None

    return None


def first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def parse_sender_details(item: dict[str, Any], headers: dict[str, str]) -> tuple[str, str, str]:
    sender_name = first_text(item.get("sender_name"), item.get("senderName"), item.get("from_name"))
    sender_email = first_text(item.get("sender_email"), item.get("senderEmail"), item.get("email"), item.get("from_email"))
    source = first_text(item.get("from"), item.get("sender"), headers.get("from"))

    parsed_name, parsed_email = parseaddr(source)
    final_email = sender_email or parsed_email
    final_name = sender_name or parsed_name
    domain = extract_domain(final_email or source)
    return final_name.strip(), final_email.strip().lower(), domain


def extract_domain(value: str) -> str:
    _, email_address = parseaddr(value)
    candidate = email_address or value
    if "@" not in candidate:
        return ""
    return candidate.rsplit("@", 1)[-1].strip().lower()


def hydrate_message(item: dict[str, Any], client: EventComposioClient | None) -> dict[str, Any]:
    if client is None:
        return item

    needs_hydration = not all(
        [
            item.get("subject") or header_map(item.get("payload", {})).get("subject"),
            item.get("from") or header_map(item.get("payload", {})).get("from"),
            item.get("date") or item.get("internalDate") or header_map(item.get("payload", {})).get("date"),
        ]
    )
    if not needs_hydration:
        return item

    message_id = first_text(item.get("messageId"), item.get("message_id"), item.get("id"))
    if not message_id:
        return item

    try:
        detail = unwrap_composio_payload(client.read_message(message_id))
    except Exception:
        return item

    if isinstance(detail, dict):
        merged = dict(detail)
        merged.setdefault("messageId", message_id)
        merged.setdefault("threadId", first_text(item.get("threadId"), item.get("thread_id")))
        for key, value in item.items():
            merged.setdefault(key, value)
        return merged

    return item


def normalize_thread(item: dict[str, Any], client: EventComposioClient | None, now: datetime) -> TriageThread | None:
    hydrated = hydrate_message(item, client)
    payload_value = unwrap_composio_payload(hydrated.get("payload"))
    payload = payload_value if isinstance(payload_value, dict) else {}
    headers = header_map(payload)

    sender_name, sender_email, sender_domain = parse_sender_details(hydrated, headers)
    subject = first_text(hydrated.get("subject"), headers.get("subject"))
    snippet = first_text(hydrated.get("snippet"), hydrated.get("preview"), hydrated.get("summary"))
    body_preview = first_text(
        hydrated.get("body_preview"),
        hydrated.get("bodyPreview"),
        hydrated.get("body"),
        snippet,
        extract_payload_text(payload),
    )
    thread_id = first_text(hydrated.get("threadId"), hydrated.get("thread_id"))
    message_id = first_text(hydrated.get("messageId"), hydrated.get("message_id"), hydrated.get("id"))
    date_raw = first_text(
        hydrated.get("date"),
        hydrated.get("receivedAt"),
        hydrated.get("received_at"),
        hydrated.get("internalDate"),
        hydrated.get("internal_date"),
        headers.get("date"),
    )
    parsed_date = parse_datetime_value(date_raw)
    if parsed_date is None:
        return None

    labels = as_string_list(hydrated.get("labelIds")) or as_string_list(hydrated.get("labels"))
    is_unread = "UNREAD" in {label.upper() for label in labels} or bool(hydrated.get("isUnread") or hydrated.get("is_unread"))

    if not subject:
        subject = "(no subject)"

    sender_display = sender_name or sender_email or sender_domain or "Unknown sender"
    age_hours = max((now - parsed_date).total_seconds() / 3600, 0.0)
    text_for_rules = f"{subject} {body_preview}".strip()

    stakeholder = classify_stakeholder(
        sender_email=sender_email or sender_display,
        sender_name=sender_name,
        subject=subject,
        body_preview=body_preview,
    )

    return TriageThread(
        thread_id=thread_id or message_id,
        message_id=message_id,
        subject=subject,
        sender_name=sender_name,
        sender_email=sender_email,
        sender_domain=sender_domain,
        sender_display=sender_display,
        body_preview=body_preview,
        snippet=snippet,
        date=parsed_date,
        date_raw=date_raw,
        labels=labels,
        is_unread=is_unread,
        stakeholder=stakeholder,
        priority=PriorityTier.TRACKING,
        age_hours=age_hours,
        age_label=format_age(age_hours),
        stale=False,
        stale_threshold_hours=0,
        status_note="",
        action_needed="",
        recommended_action="",
        extracted_dates=extract_dates(text_for_rules),
    )


def apply_priority_overrides(thread: TriageThread, event_context: EventContext) -> PriorityTier:
    base_priority = assign_priority(
        stakeholder=thread.stakeholder,
        subject=thread.subject,
        body_preview=thread.body_preview,
        thread_age_hours=thread.age_hours,
        event_context=event_context,
    )

    priority = base_priority

    if thread.stale:
        priority = escalate_priority(priority)

    if thread.stakeholder == StakeholderType.VENDOR and event_context.phase == EventPhase.ADVANCE:
        priority = escalate_priority(priority)

    if event_context.phase == EventPhase.LOAD_IN and thread.stakeholder in {StakeholderType.VENDOR, StakeholderType.VENUE}:
        priority = PriorityTier.IMMEDIATE

    if event_context.phase == EventPhase.SHOW_DAY:
        if thread.stakeholder in {StakeholderType.VENDOR, StakeholderType.VENUE}:
            priority = PriorityTier.IMMEDIATE
        elif thread.stakeholder in {StakeholderType.CLIENT, StakeholderType.INTERNAL}:
            priority = min_priority(priority, PriorityTier.TODAY)

    if priority == PriorityTier.TRACKING:
        text = f"{thread.subject} {thread.body_preview}".lower()
        if has_deadline_signals(text) or thread.extracted_dates:
            priority = PriorityTier.TODAY

    return priority


def escalate_priority(priority: PriorityTier) -> PriorityTier:
    if priority == PriorityTier.TRACKING:
        return PriorityTier.TODAY
    return PriorityTier.IMMEDIATE


def min_priority(current: PriorityTier, minimum: PriorityTier) -> PriorityTier:
    return current if current.value <= minimum.value else minimum


def priority_label(priority: PriorityTier) -> str:
    return {
        PriorityTier.IMMEDIATE: "Immediate",
        PriorityTier.TODAY: "Today",
        PriorityTier.TRACKING: "Tracking",
    }[priority]


def stakeholder_label(stakeholder: StakeholderType) -> str:
    return stakeholder.value.title()


def format_age(hours: float) -> str:
    if hours >= 48:
        return f"{hours / 24:.1f}d"
    if hours >= 1:
        return f"{hours:.1f}h"
    return f"{round(hours * 60)}m"


def stale_header_threshold(event_context: EventContext) -> int:
    if event_context.phase == EventPhase.SHOW_DAY:
        return 1
    if event_context.phase == EventPhase.LOAD_IN:
        return 4
    if event_context.phase == EventPhase.ADVANCE:
        return 12
    return 24


def compute_thread_metadata(thread: TriageThread, event_context: EventContext) -> TriageThread:
    thread.stale_threshold_hours = event_context.stale_threshold_hours(thread.stakeholder)
    thread.stale = thread.age_hours >= thread.stale_threshold_hours
    thread.priority = apply_priority_overrides(thread, event_context)
    thread.status_note = build_status_note(thread, event_context)
    thread.action_needed = build_action_needed(thread, event_context)
    thread.recommended_action = build_recommended_action(thread, event_context)
    return thread


def build_status_note(thread: TriageThread, event_context: EventContext) -> str:
    if thread.stale:
        return f"Stale at {thread.stale_threshold_hours}h threshold; {build_recommended_action(thread, event_context)}"

    text = f"{thread.subject} {thread.body_preview}".lower()
    if any(signal in text for signal in QUESTION_SIGNALS):
        return "Awaiting a direct answer or confirmation"
    if has_deadline_signals(text):
        if thread.extracted_dates:
            return f"Deadline language detected; watch {thread.extracted_dates[0]}"
        return "Deadline language detected; review today"
    if thread.is_unread:
        return "Unread thread; review and route"

    return {
        StakeholderType.VENDOR: "Operational thread; confirm details and next steps",
        StakeholderType.CLIENT: "Client-facing thread; send status or confirmation",
        StakeholderType.VENUE: "Venue dependency; acknowledge and track logistics",
        StakeholderType.SPONSOR: "Monitor for asset or approval follow-up",
        StakeholderType.SPEAKER: "Track speaker logistics and materials",
        StakeholderType.INTERNAL: "Internal coordination; no immediate action",
        StakeholderType.UNKNOWN: "Review manually and classify",
    }[thread.stakeholder]


def build_action_needed(thread: TriageThread, event_context: EventContext) -> str:
    if thread.stale:
        return build_recommended_action(thread, event_context)

    text = f"{thread.subject} {thread.body_preview}".lower()
    if thread.stakeholder == StakeholderType.CLIENT and any(signal in text for signal in QUESTION_SIGNALS):
        return "Reply to the client question and confirm next step"
    if thread.stakeholder == StakeholderType.VENDOR and any(keyword in text for keyword in ("load-in", "load in", "rider", "delivery", "install", "compliance")):
        return "Confirm vendor logistics and close open production details"
    if thread.stakeholder == StakeholderType.VENUE:
        return "Confirm venue requirement and unblock dependent vendors"
    if any(keyword in text for keyword in IMMEDIATE_KEYWORDS):
        return "Respond immediately and resolve the blocker"
    if has_deadline_signals(text):
        if thread.extracted_dates:
            return f"Answer before {thread.extracted_dates[0]}"
        return "Confirm timing and respond today"

    return {
        StakeholderType.VENDOR: "Review and respond within business hours",
        StakeholderType.CLIENT: "Send a same-day status update",
        StakeholderType.VENUE: "Acknowledge and confirm logistics today",
        StakeholderType.SPONSOR: "Review deliverable status today",
        StakeholderType.SPEAKER: "Review logistics and route to production",
        StakeholderType.INTERNAL: "Monitor and route internally",
        StakeholderType.UNKNOWN: "Review manually and assign an owner",
    }[thread.stakeholder]


def build_recommended_action(thread: TriageThread, event_context: EventContext) -> str:
    if not thread.stale:
        return build_action_needed(thread, event_context)

    if thread.stakeholder == StakeholderType.VENDOR:
        if event_context.phase in {EventPhase.LOAD_IN, EventPhase.SHOW_DAY}:
            return "Call the vendor account manager now"
        return "Send follow-up and request a firm ETA"
    if thread.stakeholder == StakeholderType.CLIENT:
        return "Send a warm follow-up that restates the ask"
    if thread.stakeholder == StakeholderType.VENUE:
        return "Escalate to production lead and copy venue sales manager"
    if thread.stakeholder == StakeholderType.SPEAKER:
        return "Follow up with the speaker or bureau directly"
    if thread.stakeholder == StakeholderType.INTERNAL:
        return "Ping the owner in Slack or project chat"
    if thread.stakeholder == StakeholderType.SPONSOR:
        return "Check sponsor deliverable status and confirm next checkpoint"
    return "Review manually and assign an escalation owner"


def filter_by_domains(threads: list[TriageThread], domains: list[str]) -> list[TriageThread]:
    if not domains:
        return threads
    allowed = set(domains)
    return [thread for thread in threads if thread.sender_domain in allowed]


def sort_threads(threads: list[TriageThread]) -> list[TriageThread]:
    return sorted(
        threads,
        key=lambda thread: (
            STAKEHOLDER_SORT_ORDER.get(thread.stakeholder, 99),
            -thread.age_hours,
            thread.sender_display.lower(),
            thread.subject.lower(),
        ),
    )


def render_markdown(
    event_name: str,
    time_range: str,
    event_context: EventContext,
    generated_at: datetime,
    threads: list[TriageThread],
) -> str:
    immediate = sort_threads([thread for thread in threads if thread.priority == PriorityTier.IMMEDIATE])
    today = sort_threads([thread for thread in threads if thread.priority == PriorityTier.TODAY])
    tracking = sort_threads([thread for thread in threads if thread.priority == PriorityTier.TRACKING])
    stale = sort_threads([thread for thread in threads if thread.stale])

    lines = [
        f"# Inbox Digest — {event_name}",
        f"Generated: {generated_at.isoformat(timespec='seconds')}",
        f"Period: Last {time_range}",
        f"Phase: {event_context.phase_label}",
        f"Threads: {len(immediate)} Immediate · {len(today)} Today · {len(tracking)} Tracking · {len(stale)} Stale",
        "",
        "## Tier 1 — Immediate Action Required",
        "| Sender | Type | Subject | Action Needed | Age |",
        "|--------|------|---------|---------------|-----|",
    ]

    if immediate:
        lines.extend(
            f"| {escape_cell(thread.sender_display)} | {stakeholder_label(thread.stakeholder)} | {escape_cell(thread.subject)} | {escape_cell(thread.action_needed)} | {thread.age_label} |"
            for thread in immediate
        )
    else:
        lines.append("| — | — | — | No immediate-action threads in scope | — |")

    lines.extend(
        [
            "",
            "## Tier 2 — Action Today",
            "| Sender | Type | Subject | Status | Age |",
            "|--------|------|---------|--------|-----|",
        ]
    )

    if today:
        lines.extend(
            f"| {escape_cell(thread.sender_display)} | {stakeholder_label(thread.stakeholder)} | {escape_cell(thread.subject)} | {escape_cell(thread.status_note)} | {thread.age_label} |"
            for thread in today
        )
    else:
        lines.append("| — | — | — | No same-day threads in scope | — |")

    lines.extend(["", "## Tier 3 — Tracking"])
    if tracking:
        lines.extend(
            f"- {escape_inline(thread.sender_display)} — {escape_inline(thread.subject)} _({escape_inline(thread.status_note)})_"
            for thread in tracking
        )
    else:
        lines.append("- No tracking threads in scope")

    lines.extend(
        [
            "",
            f"## Stale Threads — No Reply {stale_header_threshold(event_context)}h+",
            "| Thread | Type | Age | Recommended Action |",
            "|--------|------|-----|--------------------|",
        ]
    )

    if stale:
        lines.extend(
            f"| {escape_cell(f'{thread.sender_display} — {thread.subject}')} | {stakeholder_label(thread.stakeholder)} | {thread.age_label} | {escape_cell(thread.recommended_action)} |"
            for thread in stale
        )
    else:
        lines.append("| — | — | — | No stale threads detected |")

    return "\n".join(lines)


def build_json_output(
    event_name: str,
    time_range: str,
    domains: list[str],
    event_context: EventContext,
    generated_at: datetime,
    query: str,
    threads: list[TriageThread],
) -> dict[str, Any]:
    immediate = sort_threads([thread for thread in threads if thread.priority == PriorityTier.IMMEDIATE])
    today = sort_threads([thread for thread in threads if thread.priority == PriorityTier.TODAY])
    tracking = sort_threads([thread for thread in threads if thread.priority == PriorityTier.TRACKING])
    stale = sort_threads([thread for thread in threads if thread.stale])

    return {
        "event": event_name,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "period": time_range,
        "phase": event_context.phase_label,
        "query": query,
        "domain_filters": domains,
        "counts": {
            "immediate": len(immediate),
            "today": len(today),
            "tracking": len(tracking),
            "stale": len(stale),
        },
        "tiers": {
            "immediate": [thread.as_dict() for thread in immediate],
            "today": [thread.as_dict() for thread in today],
            "tracking": [thread.as_dict() for thread in tracking],
        },
        "stale_threads": [thread.as_dict() for thread in stale],
    }


def render_dry_run_markdown(
    event_name: str,
    event_context: EventContext,
    generated_at: datetime,
    time_range: str,
    query: str,
    domains: list[str],
) -> str:
    lines = [
        f"# Inbox Digest — {event_name}",
        f"Generated: {generated_at.isoformat(timespec='seconds')}",
        f"Period: Last {time_range}",
        f"Phase: {event_context.phase_label}",
        "Threads: 0 Immediate · 0 Today · 0 Tracking · 0 Stale",
        "",
        "## Dry Run",
        f"- Query: `{query}`",
        "- Label: `INBOX`",
        "- Max results: `50`",
        f"- Domain filters: `{', '.join(domains) if domains else 'none'}`",
        "- Composio fetch skipped",
    ]
    return "\n".join(lines)


def resolve_output_path(output: str | None, event_name: str, generated_at: datetime, as_json: bool) -> Path | None:
    if not output:
        return None

    path = Path(output).expanduser()
    suffix = ".json" if as_json else ".md"
    directory_like = output.endswith(("/", "\\")) or (path.suffix == "" and not path.exists()) or path.is_dir()
    if directory_like:
        slug = slugify(event_name)
        return path / f"{generated_at.date().isoformat()}-{slug}-inbox-digest{suffix}"
    return path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "event"


def escape_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("|", "\\|")).strip()


def escape_inline(value: str) -> str:
    return value.replace("_", "\\_").replace("*", "\\*").strip()


def write_output(content: str, output_path: Path | None) -> None:
    if output_path is None:
        print(content)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(str(output_path))


def dedupe_threads(threads: list[TriageThread]) -> list[TriageThread]:
    latest_by_thread: dict[str, TriageThread] = {}
    for thread in threads:
        key = thread.thread_id or thread.message_id
        existing = latest_by_thread.get(key)
        if existing is None or thread.date > existing.date:
            latest_by_thread[key] = thread
    return list(latest_by_thread.values())


def fetch_threads(
    client: EventComposioClient,
    query: str,
    now: datetime,
) -> list[TriageThread]:
    raw_result = client.fetch_emails(query=query, max_results=50)
    messages = extract_message_collection(raw_result)
    if not messages:
        return []

    threads: list[TriageThread] = []
    for item in messages:
        normalized = normalize_thread(item, client=client, now=now)
        if normalized is not None:
            threads.append(normalized)

    return sorted(dedupe_threads(threads), key=lambda thread: thread.date, reverse=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    generated_at = datetime.now(tz=UTC)
    event_context = EventContext(event_name=args.event, event_date=args.date, now=generated_at)
    domains = parse_domain_filters(args.domains)
    query = build_query(args.event, args.time_range)

    if args.dry_run:
        if args.json:
            payload = {
                "dry_run": True,
                "event": args.event,
                "event_date": args.date.date().isoformat(),
                "generated_at": generated_at.isoformat(timespec="seconds"),
                "phase": event_context.phase_label,
                "period": args.time_range,
                "query": query,
                "label": "INBOX",
                "max_results": 50,
                "domain_filters": domains,
            }
            content = json.dumps(payload, indent=2)
        else:
            content = render_dry_run_markdown(
                event_name=args.event,
                event_context=event_context,
                generated_at=generated_at,
                time_range=args.time_range,
                query=query,
                domains=domains,
            )

        output_path = resolve_output_path(args.output, args.event, generated_at, args.json)
        write_output(content, output_path)
        return 0

    try:
        client = EventComposioClient()
        threads = fetch_threads(client=client, query=query, now=generated_at)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        print(f"Failed to fetch Gmail threads via Composio: {exc}", file=sys.stderr)
        return 1

    filtered_threads = filter_by_domains(threads, domains)
    enriched_threads = [compute_thread_metadata(thread, event_context) for thread in filtered_threads]

    if args.json:
        payload = build_json_output(
            event_name=args.event,
            time_range=args.time_range,
            domains=domains,
            event_context=event_context,
            generated_at=generated_at,
            query=query,
            threads=enriched_threads,
        )
        content = json.dumps(payload, indent=2)
    else:
        content = render_markdown(
            event_name=args.event,
            time_range=args.time_range,
            event_context=event_context,
            generated_at=generated_at,
            threads=enriched_threads,
        )

    output_path = resolve_output_path(args.output, args.event, generated_at, args.json)
    write_output(content, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

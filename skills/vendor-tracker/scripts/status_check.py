from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedCallResult=false

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.composio_client import EventComposioClient
from lib.event_context import EventContext, EventPhase


PHASE_THRESHOLD_HOURS: dict[EventPhase, int] = {
    EventPhase.NORMAL: 48,
    EventPhase.PLANNING: 24,
    EventPhase.ADVANCE: 12,
    EventPhase.LOAD_IN: 2,
    EventPhase.SHOW_DAY: 1,
    EventPhase.POST_EVENT: 72,
}

VENDOR_PROFILES: dict[str, dict[str, Any]] = {
    "AV": {"lead_time": "2-4 weeks", "lead_time_days": 14, "impact": "critical"},
    "Venue": {"lead_time": "Months", "lead_time_days": 60, "impact": "critical"},
    "Catering": {"lead_time": "2-3 weeks", "lead_time_days": 14, "impact": "high"},
    "Security": {"lead_time": "1-2 weeks", "lead_time_days": 7, "impact": "high"},
    "Decor/Floral": {"lead_time": "1-2 weeks", "lead_time_days": 7, "impact": "medium"},
    "Signage": {"lead_time": "5-10 business days", "lead_time_days": 5, "impact": "medium"},
    "Transport": {"lead_time": "1-2 weeks", "lead_time_days": 7, "impact": "high"},
    "Staffing": {"lead_time": "1-2 weeks", "lead_time_days": 7, "impact": "medium"},
    "Entertainment": {"lead_time": "Varies", "lead_time_days": 14, "impact": "high"},
    "Rentals": {"lead_time": "1 week", "lead_time_days": 7, "impact": "medium"},
    "Unknown": {"lead_time": "Unknown", "lead_time_days": 7, "impact": "medium"},
}

NAME_KEYS = ("vendor", "vendor_name", "name")
TYPE_KEYS = ("type", "vendor_type", "category")
ITEM_KEYS = (
    "item",
    "deliverable",
    "deliverable_name",
    "outstanding_item",
    "outstanding",
    "request",
    "task",
    "needed",
    "what",
    "what_needed",
    "what_they_need",
)
DUE_KEYS = ("due_date", "deadline", "due", "needed_by", "confirm_by", "requested_by")
LAST_CONTACT_KEYS = (
    "last_contact",
    "last_communication",
    "last_communication_date",
    "last_reply",
    "last_email",
    "last_touch",
)
WAITING_KEYS = ("waiting_on", "blocked_by", "dependency", "needed_from")
OWNER_KEYS = ("owner", "who_owns_it", "internal_owner", "lead")
STATUS_KEYS = ("status", "item_status", "deliverable_status", "confirmation_status")
CONFIRMED_KEYS = ("confirmed", "is_confirmed", "complete", "completed")
EMAIL_KEYS = ("email", "vendor_email", "contact_email", "account_manager_email")
PHONE_KEYS = ("phone", "vendor_phone", "contact_phone", "account_manager_phone")
CONTACT_KEYS = ("contact_name", "contact", "account_manager", "rep", "account_manager_name")
CONTRACT_KEYS = ("contract_status", "agreement_status")
PAYMENT_KEYS = ("payment_status", "invoice_status", "balance_status")
MILESTONE_KEYS = ("next_milestone", "milestone", "next_step")
NOTES_KEYS = ("notes", "details", "description", "risk", "context")
ORIGINAL_SUBJECT_KEYS = ("original_subject", "email_subject", "thread_subject")
ORIGINAL_REQUEST_KEYS = ("original_request", "reference", "request_context")
ATTEMPT_KEYS = ("attempts", "follow_up_count", "escalation_attempts", "contact_attempts")
BLOCKED_KEYS = ("blocked", "waiting_on_us")

WAITING_ON_US_TERMS = {
    "us",
    "our team",
    "event team",
    "internal",
    "client",
    "production",
    "planner",
    "approval",
    "headcount",
    "po",
    "purchase order",
    "floor plan",
    "artwork",
    "assets",
    "payment from us",
}

CONFIRMED_TERMS = {
    "confirmed",
    "complete",
    "completed",
    "done",
    "approved",
    "signed",
    "locked",
    "booked",
    "received",
}

PENDING_TERMS = {
    "pending",
    "not started",
    "awaiting",
    "open",
    "in progress",
    "unconfirmed",
    "unsent",
    "draft",
    "balance due",
    "unpaid",
}

IMPACT_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass(slots=True)
class VendorItem:
    vendor_name: str
    vendor_type: str
    item: str
    due_date: datetime | None
    last_contact: datetime | None
    waiting_on: str
    owner: str
    vendor_email: str
    vendor_phone: str
    contact_name: str
    status_text: str
    contract_status: str
    payment_status: str
    next_milestone: str
    notes: str
    original_subject: str
    original_request: str
    attempts: int
    source: str
    blocked_override: bool | None
    confirmed_override: bool | None


@dataclass(slots=True)
class VendorStatus:
    vendor_name: str
    vendor_type: str
    item: str
    due_date: datetime | None
    last_contact: datetime | None
    waiting_on: str
    owner: str
    vendor_email: str
    vendor_phone: str
    contact_name: str
    status_text: str
    contract_status: str
    payment_status: str
    next_milestone: str
    notes: str
    original_subject: str
    original_request: str
    attempts: int
    source: str
    status: str
    impact: str
    lead_time: str
    threshold_hours: int
    risk_reason: str
    recommended_action: str
    hours_since_last_contact: float | None
    hours_to_due: float | None
    hours_overdue: float | None
    blocked: bool
    confirmed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "vendor_name": self.vendor_name,
            "vendor_type": self.vendor_type,
            "item": self.item,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "due_date_label": format_short_date(self.due_date),
            "last_contact": self.last_contact.isoformat() if self.last_contact else None,
            "last_contact_label": format_short_date(self.last_contact),
            "waiting_on": self.waiting_on,
            "owner": self.owner,
            "vendor_email": self.vendor_email,
            "vendor_phone": self.vendor_phone,
            "contact_name": self.contact_name,
            "status_text": self.status_text,
            "contract_status": self.contract_status,
            "payment_status": self.payment_status,
            "next_milestone": self.next_milestone,
            "notes": self.notes,
            "original_subject": self.original_subject,
            "original_request": self.original_request,
            "attempts": self.attempts,
            "source": self.source,
            "status": self.status,
            "impact": self.impact,
            "lead_time": self.lead_time,
            "threshold_hours": self.threshold_hours,
            "risk_reason": self.risk_reason,
            "recommended_action": self.recommended_action,
            "hours_since_last_contact": round(self.hours_since_last_contact, 2) if self.hours_since_last_contact is not None else None,
            "hours_to_due": round(self.hours_to_due, 2) if self.hours_to_due is not None else None,
            "hours_overdue": round(self.hours_overdue, 2) if self.hours_overdue is not None else None,
            "blocked": self.blocked,
            "confirmed": self.confirmed,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a vendor status dashboard for an event.")
    parser.add_argument("--event", required=True, help="Event name.")
    parser.add_argument(
        "--date",
        required=True,
        type=parse_event_date,
        help="Event date in YYYY-MM-DD format.",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--spreadsheet", help="Google Sheets spreadsheet ID.")
    source_group.add_argument("--vendors", help="Path to a JSON file containing vendor data.")
    parser.add_argument("--sheet-range", default="Sheet1", help='Google Sheets range to read. Defaults to "Sheet1".')
    parser.add_argument("--output", help="Output file path or directory. Defaults to stdout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be checked without API calls.")
    return parser.parse_args(argv)


def parse_event_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must be in YYYY-MM-DD format") from exc


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "event"


def resolve_output_path(output: str | None, event_name: str, generated_at: datetime, as_json: bool) -> Path | None:
    if not output:
        return None

    path = Path(output).expanduser()
    suffix = ".json" if as_json else ".md"
    directory_like = output.endswith(("/", "\\")) or (path.suffix == "" and not path.exists()) or path.is_dir()
    if directory_like:
        return path / f"{generated_at.date().isoformat()}-{slugify(event_name)}-vendor-status{suffix}"
    return path


def write_output(content: str, output_path: Path | None) -> None:
    if output_path is None:
        print(content)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(str(output_path))


def first_value(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_space(value)
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def first_present(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    if lowered in {"true", "yes", "y", "1", "blocked", "complete", "completed", "confirmed"}:
        return True
    if lowered in {"false", "no", "n", "0", "pending", "open", "incomplete", "unconfirmed"}:
        return False
    return None


def parse_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = normalize_space(value)
    if not text:
        return 0
    match = re.search(r"-?\d+", text)
    return int(match.group(0)) if match else 0


def parse_datetime(value: Any, default_year: int) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)

    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 1_000_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, tz=UTC)

    text = normalize_space(value)
    if not text:
        return None
    if text.isdigit():
        return parse_datetime(int(text), default_year)

    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        pass

    for pattern in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d",
        "%B %d",
        "%m/%d",
    ):
        try:
            parsed = datetime.strptime(text, pattern)
            if "%Y" not in pattern and "%y" not in pattern:
                parsed = parsed.replace(year=default_year)
            return parsed.replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def maybe_parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "[{":
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def unwrap_action_result(value: Any) -> Any:
    current = maybe_parse_json(value)
    for _ in range(8):
        current = maybe_parse_json(current)
        if isinstance(current, dict) and "data" in current:
            current = current["data"]
            continue
        if isinstance(current, dict) and "response" in current:
            current = current["response"]
            continue
        break
    return maybe_parse_json(current)


def extract_sheet_rows(payload: Any) -> list[list[str]]:
    def search(node: Any) -> list[list[str]]:
        if isinstance(node, list):
            if node and all(isinstance(row, list) for row in node):
                return [[normalize_space(cell) for cell in row] for row in node]
            for item in node:
                result = search(item)
                if result:
                    return result
            return []

        if isinstance(node, dict):
            values = node.get("values")
            if isinstance(values, list) and values and all(isinstance(row, list) for row in values):
                return [[normalize_space(cell) for cell in row] for row in values]
            for value in node.values():
                result = search(value)
                if result:
                    return result
        return []

    return search(unwrap_action_result(payload))


def canonicalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def rows_to_records(rows: list[list[str]]) -> list[dict[str, Any]]:
    if len(rows) < 2:
        return []

    headers = [canonicalize_header(cell) or f"column_{index + 1}" for index, cell in enumerate(rows[0])]
    records: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows[1:], start=2):
        if not any(normalize_space(cell) for cell in row):
            continue
        padded = row + [""] * max(0, len(headers) - len(row))
        record = {headers[index]: normalize_space(padded[index]) for index in range(len(headers))}
        record["__source"] = f"row {row_index}"
        records.append(record)
    return records


def flatten_vendor_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("vendors"), list):
            return flatten_vendor_entries(payload["vendors"])
        if isinstance(payload.get("items"), list):
            return flatten_vendor_entries(payload["items"])
        return flatten_vendor_entries([payload])

    if not isinstance(payload, list):
        raise ValueError("Vendor JSON must be a list of vendor records or an object with a vendors/items array")

    records: list[dict[str, Any]] = []
    nested_keys = ("items", "deliverables", "outstanding_items", "outstanding", "tasks")
    for index, entry in enumerate(payload, start=1):
        if not isinstance(entry, dict):
            continue
        nested_key = next((key for key in nested_keys if isinstance(entry.get(key), list)), None)
        if not nested_key:
            record = dict(entry)
            record.setdefault("__source", f"vendors[{index}]")
            records.append(record)
            continue
        base = {key: value for key, value in entry.items() if key != nested_key}
        nested = entry[nested_key]
        for nested_index, item in enumerate(nested, start=1):
            merged = dict(base)
            if isinstance(item, dict):
                merged.update(item)
            elif isinstance(item, str):
                merged["item"] = item
            else:
                continue
            merged["__source"] = f"vendors[{index}].{nested_key}[{nested_index}]"
            records.append(merged)
    return records


def load_vendor_file(path: str) -> list[dict[str, Any]]:
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return flatten_vendor_entries(payload)


def canonicalize_vendor_type(value: str) -> str:
    lowered = normalize_space(value).lower()
    if not lowered:
        return "Unknown"
    if any(token in lowered for token in ("av", "audio", "video", "lighting", "technical", "staging", "rigging")):
        return "AV"
    if any(token in lowered for token in ("venue", "hotel", "ballroom", "convention", "site")):
        return "Venue"
    if any(token in lowered for token in ("catering", "f&b", "food", "beverage", "banquet")):
        return "Catering"
    if "security" in lowered:
        return "Security"
    if any(token in lowered for token in ("decor", "floral", "florist")):
        return "Decor/Floral"
    if any(token in lowered for token in ("signage", "print", "wayfinding")):
        return "Signage"
    if any(token in lowered for token in ("transport", "logistics", "trucking", "shuttle")):
        return "Transport"
    if "staff" in lowered:
        return "Staffing"
    if any(token in lowered for token in ("entertainment", "talent", "performer", "artist")):
        return "Entertainment"
    if any(token in lowered for token in ("rental", "linen", "chair", "table", "furniture")):
        return "Rentals"
    return normalize_space(value).title()


def profile_for(vendor_type: str) -> dict[str, Any]:
    return VENDOR_PROFILES.get(vendor_type, VENDOR_PROFILES["Unknown"])


def default_item_name(contract_status: str, payment_status: str, next_milestone: str) -> str:
    if contract_status and contains_any(contract_status, PENDING_TERMS):
        return "Contract finalization"
    if payment_status and contains_any(payment_status, {"due", "unpaid", "balance due", "deposit"}):
        return "Payment status"
    if next_milestone:
        return next_milestone
    return "Vendor check-in"


def normalize_vendor_item(record: dict[str, Any], event_year: int) -> VendorItem:
    contract_status = first_value(record, CONTRACT_KEYS)
    payment_status = first_value(record, PAYMENT_KEYS)
    next_milestone = first_value(record, MILESTONE_KEYS)
    return VendorItem(
        vendor_name=first_value(record, NAME_KEYS) or "Unknown Vendor",
        vendor_type=canonicalize_vendor_type(first_value(record, TYPE_KEYS)),
        item=first_value(record, ITEM_KEYS) or default_item_name(contract_status, payment_status, next_milestone),
        due_date=parse_datetime(first_value(record, DUE_KEYS), event_year),
        last_contact=parse_datetime(first_value(record, LAST_CONTACT_KEYS), event_year),
        waiting_on=first_value(record, WAITING_KEYS),
        owner=first_value(record, OWNER_KEYS) or "Our team",
        vendor_email=first_value(record, EMAIL_KEYS),
        vendor_phone=first_value(record, PHONE_KEYS),
        contact_name=first_value(record, CONTACT_KEYS),
        status_text=first_value(record, STATUS_KEYS),
        contract_status=contract_status,
        payment_status=payment_status,
        next_milestone=next_milestone,
        notes=first_value(record, NOTES_KEYS),
        original_subject=first_value(record, ORIGINAL_SUBJECT_KEYS),
        original_request=first_value(record, ORIGINAL_REQUEST_KEYS),
        attempts=parse_int(first_value(record, ATTEMPT_KEYS)),
        source=normalize_space(record.get("__source", "input")),
        blocked_override=parse_bool(first_present(record, BLOCKED_KEYS)),
        confirmed_override=parse_bool(first_present(record, CONFIRMED_KEYS)),
    )


def contains_any(value: str, terms: set[str]) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in terms)


def is_waiting_on_us(item: VendorItem) -> bool:
    if item.blocked_override is True:
        return True
    waiting = item.waiting_on.lower()
    if waiting and any(term in waiting for term in WAITING_ON_US_TERMS):
        return True
    if contains_any(item.status_text, {"waiting on us", "blocked", "internal action", "client action"}):
        return True
    return False


def is_confirmed(item: VendorItem) -> bool:
    if item.confirmed_override is not None:
        return item.confirmed_override
    if item.status_text and contains_any(item.status_text, CONFIRMED_TERMS) and not contains_any(item.status_text, PENDING_TERMS):
        return True
    if item.contract_status and contains_any(item.contract_status, {"signed", "complete", "confirmed"}):
        return True
    for value in (item.payment_status, item.next_milestone, item.notes):
        if value and contains_any(value, {"confirmed", "approved"}):
            return True
    return False


def phase_threshold_hours(phase: EventPhase) -> int:
    return PHASE_THRESHOLD_HOURS.get(phase, 48)


def hours_between(later: datetime, earlier: datetime | None) -> float | None:
    if earlier is None:
        return None
    return (later - earlier).total_seconds() / 3600


def critical_window_days(impact: str) -> int:
    if impact == "critical":
        return 14
    if impact == "high":
        return 7
    return 3


def format_duration_hours(hours: float) -> str:
    if hours >= 24:
        days = hours / 24
        return f"{days:.1f}d"
    return f"{hours:.0f}h"


def build_on_track_summary(item: VendorItem, hours_since_last_contact: float | None) -> str:
    parts: list[str] = []
    if item.status_text:
        parts.append(item.status_text)
    elif item.contract_status:
        parts.append(f"Contract {item.contract_status}")
    elif item.payment_status:
        parts.append(f"Payment {item.payment_status}")
    elif item.next_milestone:
        parts.append(f"Next: {item.next_milestone}")
    else:
        parts.append("Within response window")

    if hours_since_last_contact is not None and hours_since_last_contact < 24:
        parts.append("recent vendor contact")
    return ", ".join(parts)


def build_recommended_action(status: str, item: VendorItem, event_context: EventContext) -> str:
    contact = item.contact_name or item.vendor_name
    vendor_type = item.vendor_type
    if status == "BLOCKED":
        needed = item.waiting_on or item.item
        owner = item.owner or "Our team"
        return f"Send {needed} from {owner}"
    if status == "OVERDUE":
        if event_context.phase in {EventPhase.LOAD_IN, EventPhase.SHOW_DAY}:
            return f"Phone {contact} immediately"
        if vendor_type in {"AV", "Venue", "Catering"}:
            return f"Phone {contact} within 4h"
        return f"Follow up now; phone {contact} next business day if still unconfirmed"
    if status == "AT RISK":
        if event_context.phase == EventPhase.SHOW_DAY:
            return f"Phone {contact} now"
        if vendor_type in {"AV", "Venue", "Catering"} and event_context.phase in {EventPhase.ADVANCE, EventPhase.LOAD_IN}:
            return f"Follow up now; prep phone escalation for {contact}"
        return "Follow up today and confirm timing"
    return "Monitor next milestone"


def evaluate_status(item: VendorItem, event_context: EventContext, now: datetime) -> VendorStatus:
    profile = profile_for(item.vendor_type)
    impact = str(profile["impact"])
    lead_time = str(profile["lead_time"])
    threshold_hours = phase_threshold_hours(event_context.phase)
    blocked = is_waiting_on_us(item)
    confirmed = is_confirmed(item)

    hours_since_last_contact = hours_between(now, item.last_contact)
    hours_to_due = hours_between(item.due_date, now) if item.due_date else None
    hours_overdue = abs(hours_to_due) if hours_to_due is not None and hours_to_due < 0 else None
    response_overdue = hours_since_last_contact is not None and hours_since_last_contact >= threshold_hours

    status = "ON TRACK"
    risk_reason = build_on_track_summary(item, hours_since_last_contact)

    if blocked:
        status = "BLOCKED"
        needed = item.waiting_on or item.item
        risk_reason = f"Waiting on {needed} from {item.owner or 'our team'}"
    elif item.due_date and item.due_date < now and not confirmed:
        status = "OVERDUE"
        risk_reason = f"Past due by {format_duration_hours(abs(hours_to_due or 0))} with no confirmation"
    elif item.due_date is None and response_overdue and not confirmed:
        status = "OVERDUE"
        risk_reason = f"No vendor reply for {format_duration_hours(hours_since_last_contact or 0)} (threshold {threshold_hours}h)"
    else:
        risk_factors: list[str] = []
        if item.due_date and hours_to_due is not None and 0 <= hours_to_due <= max(24, threshold_hours * 2):
            risk_factors.append(f"deadline in {format_duration_hours(hours_to_due)}")
        if hours_since_last_contact is not None and hours_since_last_contact >= threshold_hours * 0.75:
            risk_factors.append(f"last contact {format_duration_hours(hours_since_last_contact)} ago")
        if not confirmed and event_context.days_until_event <= critical_window_days(impact):
            risk_factors.append(f"{impact} vendor inside final window")
        if item.vendor_type in {"AV", "Venue"} and event_context.days_until_event <= 14 and not confirmed:
            risk_factors.append("critical vendor inside 14-day window")
        if contains_any(item.status_text, PENDING_TERMS) or contains_any(item.contract_status, PENDING_TERMS) or contains_any(item.payment_status, PENDING_TERMS):
            if event_context.days_until_event <= max(7, critical_window_days(impact)):
                risk_factors.append("open status close to event")

        if risk_factors and not confirmed:
            status = "AT RISK"
            risk_reason = "; ".join(risk_factors[:3])

    recommended_action = build_recommended_action(status, item, event_context)

    return VendorStatus(
        vendor_name=item.vendor_name,
        vendor_type=item.vendor_type,
        item=item.item,
        due_date=item.due_date,
        last_contact=item.last_contact,
        waiting_on=item.waiting_on,
        owner=item.owner,
        vendor_email=item.vendor_email,
        vendor_phone=item.vendor_phone,
        contact_name=item.contact_name,
        status_text=item.status_text,
        contract_status=item.contract_status,
        payment_status=item.payment_status,
        next_milestone=item.next_milestone,
        notes=item.notes,
        original_subject=item.original_subject,
        original_request=item.original_request,
        attempts=item.attempts,
        source=item.source,
        status=status,
        impact=impact,
        lead_time=lead_time,
        threshold_hours=threshold_hours,
        risk_reason=risk_reason,
        recommended_action=recommended_action,
        hours_since_last_contact=hours_since_last_contact,
        hours_to_due=hours_to_due,
        hours_overdue=hours_overdue,
        blocked=blocked,
        confirmed=confirmed,
    )


def sort_items(items: list[VendorStatus]) -> list[VendorStatus]:
    far_future = datetime.max.replace(tzinfo=UTC)
    far_past = datetime.min.replace(tzinfo=UTC)
    return sorted(
        items,
        key=lambda item: (
            IMPACT_ORDER.get(item.impact, 9),
            item.due_date or far_future,
            item.last_contact or far_past,
            item.vendor_name.lower(),
            item.item.lower(),
        ),
    )


def days_away_label(event_context: EventContext) -> str:
    days = event_context.days_until_event
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''} away"
    if days == 0:
        return "today"
    past = abs(days)
    return f"{past} day{'s' if past != 1 else ''} ago"


def format_short_date(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone(UTC).strftime("%b %-d")


def safe_days_over(item: VendorStatus) -> str:
    if item.hours_overdue is None:
        return "—"
    return f"{max(1, round(item.hours_overdue / 24))}"


def render_markdown(event_name: str, generated_at: datetime, event_context: EventContext, items: list[VendorStatus]) -> str:
    overdue = sort_items([item for item in items if item.status == "OVERDUE"])
    at_risk = sort_items([item for item in items if item.status == "AT RISK"])
    on_track = sort_items([item for item in items if item.status == "ON TRACK"])
    blocked = sort_items([item for item in items if item.status == "BLOCKED"])
    vendor_count = len({item.vendor_name for item in items})

    lines = [
        f"# Vendor Status — {event_name}",
        f"Updated: {generated_at.isoformat(timespec='seconds')}",
        f"Event Date: {event_context.event_date.date().isoformat()} ({days_away_label(event_context)} — {event_context.phase_label})",
        f"Vendors: {vendor_count} total · {len(on_track)} on track · {len(at_risk)} at risk · {len(overdue)} overdue · {len(blocked)} blocked",
        "",
        "## OVERDUE — Immediate Action Required",
        "| Vendor | Type | Item | Due Date | Days Over | Last Contact | Action |",
        "|--------|------|------|----------|-----------|--------------|--------|",
    ]

    if overdue:
        lines.extend(
            f"| {escape_cell(item.vendor_name)} | {escape_cell(item.vendor_type)} | {escape_cell(item.item)} | {format_short_date(item.due_date)} | {safe_days_over(item)} | {format_short_date(item.last_contact)} | {escape_cell(item.recommended_action)} |"
            for item in overdue
        )
    else:
        lines.append("| — | — | — | — | — | — | No overdue vendor items |")

    lines.extend(
        [
            "",
            "## AT RISK — Monitor Closely",
            "| Vendor | Type | Item | Due Date | Last Contact | Risk |",
            "|--------|------|------|----------|--------------|------|",
        ]
    )

    if at_risk:
        lines.extend(
            f"| {escape_cell(item.vendor_name)} | {escape_cell(item.vendor_type)} | {escape_cell(item.item)} | {format_short_date(item.due_date)} | {format_short_date(item.last_contact)} | {escape_cell(item.risk_reason)} |"
            for item in at_risk
        )
    else:
        lines.append("| — | — | — | — | — | No at-risk vendor items |")

    lines.extend(
        [
            "",
            "## ON TRACK",
            "| Vendor | Type | Status | Next Milestone |",
            "|--------|------|--------|----------------|",
        ]
    )

    if on_track:
        lines.extend(
            f"| {escape_cell(item.vendor_name)} | {escape_cell(item.vendor_type)} | {escape_cell(item.risk_reason)} | {escape_cell(item.next_milestone or format_short_date(item.due_date))} |"
            for item in on_track
        )
    else:
        lines.append("| — | — | — | No on-track items in scope |")

    lines.extend(
        [
            "",
            "## BLOCKED — Waiting on Us",
            "| Vendor | Type | What They Need | Who Owns It | Deadline |",
            "|--------|------|----------------|-------------|----------|",
        ]
    )

    if blocked:
        lines.extend(
            f"| {escape_cell(item.vendor_name)} | {escape_cell(item.vendor_type)} | {escape_cell(item.waiting_on or item.item)} | {escape_cell(item.owner or 'Our team')} | {format_short_date(item.due_date)} |"
            for item in blocked
        )
    else:
        lines.append("| — | — | — | — | No blocked vendor items |")

    return "\n".join(lines)


def build_json_output(
    event_name: str,
    generated_at: datetime,
    event_context: EventContext,
    source: dict[str, Any],
    items: list[VendorStatus],
) -> dict[str, Any]:
    overdue = sort_items([item for item in items if item.status == "OVERDUE"])
    at_risk = sort_items([item for item in items if item.status == "AT RISK"])
    on_track = sort_items([item for item in items if item.status == "ON TRACK"])
    blocked = sort_items([item for item in items if item.status == "BLOCKED"])

    return {
        "event": event_name,
        "event_date": event_context.event_date.date().isoformat(),
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "phase": event_context.phase.value,
        "phase_label": event_context.phase_label,
        "days_until_event": event_context.days_until_event,
        "threshold_hours": phase_threshold_hours(event_context.phase),
        "source": source,
        "counts": {
            "vendors": len({item.vendor_name for item in items}),
            "items": len(items),
            "overdue": len(overdue),
            "at_risk": len(at_risk),
            "on_track": len(on_track),
            "blocked": len(blocked),
        },
        "items": [item.as_dict() for item in sort_items(items)],
        "sections": {
            "overdue": [item.as_dict() for item in overdue],
            "at_risk": [item.as_dict() for item in at_risk],
            "on_track": [item.as_dict() for item in on_track],
            "blocked": [item.as_dict() for item in blocked],
        },
    }


def render_dry_run_markdown(
    event_name: str,
    generated_at: datetime,
    event_context: EventContext,
    source: dict[str, Any],
    as_json: bool,
) -> str:
    lines = [
        f"# Vendor Status — {event_name}",
        f"Updated: {generated_at.isoformat(timespec='seconds')}",
        f"Event Date: {event_context.event_date.date().isoformat()} ({days_away_label(event_context)} — {event_context.phase_label})",
        "",
        "## Dry Run",
        f"- Source: `{source['type']}`",
        f"- Phase threshold: `{phase_threshold_hours(event_context.phase)}h`",
        f"- Output format: `{'json' if as_json else 'markdown'}`",
    ]
    if source["type"] == "spreadsheet":
        lines.append(f"- Spreadsheet: `{source['spreadsheet_id']}`")
        lines.append(f"- Range: `{source['sheet_range']}`")
        lines.append("- Composio read skipped")
    else:
        lines.append(f"- Vendor file: `{source['vendors_path']}`")
        lines.append("- Local file parsing skipped")
    return "\n".join(lines)


def escape_cell(value: str) -> str:
    return normalize_space(value).replace("|", "\\|") or "—"


def fetch_vendor_records(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if args.spreadsheet:
        client = EventComposioClient()
        raw_rows = client.read_spreadsheet(args.spreadsheet, args.sheet_range)
        rows = extract_sheet_rows(raw_rows)
        return (
            {"type": "spreadsheet", "spreadsheet_id": args.spreadsheet, "sheet_range": args.sheet_range},
            rows_to_records(rows),
        )
    return ({"type": "vendors_file", "vendors_path": str(Path(args.vendors).expanduser())}, load_vendor_file(args.vendors))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    generated_at = datetime.now(tz=UTC)
    event_context = EventContext(event_name=args.event, event_date=args.date, now=generated_at)
    source: dict[str, Any]

    if args.spreadsheet:
        source = {"type": "spreadsheet", "spreadsheet_id": args.spreadsheet, "sheet_range": args.sheet_range}
    else:
        source = {"type": "vendors_file", "vendors_path": str(Path(args.vendors).expanduser())}

    if args.dry_run:
        if args.json:
            content = json.dumps(
                {
                    "dry_run": True,
                    "event": args.event,
                    "event_date": args.date.date().isoformat(),
                    "generated_at": generated_at.isoformat(timespec="seconds"),
                    "phase": event_context.phase.value,
                    "phase_label": event_context.phase_label,
                    "threshold_hours": phase_threshold_hours(event_context.phase),
                    "source": source,
                },
                indent=2,
            )
        else:
            content = render_dry_run_markdown(args.event, generated_at, event_context, source, args.json)
        write_output(content, resolve_output_path(args.output, args.event, generated_at, args.json))
        return 0

    try:
        source, records = fetch_vendor_records(args)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        print(f"Failed to load vendor data: {exc}", file=sys.stderr)
        return 1

    items = [normalize_vendor_item(record, event_context.event_date.year) for record in records]
    statuses = [evaluate_status(item, event_context, generated_at) for item in items]

    if args.json:
        content = json.dumps(
            build_json_output(args.event, generated_at, event_context, source, statuses),
            indent=2,
        )
    else:
        content = render_markdown(args.event, generated_at, event_context, statuses)

    write_output(content, resolve_output_path(args.output, args.event, generated_at, args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

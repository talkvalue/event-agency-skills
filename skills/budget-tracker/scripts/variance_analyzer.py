# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedCallResult=false, reportUnusedParameter=false, reportUnusedVariable=false, reportUnknownLambdaType=false, reportImplicitStringConcatenation=false
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.composio_client import EventComposioClient
from lib.event_context import EventContext


VARIANCE_THRESHOLDS = {
    "venue": 0.05,
    "catering": 0.10,
    "av": 0.10,
    "marketing": 0.15,
    "decor": 0.10,
    "contingency": 0.00,
}
DEFAULT_THRESHOLD = 0.10
AMOUNT_KEYS = (
    "amount",
    "invoice_amount",
    "invoice_total",
    "balance_due",
    "outstanding_amount",
    "receivable",
    "total",
)
ESTIMATE_KEYS = (
    "estimated",
    "estimate",
    "budget",
    "budget_amount",
    "planned",
    "quoted",
    "forecast",
)
ACTUAL_KEYS = (
    "actual",
    "actual_spend",
    "spent",
    "paid",
    "committed",
    "actual_to_date",
    "actuals",
)
CATEGORY_KEYS = (
    "category",
    "budget_category",
    "type",
    "line_item_category",
    "department",
    "cost_center",
)
NOTES_KEYS = (
    "notes",
    "reason",
    "cause",
    "variance_reason",
    "description",
    "context",
)
ACCOUNT_KEYS = (
    "account",
    "account_name",
    "client",
    "sponsor",
    "vendor",
    "vendor_name",
    "customer",
    "name",
)
INVOICE_NUMBER_KEYS = (
    "invoice_number",
    "invoice",
    "invoice_id",
    "number",
    "reference",
)
DUE_DATE_KEYS = (
    "due_date",
    "due",
    "payment_due",
    "invoice_due",
)
AGE_KEYS = ("age_days", "days_overdue", "aging_days", "invoice_age")
LATE_COUNT_KEYS = (
    "late_payments",
    "times_late",
    "late_count",
    "repeat_late_count",
)
RELATIONSHIP_KEYS = (
    "relationship_years",
    "years_as_client",
    "client_years",
    "account_years",
)
EVENT_DATE_KEYS = ("event_date", "date", "eventDate")
METADATA_KEYS = ("metadata", "event", "summary")
JSON_OUTPUT_SUFFIXES = {".json", ".jsonl"}


@dataclass(slots=True)
class CategorySummary:
    category: str
    estimated: float
    actual: float
    variance_amount: float
    variance_percent: float | None
    threshold_percent: float
    status: str
    cause: str
    recommended_action: str
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["estimated"] = round(self.estimated, 2)
        payload["actual"] = round(self.actual, 2)
        payload["variance_amount"] = round(self.variance_amount, 2)
        payload["variance_percent"] = round(self.variance_percent, 4) if self.variance_percent is not None else None
        payload["threshold_percent"] = round(self.threshold_percent, 4)
        return payload


@dataclass(slots=True)
class InvoiceSummary:
    account: str
    invoice_number: str
    amount: float
    age_days: int
    bucket: str
    risk: str
    follow_up_tone: str
    recommended_action: str
    due_date: datetime | None
    late_count: int
    relationship_years: float | None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["amount"] = round(self.amount, 2)
        payload["due_date"] = self.due_date.date().isoformat() if self.due_date else None
        return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze event budget variance and invoice aging from Google Sheets or JSON input."
    )
    parser.add_argument("--event", required=True, help="Event name for the dashboard.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--spreadsheet", help="Google Sheets spreadsheet ID with budget and invoice data.")
    source_group.add_argument("--budget-file", help="Path to a JSON file with budget and invoice data.")
    parser.add_argument("--output", help="Output file path or directory. Defaults to stdout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the analysis plan without calling Composio. Works without COMPOSIO_API_KEY.",
    )
    return parser.parse_args(argv)


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "event"


def canonicalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def resolve_output_path(output: str | None, event_name: str, generated_at: datetime, as_json: bool) -> Path | None:
    if not output:
        return None

    path = Path(output).expanduser()
    suffix = ".json" if as_json else ".md"
    directory_like = output.endswith(("/", "\\")) or (path.suffix == "" and not path.exists()) or path.is_dir()
    if directory_like:
        return path / f"{generated_at.date().isoformat()}-{slugify(event_name)}-budget-variance{suffix}"
    return path


def write_output(content: str, output_path: Path | None) -> None:
    if output_path is None:
        print(content)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(str(output_path))


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


def parse_amount(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_space(value)
    if not text:
        return 0.0
    cleaned = text.replace(",", "")
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return 0.0
    amount = float(match.group(0))
    return -amount if negative and amount > 0 else amount


def parse_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    match = re.search(r"-?\d+", normalize_space(value))
    return int(match.group(0)) if match else 0


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = normalize_space(value)
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def parse_datetime(value: Any, fallback_year: int | None = None) -> datetime | None:
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
        return parse_datetime(int(text), fallback_year)

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
        "%b %d",
        "%B %d",
        "%m/%d",
    ):
        try:
            parsed = datetime.strptime(text, pattern)
            if "%Y" not in pattern and "%y" not in pattern and fallback_year is not None:
                parsed = parsed.replace(year=fallback_year)
            return parsed.replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def first_text(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_space(value)
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def first_amount(record: dict[str, Any], keys: tuple[str, ...]) -> float:
    for key in keys:
        if key in record:
            amount = parse_amount(record[key])
            if amount != 0 or normalize_space(record[key]):
                return amount
    return 0.0


def infer_event_date(metadata: dict[str, Any], records: list[dict[str, Any]], now: datetime) -> datetime | None:
    for key in EVENT_DATE_KEYS:
        parsed = parse_datetime(metadata.get(key), now.year)
        if parsed:
            return parsed

    for record in records:
        for key in EVENT_DATE_KEYS:
            parsed = parse_datetime(record.get(key), now.year)
            if parsed:
                return parsed
    return None


def should_emit_json(args: argparse.Namespace) -> bool:
    if args.json:
        return True
    if isinstance(args.output, str):
        return Path(args.output).suffix.lower() in JSON_OUTPUT_SUFFIXES
    return False


def extract_json_records(node: Any, source_label: str) -> list[dict[str, Any]]:
    if isinstance(node, list):
        return [dict(item, __source=f"{source_label}[{index}]") for index, item in enumerate(node, start=1) if isinstance(item, dict)]
    if isinstance(node, dict):
        return [dict(node, __source=source_label)]
    return []


def load_budget_file(path_value: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    path = Path(path_value).expanduser()
    if not path.exists():
        raise SystemExit(f"Budget file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    metadata = payload if isinstance(payload, dict) else {}
    budget_records: list[dict[str, Any]] = []
    invoice_records: list[dict[str, Any]] = []

    if isinstance(payload, list):
        budget_records = extract_json_records(payload, "budget")
    elif isinstance(payload, dict):
        for key in METADATA_KEYS:
            nested = payload.get(key)
            if isinstance(nested, dict):
                metadata = {**metadata, **nested}

        for key in ("budget", "categories", "line_items", "budget_items", "records", "items"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                budget_records.extend(extract_json_records(candidate, key))

        for key in ("invoices", "receivables", "outstanding_invoices", "invoice_aging"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                invoice_records.extend(extract_json_records(candidate, key))

        if not budget_records:
            budget_records = extract_json_records(payload.get("data", payload), "budget")

    if not budget_records and isinstance(payload, dict):
        budget_records = [dict(payload, __source="budget")]

    return metadata, budget_records, invoice_records


def fetch_spreadsheet_records(spreadsheet_id: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    client = EventComposioClient()
    rows = extract_sheet_rows(client.read_spreadsheet(spreadsheet_id, "Sheet1"))
    records = rows_to_records(rows)
    return {"spreadsheet_id": spreadsheet_id}, records, []


def canonicalize_category(value: str) -> str:
    lowered = normalize_space(value).lower()
    if not lowered:
        return "Uncategorized"
    if any(token in lowered for token in ("grand total", "overall total", "total budget", "subtotal")):
        return ""
    if any(token in lowered for token in ("venue", "hotel", "ballroom", "room rental")):
        return "Venue"
    if any(token in lowered for token in ("av", "audio", "video", "lighting", "staging", "rigging", "production")):
        return "AV"
    if any(token in lowered for token in ("catering", "food", "beverage", "f&b", "banquet", "bar")):
        return "Catering"
    if any(token in lowered for token in ("marketing", "ads", "social", "pr", "collateral", "promotion")):
        return "Marketing"
    if any(token in lowered for token in ("travel", "flight", "hotel rooms", "ground transport", "airfare")):
        return "Travel"
    if any(token in lowered for token in ("speaker", "honoraria", "green room", "gift")):
        return "Speakers"
    if any(token in lowered for token in ("staff", "staffing", "registration desk", "ushers", "labor")):
        return "Staffing"
    if any(token in lowered for token in ("decor", "floral", "linen", "furniture")):
        return "Decor"
    if "contingency" in lowered:
        return "Contingency"
    return normalize_space(value).title()


def threshold_for(category: str) -> float:
    return VARIANCE_THRESHOLDS.get(category.lower(), DEFAULT_THRESHOLD)


def classify_cause(notes: str, category: str) -> str:
    lowered = notes.lower()
    if any(token in lowered for token in ("scope", "added", "additional", "change order", "upgrade")):
        return "Scope change or late addition"
    if any(token in lowered for token in ("weather", "force majeure", "storm", "rain")):
        return "Weather or force majeure"
    if any(token in lowered for token in ("price", "rate", "increase", "surcharge", "minimum")):
        return "Vendor price increase"
    if any(token in lowered for token in ("underestimate", "under budgeted", "estimate", "missed")):
        return "Original estimate was too low"
    if category == "Venue":
        return "Likely scope change or venue surcharge"
    if category == "Catering":
        return "Likely headcount or per-head cost movement"
    if category == "Marketing":
        return "Likely additional channel spend or campaign extension"
    if category == "AV":
        return "Likely added technical scope or labor"
    return "Needs budget-owner review"


def recommended_variance_action(
    category: str,
    variance_amount: float,
    variance_percent: float | None,
    event_context: EventContext | None,
) -> str:
    if category == "Contingency" and variance_amount > 0:
        if event_context and event_context.days_until_event > 14:
            return "Contingency has been drawn before T-14. Hold further draws until explicitly approved."
        return "Document what triggered the contingency draw and protect the remaining buffer."
    if variance_amount <= 0:
        return "Keep the savings visible and avoid reallocating it until other overruns are confirmed."
    if category == "Venue":
        return "Confirm whether this is a scope change, then seek venue concessions or offset elsewhere."
    if category == "Catering":
        return "Reforecast final headcount now and trim menu or bar upgrades before the overage compounds."
    if category == "AV":
        return "Audit labor, rentals, and last-minute scope adds before approving any further technical spend."
    if category == "Marketing":
        return "Cut the lowest-converting placements first and protect channels that are still driving registrations."
    if variance_percent is not None and variance_percent >= 0.20:
        return "Freeze new spend in this line until the owner explains the overage and names an offset."
    return "Review this line with the owner and offset it against lower-priority categories if possible."


def build_category_summaries(records: list[dict[str, Any]], event_context: EventContext | None) -> list[CategorySummary]:
    grouped: dict[str, dict[str, Any]] = {}

    for record in records:
        raw_category = first_text(record, CATEGORY_KEYS)
        category = canonicalize_category(raw_category)
        if not category:
            continue

        estimated = first_amount(record, ESTIMATE_KEYS)
        actual = first_amount(record, ACTUAL_KEYS)
        if actual == 0.0 and estimated != 0.0 and "remaining" in record:
            actual = max(estimated - parse_amount(record.get("remaining")), 0.0)

        notes_value = " | ".join(first_text(record, (key,)) for key in NOTES_KEYS if first_text(record, (key,)))
        bucket = grouped.setdefault(
            category,
            {"estimated": 0.0, "actual": 0.0, "notes": []},
        )
        bucket["estimated"] += estimated
        bucket["actual"] += actual
        if notes_value:
            bucket["notes"].append(notes_value)

    summaries: list[CategorySummary] = []
    for category, aggregate in grouped.items():
        estimated = float(aggregate["estimated"])
        actual = float(aggregate["actual"])
        notes = [normalize_space(note) for note in aggregate["notes"] if normalize_space(note)]
        if estimated == 0.0 and actual == 0.0 and not notes:
            continue
        variance_amount = actual - estimated
        variance_percent = variance_amount / estimated if estimated else None
        threshold = threshold_for(category)
        cause = classify_cause(" ".join(notes), category)
        status = "OK"

        if category == "Contingency" and actual > 0:
            status = "DRAWN"
            if event_context and event_context.days_until_event > 14:
                status = "ALERT"
        elif variance_amount > 0 and variance_percent is not None and variance_percent >= threshold:
            status = "ALERT"
        elif variance_amount > 0:
            status = "OVER"
        elif variance_amount < 0:
            status = "UNDER"

        summaries.append(
            CategorySummary(
                category=category,
                estimated=estimated,
                actual=actual,
                variance_amount=variance_amount,
                variance_percent=variance_percent,
                threshold_percent=threshold,
                status=status,
                cause=cause,
                recommended_action=recommended_variance_action(category, variance_amount, variance_percent, event_context),
                notes=notes[:3],
            )
        )

    return sorted(summaries, key=lambda item: (-abs(item.variance_amount), item.category))


def record_looks_like_invoice(record: dict[str, Any]) -> bool:
    keys = set(record)
    has_amount = any(key in keys and normalize_space(record.get(key)) for key in AMOUNT_KEYS)
    has_invoice_signal = bool(keys.intersection(INVOICE_NUMBER_KEYS + DUE_DATE_KEYS + AGE_KEYS + ACCOUNT_KEYS))
    return has_amount and has_invoice_signal


def compute_age_days(record: dict[str, Any], due_date: datetime | None, now: datetime) -> int:
    for key in AGE_KEYS:
        if key in record and normalize_space(record.get(key)):
            return max(parse_int(record.get(key)), 0)
    if due_date is None:
        return 0
    delta = (now.date() - due_date.date()).days
    return max(delta, 0)


def invoice_bucket(age_days: int) -> str:
    if age_days <= 0:
        return "Current"
    if age_days <= 30:
        return "1-30"
    if age_days <= 60:
        return "31-60"
    if age_days <= 90:
        return "61-90"
    return "90+"


def invoice_risk(age_days: int, late_count: int, amount: float) -> str:
    if age_days > 90 or late_count >= 3:
        return "High"
    if age_days > 30 or late_count >= 2 or amount >= 10000:
        return "Medium"
    if age_days > 0:
        return "Low"
    return "Current"


def invoice_tone(age_days: int, late_count: int, relationship_years: float | None) -> str:
    long_term = relationship_years is not None and relationship_years >= 3
    if age_days <= 0:
        return "No action"
    if age_days <= 30 and late_count <= 1 and long_term:
        return "Warm nudge"
    if age_days <= 30 and late_count <= 1:
        return "Friendly reminder"
    if age_days <= 30:
        return "Polite but direct"
    if age_days <= 60:
        return "Firm request"
    if age_days <= 90:
        return "Escalation"
    return "Escalation with consequences"


def invoice_action(invoice_number: str, amount: float, age_days: int, tone: str) -> str:
    amount_label = format_currency(amount)
    invoice_label = invoice_number or "Unnumbered invoice"
    if tone == "No action":
        return f"No follow-up needed yet for {invoice_label} ({amount_label})."
    if tone == "Warm nudge":
        return f"Send a warm nudge on {invoice_label} for {amount_label}; assume oversight and offer to resend."
    if tone == "Friendly reminder":
        return f"Send a friendly reminder on {invoice_label} for {amount_label} and confirm AP timing."
    if tone == "Polite but direct":
        return f"Ask for a firm payment date this week on {invoice_label} for {amount_label}."
    if tone == "Firm request":
        return f"State the original due date and request a specific payment date for {invoice_label} ({amount_label})."
    if age_days <= 90:
        return f"Escalate {invoice_label} ({amount_label}) to the account lead and name next-step consequences if unresolved."
    return f"Escalate {invoice_label} ({amount_label}) immediately; consider work hold or late-fee enforcement."


def build_invoice_summaries(
    budget_records: list[dict[str, Any]],
    invoice_records: list[dict[str, Any]],
    now: datetime,
    fallback_year: int,
) -> list[InvoiceSummary]:
    candidates = [record for record in budget_records if record_looks_like_invoice(record)] + invoice_records
    summaries: list[InvoiceSummary] = []

    for record in candidates:
        amount = 0.0
        for key in AMOUNT_KEYS:
            if key in record and normalize_space(record.get(key)):
                amount = parse_amount(record.get(key))
                break
        if amount <= 0:
            continue

        due_date = None
        for key in DUE_DATE_KEYS:
            due_date = parse_datetime(record.get(key), fallback_year)
            if due_date:
                break
        account = first_text(record, ACCOUNT_KEYS) or "Unknown account"
        invoice_number = first_text(record, INVOICE_NUMBER_KEYS)
        late_count = max(parse_int(first_text(record, LATE_COUNT_KEYS)), 0)
        relationship_years = parse_float(first_text(record, RELATIONSHIP_KEYS))
        age_days = compute_age_days(record, due_date, now)
        bucket = invoice_bucket(age_days)
        risk = invoice_risk(age_days, late_count, amount)
        tone = invoice_tone(age_days, late_count, relationship_years)

        summaries.append(
            InvoiceSummary(
                account=account,
                invoice_number=invoice_number,
                amount=amount,
                age_days=age_days,
                bucket=bucket,
                risk=risk,
                follow_up_tone=tone,
                recommended_action=invoice_action(invoice_number, amount, age_days, tone),
                due_date=due_date,
                late_count=late_count,
                relationship_years=relationship_years,
            )
        )

    return sorted(summaries, key=lambda item: (-item.age_days, -item.amount, item.account.lower()))


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def escape_cell(value: str) -> str:
    return normalize_space(value).replace("|", "\\|") or "—"


def aging_totals(invoices: list[InvoiceSummary]) -> dict[str, float]:
    totals = {"Current": 0.0, "1-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    for invoice in invoices:
        totals[invoice.bucket] = totals.get(invoice.bucket, 0.0) + invoice.amount
    return totals


def build_action_items(categories: list[CategorySummary], invoices: list[InvoiceSummary], event_context: EventContext | None) -> list[str]:
    actions: list[str] = []

    alerts = [item for item in categories if item.status == "ALERT"]
    if alerts:
        top = alerts[0]
        actions.append(
            f"Review {top.category} immediately: {format_currency(top.variance_amount)} over budget. {top.recommended_action}"
        )

    contingency = next((item for item in categories if item.category == "Contingency" and item.actual > 0), None)
    if contingency and event_context and event_context.days_until_event > 14:
        actions.append("Contingency has been touched before T-14. Require explicit approval before any additional draw.")

    overdue = [invoice for invoice in invoices if invoice.age_days > 0]
    if overdue:
        oldest = overdue[0]
        actions.append(
            f"Follow up on {oldest.account} {oldest.invoice_number or 'invoice'} ({format_currency(oldest.amount)}) with a {oldest.follow_up_tone.lower()} tone."
        )

    if not actions:
        actions.append("No immediate budget or receivables escalations detected. Keep monitoring run rate and payment timing.")

    return actions[:3]


def build_payload(
    event_name: str,
    generated_at: datetime,
    source: dict[str, Any],
    categories: list[CategorySummary],
    invoices: list[InvoiceSummary],
    event_context: EventContext | None,
    event_date: datetime | None,
) -> dict[str, Any]:
    total_budget = sum(item.estimated for item in categories)
    total_actual = sum(item.actual for item in categories)
    total_remaining = total_budget - total_actual
    alert_count = sum(1 for item in categories if item.status == "ALERT")
    overdue_total = sum(invoice.amount for invoice in invoices if invoice.age_days > 0)
    payload = {
        "event": event_name,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "source": source,
        "event_date": event_date.date().isoformat() if event_date else None,
        "phase": event_context.phase.value if event_context else None,
        "phase_label": event_context.phase_label if event_context else None,
        "days_until_event": event_context.days_until_event if event_context else None,
        "headline": (
            f"{format_currency(overdue_total)} is overdue and {alert_count} budget categories need attention."
            if overdue_total > 0 or alert_count > 0
            else "No immediate cash-flow or variance alert detected."
        ),
        "totals": {
            "budget": round(total_budget, 2),
            "actual": round(total_actual, 2),
            "remaining": round(total_remaining, 2),
            "percent_consumed": round((total_actual / total_budget), 4) if total_budget else None,
            "overdue_receivables": round(overdue_total, 2),
        },
        "counts": {
            "categories": len(categories),
            "alerts": alert_count,
            "invoices": len(invoices),
            "overdue_invoices": sum(1 for invoice in invoices if invoice.age_days > 0),
        },
        "aging_totals": {bucket: round(total, 2) for bucket, total in aging_totals(invoices).items()},
        "categories": [item.as_dict() for item in categories],
        "invoices": [item.as_dict() for item in invoices],
        "action_items": build_action_items(categories, invoices, event_context),
    }
    return payload


def render_dry_run_markdown(event_name: str, generated_at: datetime, source: dict[str, Any], as_json: bool) -> str:
    lines = [
        f"# Budget Variance Analysis — {event_name}",
        f"Updated: {generated_at.isoformat(timespec='seconds')}",
        "",
        "## Dry Run",
        f"- Source: `{source['type']}`",
        f"- Output format: `{'json' if as_json else 'markdown'}`",
    ]
    if source["type"] == "spreadsheet":
        lines.append(f"- Spreadsheet: `{source['spreadsheet_id']}`")
        lines.append("- Composio read skipped")
    else:
        lines.append(f"- Budget file: `{source['budget_file']}`")
        lines.append("- Local parsing skipped")
    return "\n".join(lines)


def render_markdown(payload: dict[str, Any]) -> str:
    totals = payload["totals"]
    lines = [
        f"# Budget Dashboard — {payload['event']}",
        f"Updated: {payload['generated_at']}",
    ]
    if payload.get("event_date"):
        phase_text = f" ({payload['phase_label']})" if payload.get("phase_label") else ""
        lines.append(f"Event Date: {payload['event_date']}{phase_text}")
    lines.extend(
        [
            "",
            payload["headline"],
            "",
            f"**Total Budget:** {format_currency(totals['budget'])}  |  **Spent:** {format_currency(totals['actual'])} ({format_percent(totals['percent_consumed'])})  |  **Remaining:** {format_currency(totals['remaining'])}",
            f"**Variance Alerts:** {payload['counts']['alerts']}  |  **Overdue Receivables:** {format_currency(totals['overdue_receivables'])}",
            "",
            "## Budget by Category",
            "| Category | Estimated | Actual | Variance | Var % | Threshold | Status | Cause | Recommended Action |",
            "|----------|-----------|--------|----------|-------|-----------|--------|-------|--------------------|",
        ]
    )

    for item in payload["categories"]:
        lines.append(
            "| {category} | {estimated} | {actual} | {variance} | {variance_pct} | {threshold} | {status} | {cause} | {action} |".format(
                category=escape_cell(item["category"]),
                estimated=format_currency(float(item["estimated"])),
                actual=format_currency(float(item["actual"])),
                variance=format_currency(float(item["variance_amount"])),
                variance_pct=format_percent(item.get("variance_percent")),
                threshold=format_percent(item.get("threshold_percent")),
                status=escape_cell(item["status"]),
                cause=escape_cell(item["cause"]),
                action=escape_cell(item["recommended_action"]),
            )
        )

    lines.extend(
        [
            "",
            "## Invoice Aging",
            f"Current: {format_currency(payload['aging_totals'].get('Current', 0.0))}  |  1-30: {format_currency(payload['aging_totals'].get('1-30', 0.0))}  |  31-60: {format_currency(payload['aging_totals'].get('31-60', 0.0))}  |  61-90: {format_currency(payload['aging_totals'].get('61-90', 0.0))}  |  90+: {format_currency(payload['aging_totals'].get('90+', 0.0))}",
            "",
            "| Account | Invoice # | Amount | Age | Risk | Tone | Recommended Action |",
            "|---------|-----------|--------|-----|------|------|--------------------|",
        ]
    )

    if payload["invoices"]:
        for item in payload["invoices"]:
            lines.append(
                "| {account} | {invoice} | {amount} | {age} | {risk} | {tone} | {action} |".format(
                    account=escape_cell(item["account"]),
                    invoice=escape_cell(item["invoice_number"] or "—"),
                    amount=format_currency(float(item["amount"])),
                    age=escape_cell(f"{item['age_days']}d ({item['bucket']})"),
                    risk=escape_cell(item["risk"]),
                    tone=escape_cell(item["follow_up_tone"]),
                    action=escape_cell(item["recommended_action"]),
                )
            )
    else:
        lines.append("| — | — | — | — | — | — | No invoice aging data found. |")

    lines.extend(["", "## Action Items"])
    for index, action in enumerate(payload["action_items"], start=1):
        lines.append(f"{index}. {action}")

    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    generated_at = datetime.now(tz=UTC)
    output_as_json = should_emit_json(args)

    if args.spreadsheet:
        source = {"type": "spreadsheet", "spreadsheet_id": args.spreadsheet}
    else:
        source = {"type": "budget_file", "budget_file": str(Path(args.budget_file).expanduser())}

    if args.dry_run:
        if output_as_json:
            content = json.dumps(
                {
                    "dry_run": True,
                    "event": args.event,
                    "generated_at": generated_at.isoformat(timespec="seconds"),
                    "source": source,
                },
                indent=2,
            )
        else:
            content = render_dry_run_markdown(args.event, generated_at, source, output_as_json)
        write_output(content, resolve_output_path(args.output, args.event, generated_at, output_as_json))
        return 0

    try:
        if args.spreadsheet:
            metadata, budget_records, invoice_records = fetch_spreadsheet_records(args.spreadsheet)
        else:
            metadata, budget_records, invoice_records = load_budget_file(args.budget_file)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        print(f"Failed to load budget data: {exc}", file=sys.stderr)
        return 1

    event_date = infer_event_date(metadata, budget_records, generated_at)
    event_context = EventContext(event_name=args.event, event_date=event_date, now=generated_at) if event_date else None
    categories = build_category_summaries(budget_records, event_context)
    invoices = build_invoice_summaries(budget_records, invoice_records, generated_at, (event_date or generated_at).year)
    payload = build_payload(args.event, generated_at, source, categories, invoices, event_context, event_date)

    content = json.dumps(payload, indent=2) if output_as_json else render_markdown(payload)
    write_output(content, resolve_output_path(args.output, args.event, generated_at, output_as_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


OUTPUT_JSON_SUFFIXES = {".json", ".jsonl"}
REGISTRATION_KEYS = ("email", "registration_id", "registrant_id", "attendee_id", "name")
ATTENDANCE_KEYS = ("attended", "attendance", "checked_in", "check_in", "showed_up", "status")
SOURCE_KEYS = ("channel", "source", "utm_source", "registration_source", "referrer")
MEDIUM_KEYS = ("utm_medium", "medium")
SESSION_TITLE_KEYS = ("session", "session_title", "title", "name")
SESSION_ATTENDANCE_KEYS = ("attendance", "attendees", "check_ins", "filled_seats")
SESSION_CAPACITY_KEYS = ("capacity", "room_capacity", "max_capacity")
SESSION_RATING_KEYS = ("rating", "score", "feedback_score", "avg_rating")
SESSION_FORMAT_KEYS = ("format", "session_format", "type")
SPONSOR_NAME_KEYS = ("sponsor", "sponsor_name", "account", "name")
SPONSOR_TIER_KEYS = ("tier", "sponsor_tier", "package")
SPONSOR_IMPRESSIONS_KEYS = ("impressions", "views", "logo_views", "booth_traffic")
SPONSOR_LEADS_KEYS = ("leads", "badge_scans", "qualified_leads", "meetings", "demos")
SPONSOR_INVESTMENT_KEYS = ("investment", "spend", "amount", "sponsorship_fee")
SPONSOR_SATISFACTION_KEYS = ("satisfaction", "score", "survey_score", "rating")


@dataclass(slots=True)
class RegistrationMetrics:
    registrations: int
    attendees: int | None
    attendance_rate: float | None
    channels: list[dict[str, Any]]
    direct_unknown_share: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SessionMetrics:
    title: str
    attendance: int
    capacity: int | None
    fill_rate: float | None
    rating: float | None
    format: str
    score: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SponsorMetrics:
    sponsor: str
    tier: str
    impressions: int | None
    leads: int | None
    investment: float | None
    cpl: float | None
    satisfaction: float | None
    recommendation: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["investment"] = round(self.investment, 2) if self.investment is not None else None
        payload["cpl"] = round(self.cpl, 2) if self.cpl is not None else None
        return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a structured post-event performance report from registration, session, and sponsor sheets."
    )
    parser.add_argument("--event", required=True, help="Event name.")
    parser.add_argument(
        "--date",
        required=True,
        type=parse_event_date,
        help="Event date in YYYY-MM-DD format.",
    )
    parser.add_argument("--registration-sheet", help="Spreadsheet ID for registration data.")
    parser.add_argument("--sessions-sheet", help="Spreadsheet ID for session attendance data.")
    parser.add_argument("--sponsor-sheet", help="Spreadsheet ID for sponsor ROI data.")
    parser.add_argument("--output", help="Output file path or directory. Defaults to stdout.")
    parser.add_argument("--create-doc", action="store_true", help="Create a Google Doc with the report via Composio.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the report workflow without calling Composio. Works without COMPOSIO_API_KEY.",
    )
    return parser.parse_args(argv)


def parse_event_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must be in YYYY-MM-DD format") from exc


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def canonicalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


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
        return path / f"{generated_at.date().isoformat()}-{slugify(event_name)}-post-event-report{suffix}"
    return path


def write_output(content: str, output_path: Path | None) -> None:
    if output_path is None:
        print(content)
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(str(output_path))


def should_emit_json(args: argparse.Namespace) -> bool:
    if args.json:
        return True
    if isinstance(args.output, str):
        return Path(args.output).suffix.lower() in OUTPUT_JSON_SUFFIXES
    return False


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


def fetch_sheet_records(spreadsheet_id: str) -> list[dict[str, Any]]:
    client = EventComposioClient()
    rows = extract_sheet_rows(client.read_spreadsheet(spreadsheet_id, "Sheet1"))
    return rows_to_records(rows)


def first_text(record: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_space(value)
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    match = re.search(r"-?\d+", normalize_space(value))
    return int(match.group(0)) if match else None


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", normalize_space(value).replace(",", ""))
    return float(match.group(0)) if match else None


def parse_amount(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = normalize_space(value).replace(",", "")
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    match = re.search(r"-?\d+(?:\.\d+)?", text.strip("()"))
    if not match:
        return None
    amount = float(match.group(0))
    return -amount if negative and amount > 0 else amount


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = normalize_space(value).lower()
    if not text:
        return None
    if text in {"true", "yes", "y", "1", "checked in", "attended", "showed", "present", "complete"}:
        return True
    if text in {"false", "no", "n", "0", "no show", "registered", "absent", "cancelled"}:
        return False
    return None


def format_currency(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def canonicalize_channel(source: str, medium: str = "") -> str:
    text = f"{source} {medium}".lower()
    if any(token in text for token in ("linkedin", "instagram", "facebook", "social", "x ", "twitter")):
        return "Social media"
    if any(token in text for token in ("email", "newsletter", "invite", "drip")):
        return "Email campaign"
    if any(token in text for token in ("partner", "referral", "association", "sponsor promo", "co-marketing")):
        return "Partner referral"
    if any(token in text for token in ("organic", "seo", "search", "google")):
        return "Organic / SEO"
    if any(token in text for token in ("word of mouth", "friend", "colleague", "heard from")):
        return "Word of mouth"
    return "Direct"


def record_identifier(record: dict[str, Any], fallback_index: int) -> str:
    for key in REGISTRATION_KEYS:
        value = record.get(key)
        text = normalize_space(value)
        if text:
            return text.lower()
    return f"row-{fallback_index}"


def registration_metrics(records: list[dict[str, Any]]) -> RegistrationMetrics:
    if not records:
        return RegistrationMetrics(registrations=0, attendees=None, attendance_rate=None, channels=[], direct_unknown_share=None)

    deduped: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records, start=1):
        deduped[record_identifier(record, index)] = record

    channels: dict[str, dict[str, float]] = {}
    attendee_count = 0
    attendance_known = False
    for record in deduped.values():
        attended = None
        for key in ATTENDANCE_KEYS:
            attended = parse_bool(record.get(key))
            if attended is not None:
                attendance_known = True
                break
        if attended:
            attendee_count += 1
        source = first_text(record, SOURCE_KEYS)
        medium = first_text(record, MEDIUM_KEYS)
        channel = canonicalize_channel(source, medium)
        channel_bucket = channels.setdefault(channel, {"registrations": 0.0, "attendees": 0.0})
        channel_bucket["registrations"] += 1
        if attended:
            channel_bucket["attendees"] += 1

    total_registrations = len(deduped)
    total_attendees = attendee_count if attendance_known else None
    channel_rows = []
    for channel, bucket in sorted(channels.items(), key=lambda item: (-item[1]["registrations"], item[0])):
        channel_rows.append(
            {
                "channel": channel,
                "registrations": int(bucket["registrations"]),
                "attendance_rate": (bucket["attendees"] / bucket["registrations"]) if attendance_known and bucket["registrations"] else None,
            }
        )
    direct_unknown_share = None
    direct = next((item for item in channel_rows if item["channel"] == "Direct"), None)
    if direct and total_registrations:
        direct_unknown_share = direct["registrations"] / total_registrations

    return RegistrationMetrics(
        registrations=total_registrations,
        attendees=total_attendees,
        attendance_rate=(attendee_count / total_registrations) if attendance_known and total_registrations else None,
        channels=channel_rows,
        direct_unknown_share=direct_unknown_share,
    )


def session_metrics(records: list[dict[str, Any]]) -> list[SessionMetrics]:
    metrics: list[SessionMetrics] = []
    for record in records:
        title = first_text(record, SESSION_TITLE_KEYS)
        attendance = parse_int(first_text(record, SESSION_ATTENDANCE_KEYS)) or 0
        capacity = parse_int(first_text(record, SESSION_CAPACITY_KEYS))
        rating = parse_float(first_text(record, SESSION_RATING_KEYS))
        session_format = first_text(record, SESSION_FORMAT_KEYS) or "Unknown"
        fill_rate = (attendance / capacity) if capacity and capacity > 0 else None
        score = attendance
        if fill_rate is not None:
            score += fill_rate * 100
        if rating is not None:
            score += rating * 20
        if title or attendance or capacity or rating is not None:
            metrics.append(
                SessionMetrics(
                    title=title or f"Session {len(metrics) + 1}",
                    attendance=attendance,
                    capacity=capacity,
                    fill_rate=fill_rate,
                    rating=rating,
                    format=session_format,
                    score=score,
                )
            )
    metrics.sort(key=lambda item: (-item.score, item.title.lower()))
    return metrics


def sponsor_recommendation(leads: int | None, satisfaction: float | None, cpl: float | None) -> str:
    if leads is None and satisfaction is None:
        return "Need more data"
    if leads and leads >= 20 and (satisfaction is None or satisfaction >= 4.0):
        return "Renew"
    if (satisfaction is not None and satisfaction < 3.0) or (leads is not None and leads <= 3):
        return "Decline"
    if cpl is not None and cpl > 1000:
        return "Renegotiate"
    return "Renegotiate"


def sponsor_metrics(records: list[dict[str, Any]]) -> list[SponsorMetrics]:
    metrics: list[SponsorMetrics] = []
    for record in records:
        sponsor = first_text(record, SPONSOR_NAME_KEYS)
        if not sponsor:
            continue
        tier = first_text(record, SPONSOR_TIER_KEYS) or "Unknown"
        impressions = parse_int(first_text(record, SPONSOR_IMPRESSIONS_KEYS))
        leads = parse_int(first_text(record, SPONSOR_LEADS_KEYS))
        investment = parse_amount(first_text(record, SPONSOR_INVESTMENT_KEYS))
        satisfaction = parse_float(first_text(record, SPONSOR_SATISFACTION_KEYS))
        cpl = (investment / leads) if investment is not None and leads and leads > 0 else None
        metrics.append(
            SponsorMetrics(
                sponsor=sponsor,
                tier=tier,
                impressions=impressions,
                leads=leads,
                investment=investment,
                cpl=cpl,
                satisfaction=satisfaction,
                recommendation=sponsor_recommendation(leads, satisfaction, cpl),
            )
        )
    metrics.sort(key=lambda item: (0 if item.recommendation == "Renew" else 1, -(item.leads or 0), item.sponsor.lower()))
    return metrics


def attendance_tier(rate: float | None) -> str:
    if rate is None:
        return "Mixed"
    if rate >= 0.715:
        return "Exceeded"
    if rate >= 0.585:
        return "Met"
    if rate >= 0.50:
        return "Mixed"
    return "Missed"


def average_session_fill(sessions: list[SessionMetrics]) -> float | None:
    fill_rates = [session.fill_rate for session in sessions if session.fill_rate is not None]
    if not fill_rates:
        return None
    return sum(fill_rates) / len(fill_rates)


def performance_tier(registration: RegistrationMetrics, sessions: list[SessionMetrics], sponsors: list[SponsorMetrics]) -> str:
    results = [attendance_tier(registration.attendance_rate)]
    fill_rate = average_session_fill(sessions)
    if fill_rate is not None:
        results.append("Exceeded" if fill_rate >= 0.77 else "Met" if fill_rate >= 0.63 else "Missed")
    if sponsors:
        renewals = sum(1 for sponsor in sponsors if sponsor.recommendation == "Renew")
        results.append("Met" if renewals >= max(1, len(sponsors) // 2) else "Mixed")
    unique = set(results)
    if len(unique) == 1:
        return results[0]
    if "Missed" in unique and ("Met" in unique or "Exceeded" in unique):
        return "Mixed"
    if "Exceeded" in unique and "Met" in unique:
        return "Met"
    return results[0]


def what_worked(registration: RegistrationMetrics, sessions: list[SessionMetrics], sponsors: list[SponsorMetrics]) -> list[str]:
    items: list[str] = []
    if registration.attendance_rate is not None:
        benchmark = 0.65
        if registration.attendance_rate >= benchmark:
            items.append(
                f"Attendance landed at {format_percent(registration.attendance_rate)} against a 65% conference benchmark, which suggests the pre-event conversion sequence held through show day."
            )
    if registration.channels:
        top_channel = registration.channels[0]
        items.append(
            f"{top_channel['channel']} drove the most registrations ({top_channel['registrations']}). That channel deserves first look when budget or effort gets reallocated next cycle."
        )
    if sessions:
        top_session = sessions[0]
        fill_note = f" and a {format_percent(top_session.fill_rate)} fill rate" if top_session.fill_rate is not None else ""
        items.append(
            f"{top_session.title} was the standout session with {top_session.attendance} attendees{fill_note}. Its topic, speaker, or slot should influence next year's programming mix."
        )
    if sponsors:
        best = next((sponsor for sponsor in sponsors if sponsor.recommendation == "Renew"), sponsors[0])
        leads_text = f"{best.leads} leads" if best.leads is not None else "usable exposure"
        items.append(
            f"{best.sponsor} delivered the strongest sponsor story with {leads_text}; that package is the closest thing to a renewal-ready proof point."
        )
    return items[:3]


def what_didnt_work(registration: RegistrationMetrics, sessions: list[SessionMetrics], sponsors: list[SponsorMetrics]) -> list[str]:
    items: list[str] = []
    if registration.attendance_rate is None:
        items.append("Attendance data is missing, so the report can only tell a registration story. That is a material blind spot for future debriefs.")
    elif registration.attendance_rate < 0.60:
        items.append(
            f"Show rate ended at {format_percent(registration.attendance_rate)}, below the 60-70% healthy range for paid conferences. The biggest likely issue is a weak registration-to-arrival handoff."
        )
    if registration.direct_unknown_share is not None and registration.direct_unknown_share > 0.35:
        items.append(
            f"Direct/unknown accounted for {format_percent(registration.direct_unknown_share)} of registrations. Attribution is too muddy to make confident channel budget calls."
        )
    if sessions:
        weakest = min(sessions, key=lambda item: item.score)
        weakest_fill = f" ({format_percent(weakest.fill_rate)} fill)" if weakest.fill_rate is not None else ""
        items.append(
            f"{weakest.title} underperformed with {weakest.attendance} attendees{weakest_fill}. This looks like a content, time-slot, or positioning problem rather than noise."
        )
    if sponsors:
        weak_sponsor = next((sponsor for sponsor in sponsors if sponsor.recommendation != "Renew"), None)
        if weak_sponsor is not None:
            leads = weak_sponsor.leads if weak_sponsor.leads is not None else 0
            items.append(
                f"{weak_sponsor.sponsor} is not renewal-ready yet: {leads} leads and a {weak_sponsor.recommendation.lower()} recommendation. Sponsor packaging or activation value needs work."
            )
    return items[:3]


def key_insights(registration: RegistrationMetrics, sessions: list[SessionMetrics], sponsors: list[SponsorMetrics]) -> list[str]:
    insights: list[str] = []
    if registration.channels:
        top_two = registration.channels[:2]
        channel_summary = ", ".join(f"{item['channel']} ({item['registrations']})" for item in top_two)
        insights.append(f"Registration volume concentrated in {channel_summary}; concentration is useful for scale but raises channel dependency risk.")
    if sessions:
        formats: dict[str, list[float]] = {}
        for session in sessions:
            if session.fill_rate is None:
                continue
            formats.setdefault(session.format, []).append(session.fill_rate)
        if formats:
            best_format, rates = max(formats.items(), key=lambda item: sum(item[1]) / len(item[1]))
            insights.append(f"{best_format} sessions had the strongest average fill rate. Format choice appears to matter as much as topic selection.")
    if sponsors:
        known_cpl = [sponsor.cpl for sponsor in sponsors if sponsor.cpl is not None]
        if known_cpl:
            insights.append(f"Sponsor cost-per-lead ranged around {format_currency(min(known_cpl))} to {format_currency(max(known_cpl))}, which is enough spread to justify tier/package changes.")
    if not insights:
        insights.append("Data is incomplete, so the clearest insight is operational: future reports need cleaner registration, attendance, and sponsor source data.")
    return insights[:3]


def recommendations(registration: RegistrationMetrics, sessions: list[SessionMetrics], sponsors: list[SponsorMetrics]) -> list[str]:
    items: list[str] = []
    if registration.attendance_rate is not None and registration.attendance_rate < 0.60:
        items.append(
            "Start the reconfirmation sequence earlier and add a week-of attendance nudge — the current registration-to-show conversion is leaving too much value on the table."
        )
    elif registration.attendance_rate is None:
        items.append("Instrument attendance capture next time so the debrief can measure show rate, no-show sources, and source-level quality instead of registrations alone.")
    if registration.direct_unknown_share is not None and registration.direct_unknown_share > 0.35:
        items.append("Tighten UTM discipline across every campaign and partner push. Direct/unknown is too large to support confident attribution decisions.")
    if sessions:
        weakest = min(sessions, key=lambda item: item.score)
        items.append(
            f"Rework or reslot sessions like {weakest.title}; the current content/slot mix is suppressing room fill and should be changed before next year's agenda locks."
        )
    if sponsors:
        weak = next((sponsor for sponsor in sponsors if sponsor.recommendation != "Renew"), sponsors[0])
        items.append(
            f"Use {weak.sponsor} as the test case for sponsor package redesign. Shift value toward measurable leads, meetings, or better booth placement instead of passive impressions."
        )
    while len(items) < 3:
        items.append("Keep the headline-first reporting format: verdict, what worked, what failed, and then the tables. It makes the debrief more useful to clients and internal teams.")
    return items[:3]


def sponsor_summary_table(sponsors: list[SponsorMetrics]) -> list[dict[str, Any]]:
    return [item.as_dict() for item in sponsors]


def attendee_journey(registration: RegistrationMetrics, sessions: list[SessionMetrics]) -> dict[str, str]:
    top_channel = registration.channels[0]["channel"] if registration.channels else "n/a"
    avg_fill = average_session_fill(sessions)
    drop_off = (
        f"Registration to attendance ({format_percent(registration.attendance_rate)})"
        if registration.attendance_rate is not None and registration.attendance_rate < 0.60
        else "Session participation" if avg_fill is not None and avg_fill < 0.65 else "No major drop-off confirmed"
    )
    return {
        "registration": f"{registration.registrations} registrations with {top_channel} as the biggest source.",
        "pre_event_comms": "Attribution is directional; the best evidence is the channel mix, not a single claimed winner.",
        "arrival": (
            f"{registration.attendees} attendees checked in ({format_percent(registration.attendance_rate)} show rate)."
            if registration.attendees is not None
            else "Attendance data unavailable."
        ),
        "participation": (
            f"Average session fill rate was {format_percent(avg_fill)}."
            if avg_fill is not None
            else "Session participation data unavailable."
        ),
        "exit": "Exit feedback was not provided in these sheets, so post-event sentiment should be treated as incomplete.",
        "drop_off": drop_off,
    }


def build_payload(
    event_name: str,
    generated_at: datetime,
    event_context: EventContext,
    registration: RegistrationMetrics,
    sessions: list[SessionMetrics],
    sponsors: list[SponsorMetrics],
    doc_result: dict[str, Any] | None,
    sources: dict[str, Any],
) -> dict[str, Any]:
    tier = performance_tier(registration, sessions, sponsors)
    verdict = (
        f"{event_name} finished in the {tier} tier. "
        f"Registration-to-attendance came in at {format_percent(registration.attendance_rate)}."
        if registration.attendance_rate is not None
        else f"{event_name} finished in the {tier} tier, but the debrief is limited because attendance data is missing."
    )
    return {
        "event": event_name,
        "event_date": event_context.event_date.date().isoformat(),
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "phase": event_context.phase.value,
        "phase_label": event_context.phase_label,
        "sources": sources,
        "performance_tier": tier,
        "verdict": verdict,
        "registration": registration.as_dict(),
        "sessions": [item.as_dict() for item in sessions],
        "sponsors": sponsor_summary_table(sponsors),
        "what_worked": what_worked(registration, sessions, sponsors),
        "what_didnt_work": what_didnt_work(registration, sessions, sponsors),
        "key_insights": key_insights(registration, sessions, sponsors),
        "recommendations": recommendations(registration, sessions, sponsors),
        "attendee_journey": attendee_journey(registration, sessions),
        "doc": doc_result,
    }


def escape_cell(value: str) -> str:
    return normalize_space(value).replace("|", "\\|") or "—"


def render_markdown(payload: dict[str, Any]) -> str:
    registration = payload["registration"]
    lines = [
        "## Event Performance Summary",
        payload["verdict"],
        "",
        "## What Worked",
    ]
    for item in payload["what_worked"]:
        lines.append(f"- {item}")
    lines.extend(["", "## What Didn't Work"])
    for item in payload["what_didnt_work"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Key Insights"])
    for item in payload["key_insights"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommendations for Next Event"])
    for index, item in enumerate(payload["recommendations"], start=1):
        lines.append(f"{index}. {item}")

    lines.extend([
        "",
        "## Registration + Attribution Snapshot",
        f"- Registrations: {registration['registrations']}",
        f"- Attendance: {registration['attendees'] if registration['attendees'] is not None else 'n/a'}",
        f"- Show rate: {format_percent(registration['attendance_rate'])}",
        "",
        "| Channel | Registrations | Attendance Rate |",
        "|---------|---------------|-----------------|",
    ])
    for channel in registration["channels"]:
        lines.append(
            f"| {escape_cell(channel['channel'])} | {channel['registrations']} | {format_percent(channel['attendance_rate'])} |"
        )
    if not registration["channels"]:
        lines.append("| n/a | 0 | n/a |")

    lines.extend(["", "## Session Rankings", "| Session | Attendance | Fill Rate | Rating | Format |", "|---------|------------|-----------|--------|--------|"])
    for session in payload["sessions"][:10]:
        lines.append(
            f"| {escape_cell(session['title'])} | {session['attendance']} | {format_percent(session['fill_rate'])} | {session['rating'] if session['rating'] is not None else 'n/a'} | {escape_cell(session['format'])} |"
        )
    if not payload["sessions"]:
        lines.append("| n/a | 0 | n/a | n/a | n/a |")

    lines.extend(["", "## Sponsor ROI Summary", "| Sponsor | Tier | Impressions | Leads | CPL | Satisfaction | Recommendation |", "|---------|------|-------------|-------|-----|--------------|----------------|"])
    for sponsor in payload["sponsors"]:
        lines.append(
            f"| {escape_cell(sponsor['sponsor'])} | {escape_cell(sponsor['tier'])} | {sponsor['impressions'] if sponsor['impressions'] is not None else 'n/a'} | {sponsor['leads'] if sponsor['leads'] is not None else 'n/a'} | {format_currency(sponsor['cpl'])} | {sponsor['satisfaction'] if sponsor['satisfaction'] is not None else 'n/a'} | {escape_cell(sponsor['recommendation'])} |"
        )
    if not payload["sponsors"]:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | Need more data |")

    journey = payload["attendee_journey"]
    lines.extend(
        [
            "",
            "## Attendee Journey",
            f"- Registration: {journey['registration']}",
            f"- Pre-event comms: {journey['pre_event_comms']}",
            f"- Arrival: {journey['arrival']}",
            f"- Participation: {journey['participation']}",
            f"- Exit: {journey['exit']}",
            f"- Drop-off point: {journey['drop_off']}",
            "",
            "## Thank You + Forward Look",
            f"Thank you for trusting the team with {payload['event']}. The next event will improve fastest if we act on the weak spots above before planning hardens.",
        ]
    )

    if payload.get("doc"):
        lines.extend(["", "## Google Doc", f"- Created: {json.dumps(payload['doc'])}"])

    return "\n".join(lines).strip() + "\n"


def render_dry_run_markdown(event_name: str, generated_at: datetime, event_context: EventContext, sources: dict[str, Any], as_json: bool, create_doc: bool) -> str:
    lines = [
        f"# Post-Event Report Generator — {event_name}",
        f"Updated: {generated_at.isoformat(timespec='seconds')}",
        f"Event Date: {event_context.event_date.date().isoformat()} ({event_context.phase_label})",
        "",
        "## Dry Run",
        f"- Output format: `{'json' if as_json else 'markdown'}`",
        f"- Registration sheet: `{sources.get('registration_sheet') or 'not provided'}`",
        f"- Sessions sheet: `{sources.get('sessions_sheet') or 'not provided'}`",
        f"- Sponsor sheet: `{sources.get('sponsor_sheet') or 'not provided'}`",
        f"- Google Doc creation: `{'enabled' if create_doc else 'disabled'}`",
        "- Composio reads skipped",
    ]
    return "\n".join(lines)


def create_doc_if_requested(create_doc: bool, markdown: str, title: str) -> dict[str, Any] | None:
    if not create_doc:
        return None
    client = EventComposioClient()
    result = client.create_document(title=title, body=markdown)
    unwrapped = unwrap_action_result(result)
    return unwrapped if isinstance(unwrapped, dict) else {"result": unwrapped}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not any((args.registration_sheet, args.sessions_sheet, args.sponsor_sheet)):
        print("At least one of --registration-sheet, --sessions-sheet, or --sponsor-sheet is required.", file=sys.stderr)
        return 1

    generated_at = datetime.now(tz=UTC)
    event_context = EventContext(event_name=args.event, event_date=args.date, now=generated_at)
    output_as_json = should_emit_json(args)
    sources = {
        "registration_sheet": args.registration_sheet,
        "sessions_sheet": args.sessions_sheet,
        "sponsor_sheet": args.sponsor_sheet,
    }

    if args.dry_run:
        if output_as_json:
            content = json.dumps(
                {
                    "dry_run": True,
                    "event": args.event,
                    "event_date": args.date.date().isoformat(),
                    "generated_at": generated_at.isoformat(timespec="seconds"),
                    "sources": sources,
                    "create_doc": args.create_doc,
                },
                indent=2,
            )
        else:
            content = render_dry_run_markdown(args.event, generated_at, event_context, sources, output_as_json, args.create_doc)
        write_output(content, resolve_output_path(args.output, args.event, generated_at, output_as_json))
        return 0

    try:
        registration_records = fetch_sheet_records(args.registration_sheet) if args.registration_sheet else []
        session_records = fetch_sheet_records(args.sessions_sheet) if args.sessions_sheet else []
        sponsor_records = fetch_sheet_records(args.sponsor_sheet) if args.sponsor_sheet else []
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        print(f"Failed to load spreadsheet data: {exc}", file=sys.stderr)
        return 1

    registration = registration_metrics(registration_records)
    sessions = session_metrics(session_records)
    sponsors = sponsor_metrics(sponsor_records)
    markdown_preview = render_markdown(
        build_payload(
            args.event,
            generated_at,
            event_context,
            registration,
            sessions,
            sponsors,
            None,
            sources,
        )
    )

    doc_result = None
    if args.create_doc:
        try:
            doc_result = create_doc_if_requested(
                create_doc=True,
                markdown=markdown_preview,
                title=f"{args.event} post-event report — {args.date.date().isoformat()}",
            )
        except SystemExit as exc:
            return int(exc.code) if isinstance(exc.code, int) else 1
        except Exception as exc:
            print(f"Failed to create Google Doc: {exc}", file=sys.stderr)
            return 1

    payload = build_payload(args.event, generated_at, event_context, registration, sessions, sponsors, doc_result, sources)
    content = json.dumps(payload, indent=2) if output_as_json else render_markdown(payload)
    write_output(content, resolve_output_path(args.output, args.event, generated_at, output_as_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

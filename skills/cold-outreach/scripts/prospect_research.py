# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedCallResult=false, reportUnusedParameter=false
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.composio_client import EventComposioClient
from lib.event_context import EventContext


ROLE_TYPES = ("buyer", "sponsor", "speaker", "vendor", "media")
OUTPUT_JSON_SUFFIXES = {".json", ".jsonl"}
COMMON_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "with",
    "your",
}

ROLE_SIGNALS: dict[str, tuple[str, ...]] = {
    "speaker": (
        "speaker",
        "keynote",
        "panel",
        "moderator",
        "author",
        "analyst",
        "evangelist",
        "thought leader",
        "founder",
        "ceo",
    ),
    "sponsor": (
        "sponsor",
        "partnership",
        "marketing",
        "brand",
        "field marketing",
        "demand gen",
        "growth",
        "revenue",
        "community",
    ),
    "vendor": (
        "vendor",
        "supplier",
        "solution",
        "platform",
        "agency",
        "services",
        "production",
        "sales",
        "business development",
    ),
    "media": (
        "media",
        "press",
        "editor",
        "journalist",
        "reporter",
        "producer",
        "podcast",
        "publication",
        "newsletter",
    ),
    "buyer": (
        "buyer",
        "procurement",
        "sourcing",
        "merchandising",
        "category",
        "partnerships",
        "operations",
        "strategy",
        "director",
        "manager",
    ),
}


@dataclass(slots=True)
class Prospect:
    name: str
    company: str
    role: str
    email: str
    role_type: str
    source: str
    notes: str = ""
    company_domain: str = ""
    data_gaps: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProspectProfile:
    name: str
    company: str
    role: str
    email: str
    role_type: str
    source: str
    event_name: str
    event_brief: str
    event_date: str
    event_phase: str
    days_until_event: int
    personalization_hook: str
    recommended_angle: dict[str, Any]
    value_proposition: str
    recommended_cta: str
    supporting_points: list[str]
    company_domain: str
    data_gaps: list[str]
    ready_for_outreach: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Research cold-outreach prospects and recommend role-specific event angles."
    )
    parser.add_argument(
        "--event",
        required=True,
        help="Event name and description.",
    )
    parser.add_argument(
        "--date",
        required=True,
        type=parse_event_date,
        help="Event date in YYYY-MM-DD format.",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--prospects",
        help="Path to a CSV or JSON prospect list.",
    )
    source_group.add_argument(
        "--hubspot-query",
        help="HubSpot contact search query via Composio.",
    )
    parser.add_argument(
        "--role-type",
        default="auto-detect",
        choices=("auto-detect", *ROLE_TYPES),
        help="Override detected role type for all prospects.",
    )
    parser.add_argument(
        "--output",
        help="Write output to a file instead of stdout.",
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


def split_event_brief(raw_event: str) -> tuple[str, str]:
    event_text = normalize_space(raw_event)
    for separator in (" — ", " – ", ": ", " - "):
        if separator in event_text:
            name, description = event_text.split(separator, 1)
            if name.strip() and description.strip():
                return name.strip(), description.strip()
    return event_text, event_text


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return normalize_space(value)
    return ""


def maybe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "[{":
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def unwrap_payload(value: Any) -> Any:
    current = maybe_json(value)
    for _ in range(8):
        current = maybe_json(current)
        if isinstance(current, dict):
            if current.get("error"):
                raise RuntimeError(str(current["error"]))
            if "data" in current:
                current = current["data"]
                continue
            if "response" in current:
                current = current["response"]
                continue
        break
    return current


def load_prospects(path_value: str, role_override: str) -> list[Prospect]:
    path = Path(path_value).expanduser()
    if not path.exists():
        raise SystemExit(f"Prospect file not found: {path}")

    if path.suffix.lower() == ".csv":
        rows = load_csv_rows(path)
    elif path.suffix.lower() == ".json":
        rows = load_json_rows(path)
    else:
        raise SystemExit("--prospects must point to a .csv or .json file")

    prospects = [normalize_prospect(row, role_override, source="file") for row in rows]
    return [prospect for prospect in prospects if prospect is not None]


def load_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{str(key): value for key, value in row.items()} for row in reader]


def load_json_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    node: Any = payload
    if isinstance(node, dict):
        for key in ("prospects", "profiles", "contacts", "results", "items", "data"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                node = candidate
                break

    if not isinstance(node, list):
        raise SystemExit("JSON prospect file must contain a list or an object with a list field")

    return [item for item in node if isinstance(item, dict)]


def fetch_hubspot_prospects(query: str, role_override: str) -> list[Prospect]:
    client = EventComposioClient()
    raw_results = unwrap_payload(client.hubspot_search_contacts(query=query, limit=25))
    records = extract_record_list(raw_results)
    prospects = [normalize_prospect(record, role_override, source="hubspot") for record in records]
    return [prospect for prospect in prospects if prospect is not None]


def extract_record_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        for key in ("results", "contacts", "items", "records"):
            candidate = value.get(key)
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
        if any(key in value for key in ("properties", "email", "firstname", "lastName")):
            return [value]
        for nested in value.values():
            nested_records = extract_record_list(nested)
            if nested_records:
                return nested_records

    return []


def normalize_prospect(
    raw_record: dict[str, Any],
    role_override: str,
    source: str,
) -> Prospect | None:
    properties = raw_record.get("properties")
    property_map = properties if isinstance(properties, dict) else {}

    first_name = first_text(
        raw_record.get("first_name"),
        raw_record.get("firstName"),
        property_map.get("firstname"),
    )
    last_name = first_text(
        raw_record.get("last_name"),
        raw_record.get("lastName"),
        property_map.get("lastname"),
    )
    combined_name = normalize_space(" ".join(part for part in (first_name, last_name) if part))
    name = first_text(raw_record.get("name"), raw_record.get("full_name"), combined_name)

    company = first_text(
        raw_record.get("company"),
        raw_record.get("organization"),
        raw_record.get("employer"),
        property_map.get("company"),
        property_map.get("organization"),
    )
    role = first_text(
        raw_record.get("role"),
        raw_record.get("title"),
        raw_record.get("job_title"),
        raw_record.get("jobTitle"),
        property_map.get("jobtitle"),
        property_map.get("title"),
    )
    email = first_text(
        raw_record.get("email"),
        property_map.get("email"),
        raw_record.get("primary_email"),
    ).lower()
    notes = first_text(
        raw_record.get("notes"),
        raw_record.get("description"),
        property_map.get("hs_lead_status"),
        property_map.get("lifecyclestage"),
    )
    company_domain = infer_company_domain(email, raw_record, property_map)
    role_type = detect_role_type(role_override, role, company, notes)

    data_gaps: list[str] = []
    if not name:
        data_gaps.append("missing_name")
        name = "Unknown Prospect"
    if not company:
        data_gaps.append("missing_company")
        company = company_domain or "Unknown Company"
    if not role:
        data_gaps.append("missing_role")
        role = "Unknown Role"
    if not email:
        data_gaps.append("missing_email")

    if not any((name, company, role, email)):
        return None

    return Prospect(
        name=name,
        company=company,
        role=role,
        email=email,
        role_type=role_type,
        source=source,
        notes=notes,
        company_domain=company_domain,
        data_gaps=data_gaps,
    )


def infer_company_domain(email: str, raw_record: dict[str, Any], properties: dict[str, Any]) -> str:
    if "@" in email:
        return email.rsplit("@", 1)[-1]
    website = first_text(raw_record.get("website"), properties.get("website"), properties.get("domain"))
    cleaned = website.replace("https://", "").replace("http://", "").strip("/")
    return cleaned.lower()


def detect_role_type(role_override: str, role: str, company: str, notes: str) -> str:
    if role_override != "auto-detect":
        return role_override

    haystack = f"{role} {company} {notes}".lower()
    for role_type in ("speaker", "media", "sponsor", "vendor"):
        if any(signal in haystack for signal in ROLE_SIGNALS[role_type]):
            return role_type
    if any(signal in haystack for signal in ROLE_SIGNALS["buyer"]):
        return "buyer"
    return "buyer"


def extract_event_themes(event_brief: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9&+-]{3,}", event_brief.lower())
    themes: list[str] = []
    for token in tokens:
        if token in COMMON_STOPWORDS:
            continue
        if token.isdigit():
            continue
        if token not in themes:
            themes.append(token)
        if len(themes) == 5:
            break
    return themes


def build_profiles(
    prospects: list[Prospect],
    event_brief: str,
    event_name: str,
    event_context: EventContext,
) -> list[ProspectProfile]:
    themes = extract_event_themes(event_brief)
    return [
        build_profile(prospect=prospect, event_brief=event_brief, event_name=event_name, event_context=event_context, themes=themes)
        for prospect in prospects
    ]


def build_profile(
    prospect: Prospect,
    event_brief: str,
    event_name: str,
    event_context: EventContext,
    themes: list[str],
) -> ProspectProfile:
    angle = build_role_angle(prospect, event_name, event_brief, event_context, themes)
    ready_for_outreach = not prospect.data_gaps

    return ProspectProfile(
        name=prospect.name,
        company=prospect.company,
        role=prospect.role,
        email=prospect.email,
        role_type=prospect.role_type,
        source=prospect.source,
        event_name=event_name,
        event_brief=event_brief,
        event_date=event_context.event_date.date().isoformat(),
        event_phase=event_context.phase_label,
        days_until_event=event_context.days_until_event,
        personalization_hook=angle["personalization_hook"],
        recommended_angle=angle["recommended_angle"],
        value_proposition=angle["value_proposition"],
        recommended_cta=angle["recommended_cta"],
        supporting_points=angle["supporting_points"],
        company_domain=prospect.company_domain,
        data_gaps=prospect.data_gaps,
        ready_for_outreach=ready_for_outreach,
    )


def build_role_angle(
    prospect: Prospect,
    event_name: str,
    event_brief: str,
    event_context: EventContext,
    themes: list[str],
) -> dict[str, Any]:
    theme_phrase = format_theme_phrase(themes)
    phase_note = phase_message(event_context)

    if prospect.role_type == "buyer":
        return build_buyer_angle(prospect, event_name, event_brief, theme_phrase, phase_note)
    if prospect.role_type == "sponsor":
        return build_sponsor_angle(prospect, event_name, event_brief, theme_phrase, phase_note)
    if prospect.role_type == "speaker":
        return build_speaker_angle(prospect, event_name, event_brief, theme_phrase, phase_note)
    if prospect.role_type == "vendor":
        return build_vendor_angle(prospect, event_name, event_brief, theme_phrase, phase_note)
    return build_media_angle(prospect, event_name, event_brief, theme_phrase, phase_note)


def format_theme_phrase(themes: list[str]) -> str:
    if not themes:
        return "the core buying and partnership conversations around the event"
    if len(themes) == 1:
        return themes[0]
    if len(themes) == 2:
        return f"{themes[0]} and {themes[1]}"
    return f"{', '.join(themes[:2])}, and {themes[2]}"


def phase_message(event_context: EventContext) -> str:
    days = event_context.days_until_event
    if days <= 0:
        return "the event timing is immediate, so any outreach should be direct and availability-focused"
    if days <= 14:
        return "the event window is close enough that calendars and activation plans will already be tightening"
    if days <= 45:
        return "there is still time to shape meetings, programming, and partner positioning instead of reacting late"
    return "there is enough runway to position the event as a strategic decision rather than a last-minute invitation"


def build_buyer_angle(
    prospect: Prospect,
    event_name: str,
    event_brief: str,
    theme_phrase: str,
    phase_note: str,
) -> dict[str, Any]:
    role_lower = prospect.role.lower()
    if any(keyword in role_lower for keyword in ("buyer", "procurement", "sourcing", "merch")):
        primary = "networking_roi"
        angle_summary = f"Lead with networking ROI: show how {event_name} compresses the right conversations for {prospect.company}."
    elif any(keyword in role_lower for keyword in ("chief", "vp", "head", "director")):
        primary = "attendance_value"
        angle_summary = f"Lead with attendance value: frame {event_name} as a high-signal room instead of another generic conference."
    else:
        primary = "content_quality"
        angle_summary = f"Lead with content quality: position {event_name} as useful because the agenda is built around {theme_phrase}."

    hook = (
        f"{prospect.company} is likely evaluating event time through the lens of buyer efficiency, so the message should start with how a {prospect.role} can leave {event_name} with better conversations around {theme_phrase}."
    )
    value = (
        f"The strongest buyer angle for {prospect.company} is that {event_name} combines attendee value, networking ROI, and content quality in one room. Instead of selling the event itself, position it as a faster way for {prospect.name} to pressure-test suppliers, benchmark the market, and prioritize the sessions that matter most to a {prospect.role}."
    )
    cta = f"Offer to send the attendee and session pockets that would be highest value for {prospect.company}."
    supporting_points = [
        f"Attendance value: emphasize that the event is relevant because the audience is gathered around {theme_phrase}, not because it is merely large.",
        f"Networking ROI: connect the trip to a smaller number of sharper meetings for {prospect.company}.",
        f"Content quality: tie the agenda back to the real decisions someone in {prospect.role} is making right now.",
        phase_note,
        f"Use the event brief naturally: {event_brief}.",
    ]
    return angle_payload(primary, angle_summary, hook, value, cta, supporting_points)


def build_sponsor_angle(
    prospect: Prospect,
    event_name: str,
    event_brief: str,
    theme_phrase: str,
    phase_note: str,
) -> dict[str, Any]:
    role_lower = prospect.role.lower()
    if any(keyword in role_lower for keyword in ("partnership", "event", "field marketing", "brand")):
        primary = "activation_opportunities"
        angle_summary = f"Lead with activation opportunities: suggest a concrete way {prospect.company} can show up at {event_name}."
    elif any(keyword in role_lower for keyword in ("marketing", "growth", "revenue", "demand")):
        primary = "audience_demographics"
        angle_summary = f"Lead with audience demographics: map the room at {event_name} to the buyers {prospect.company} needs to influence."
    else:
        primary = "competitor_presence"
        angle_summary = f"Lead with competitor presence: frame the event as a visibility moment where peers may already be shaping the category conversation."

    hook = (
        f"A sponsor message to {prospect.name} should feel like a growth idea, not a package sale. Anchor it in the demographic overlap between {event_name} and the audience {prospect.company} wants around {theme_phrase}."
    )
    value = (
        f"The most credible sponsor value proposition for {prospect.company} is audience fit plus a specific activation concept. Position {event_name} as a place to create useful brand moments for the right decision-makers, then show how sponsorship can open a sharper conversation than a generic logo placement would."
    )
    cta = f"Invite {prospect.name} to review one tailored activation concept for {prospect.company}."
    supporting_points = [
        "Audience demographics: tie the room to the customer profile they are trying to reach.",
        f"Activation opportunities: suggest one specific footprint, lounge, session, or hosted moment that suits {prospect.company}.",
        "Competitor presence: use peer visibility as urgency without inventing competitor names.",
        phase_note,
        f"Reference the event brief directly: {event_brief}.",
    ]
    return angle_payload(primary, angle_summary, hook, value, cta, supporting_points)


def build_speaker_angle(
    prospect: Prospect,
    event_name: str,
    event_brief: str,
    theme_phrase: str,
    phase_note: str,
) -> dict[str, Any]:
    role_lower = prospect.role.lower()
    if any(keyword in role_lower for keyword in ("founder", "ceo", "president", "chief")):
        primary = "stage_size"
        angle_summary = f"Lead with stage size: show why {prospect.name}'s perspective deserves a visible slot at {event_name}."
    elif any(keyword in role_lower for keyword in ("research", "product", "strategy", "content", "analyst")):
        primary = "content_fit"
        angle_summary = f"Lead with content fit: connect {prospect.name}'s expertise to the audience questions inside {event_name}."
    else:
        primary = "audience_profile"
        angle_summary = f"Lead with audience profile: explain who will benefit from hearing {prospect.name} at {event_name}."

    hook = (
        f"For a speaker prospect, the opening should explain why attendees at {event_name} need {prospect.name}'s specific lens on {theme_phrase}, not why the event is prestigious."
    )
    value = (
        f"The clearest speaker proposition for {prospect.company} is audience fit plus transparent logistics. Frame {event_name} as a place where {prospect.name}'s expertise can land with the right audience, then make it easy to understand the format, stage visibility, and travel or compensation conversation upfront."
    )
    cta = f"Ask whether {prospect.name} is open to a short conversation about the format and practical details for {event_name}."
    supporting_points = [
        "Stage size: position the slot as visible enough to matter without overselling scale.",
        "Audience profile: describe the people who would benefit from their point of view.",
        f"Content fit: connect their role at {prospect.company} to the event's core topic areas around {theme_phrase}.",
        "Travel and comp details: be direct so the invite feels serious.",
        phase_note,
        f"Work from the event brief: {event_brief}.",
    ]
    return angle_payload(primary, angle_summary, hook, value, cta, supporting_points)


def build_vendor_angle(
    prospect: Prospect,
    event_name: str,
    event_brief: str,
    theme_phrase: str,
    phase_note: str,
) -> dict[str, Any]:
    role_lower = prospect.role.lower()
    if any(keyword in role_lower for keyword in ("sales", "business development", "partnership")):
        primary = "multi_event_pipeline"
        angle_summary = f"Lead with multi-event pipeline: frame the relationship as more than a one-off project for {event_name}."
    elif any(keyword in role_lower for keyword in ("operations", "production", "delivery")):
        primary = "event_scale"
        angle_summary = f"Lead with event scale: show the operational scope and seriousness of {event_name}."
    else:
        primary = "preferred_vendor_status"
        angle_summary = f"Lead with preferred vendor status: position {prospect.company} as a partner worth building with over time."

    hook = (
        f"A vendor prospect should hear how {event_name} fits their revenue model: either meaningful event scale now, a cleaner path to preferred status, or a broader pipeline beyond a single show."
    )
    value = (
        f"The vendor angle for {prospect.company} should connect event scale, long-term pipeline, and preferred-vendor upside. Instead of sounding like procurement, frame the outreach as a business-development conversation about how {prospect.company} could support this event category well."
    )
    cta = f"Invite {prospect.name} to review where {prospect.company} could fit into the event pipeline around {event_name}."
    supporting_points = [
        "Event scale: describe the seriousness of the production or attendee footprint without inventing metrics.",
        "Multi-event pipeline: suggest a relationship that can extend beyond a single event cycle.",
        f"Preferred vendor status: signal that strong partners can earn repeat visibility with the team behind {event_name}.",
        phase_note,
        f"Keep the event story grounded in the brief: {event_brief}.",
    ]
    return angle_payload(primary, angle_summary, hook, value, cta, supporting_points)


def build_media_angle(
    prospect: Prospect,
    event_name: str,
    event_brief: str,
    theme_phrase: str,
    phase_note: str,
) -> dict[str, Any]:
    role_lower = prospect.role.lower()
    if any(keyword in role_lower for keyword in ("editor", "journalist", "reporter")):
        primary = "exclusivity"
        angle_summary = f"Lead with exclusivity: show the editorial value of a differentiated angle around {event_name}."
    elif any(keyword in role_lower for keyword in ("producer", "podcast", "host")):
        primary = "content_access"
        angle_summary = f"Lead with content access: highlight the conversations and voices {prospect.company} could unlock at {event_name}."
    else:
        primary = "audience_reach"
        angle_summary = f"Lead with audience reach: connect the event to an audience story that matters for {prospect.company}."

    hook = (
        f"A media angle should sound editorial, not promotional. Tie {event_name} to the exclusivity, content access, and audience reach that would make coverage useful for {prospect.company}."
    )
    value = (
        f"The strongest media proposition for {prospect.company} is a clear reporting or audience angle. Show how {event_name} can give {prospect.name} better access to people, conversations, and thematic stories around {theme_phrase} without sounding like a publicity blast."
    )
    cta = f"Ask whether {prospect.name} wants the most coverage-worthy angles and access options for {event_name}."
    supporting_points = [
        "Exclusivity: offer differentiated access or perspective instead of generic press language.",
        "Content access: point to interviews, backstage context, or session access that would matter editorially.",
        f"Audience reach: explain why the conversations around {event_name} matter to {prospect.company}'s readership or listeners.",
        phase_note,
        f"Use the actual event framing: {event_brief}.",
    ]
    return angle_payload(primary, angle_summary, hook, value, cta, supporting_points)


def angle_payload(
    primary: str,
    angle_summary: str,
    personalization_hook: str,
    value_proposition: str,
    recommended_cta: str,
    supporting_points: list[str],
) -> dict[str, Any]:
    return {
        "personalization_hook": personalization_hook,
        "recommended_angle": {
            "primary": primary,
            "summary": angle_summary,
        },
        "value_proposition": value_proposition,
        "recommended_cta": recommended_cta,
        "supporting_points": supporting_points,
    }


def output_payload(
    profiles: list[ProspectProfile],
    event_name: str,
    event_brief: str,
    event_context: EventContext,
) -> dict[str, Any]:
    return {
        "event": {
            "name": event_name,
            "brief": event_brief,
            "date": event_context.event_date.date().isoformat(),
            "phase": event_context.phase_label,
            "days_until_event": event_context.days_until_event,
        },
        "profiles": [profile.as_dict() for profile in profiles],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    event = payload["event"]
    lines = [
        f"# Prospect Research — {event['name']}",
        "",
        f"- Event date: {event['date']}",
        f"- Event phase: {event['phase']}",
        f"- Days until event: {event['days_until_event']}",
        "",
    ]

    profiles = payload.get("profiles", [])
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        angle = profile.get("recommended_angle", {})
        lines.extend(
            [
                f"## {profile.get('name', 'Unknown')} — {profile.get('company', 'Unknown Company')}",
                "",
                f"- Role: {profile.get('role', 'Unknown Role')}",
                f"- Role type: {profile.get('role_type', 'unknown')}",
                f"- Email: {profile.get('email') or 'missing'}",
                f"- Angle: {angle.get('summary', '')}",
                f"- Hook: {profile.get('personalization_hook', '')}",
                f"- Value proposition: {profile.get('value_proposition', '')}",
                f"- CTA: {profile.get('recommended_cta', '')}",
            ]
        )
        supporting_points = profile.get("supporting_points", [])
        if isinstance(supporting_points, list) and supporting_points:
            lines.append("- Supporting points:")
            for item in supporting_points:
                lines.append(f"  - {item}")
        data_gaps = profile.get("data_gaps", [])
        if isinstance(data_gaps, list) and data_gaps:
            lines.append(f"- Data gaps: {', '.join(data_gaps)}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_output(text: str, path_value: str | None) -> None:
    if not path_value:
        print(text)
        return

    path = Path(path_value).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def should_emit_json(args: argparse.Namespace) -> bool:
    if args.json:
        return True
    if isinstance(args.output, str):
        return Path(args.output).suffix.lower() in OUTPUT_JSON_SUFFIXES
    return False


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    event_name, event_brief = split_event_brief(args.event)
    event_context = EventContext(event_name=event_name, event_date=args.date)

    if args.prospects:
        prospects = load_prospects(args.prospects, args.role_type)
    else:
        prospects = fetch_hubspot_prospects(args.hubspot_query, args.role_type)

    if not prospects:
        raise SystemExit("No prospects found.")

    profiles = build_profiles(
        prospects=prospects,
        event_brief=event_brief,
        event_name=event_name,
        event_context=event_context,
    )
    payload = output_payload(
        profiles=profiles,
        event_name=event_name,
        event_brief=event_brief,
        event_context=event_context,
    )

    if should_emit_json(args):
        text = json.dumps(payload, indent=2)
    else:
        text = render_markdown(payload)
    write_output(text, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

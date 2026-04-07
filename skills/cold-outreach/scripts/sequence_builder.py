# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedCallResult=false, reportUnusedParameter=false
from __future__ import annotations

import argparse
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


PURPOSES = ("intro", "follow_up", "value_add", "break_up")
BANNED_PHRASES = (
    "i hope this email finds you well",
    "just following up",
    "circling back",
    "touching base",
    "quick question",
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "but",
    "for",
    "from",
    "have",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "so",
    "that",
    "the",
    "their",
    "this",
    "to",
    "we",
    "with",
    "you",
    "your",
}
INSIGHT_LIBRARY: dict[str, tuple[str, str]] = {
    "buyer": (
        "Why attendance ROI is now about better meetings, not more meetings",
        "Teams are getting stricter about travel approvals, so the strongest event attendance cases now come down to whether the room produces sharper conversations and faster decisions.",
    ),
    "sponsor": (
        "Why sponsors are shifting from logo spend to guided activation",
        "The strongest event programs are moving budget toward experiences that create useful conversations, because passive visibility is harder to defend than measurable buyer interaction.",
    ),
    "speaker": (
        "Why audiences now reward speakers who solve a live operator problem",
        "The sessions that travel furthest after an event tend to be the ones that help an audience act differently the next week, not the ones that only sound impressive on stage.",
    ),
    "vendor": (
        "Why event teams are consolidating around fewer, more strategic vendors",
        "Procurement pressure is pushing organizers toward partners who can deliver consistently across more than one event cycle, which makes reliability and fit matter more than a one-off quote.",
    ),
    "media": (
        "Why event coverage works best when access is built around a clear audience angle",
        "Editorial teams are prioritizing event stories that combine access with a sharper audience takeaway, instead of generic event recap coverage that reads like promotion.",
    ),
}


@dataclass(slots=True)
class EmailTouch:
    touch: int
    day: int
    purpose: str
    subject: str
    body: str
    cta: str
    specificity_markers: list[str] = field(default_factory=list)
    draft: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QualityCheckResult:
    passed: bool
    issues: list[str]
    repeated_phrases: list[str]
    banned_phrase_hits: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProspectSequence:
    name: str
    company: str
    role: str
    email: str
    role_type: str
    personalization_hook: str
    angle_summary: str
    value_proposition: str
    touches: list[EmailTouch]
    quality_check: QualityCheckResult

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["touches"] = [touch.as_dict() for touch in self.touches]
        payload["quality_check"] = self.quality_check.as_dict()
        return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build four-touch cold-outreach sequences from prospect profiles."
    )
    parser.add_argument(
        "--profiles",
        required=True,
        help="Path to prospect profiles JSON from prospect_research.py.",
    )
    parser.add_argument(
        "--event",
        required=True,
        help="Event name.",
    )
    parser.add_argument(
        "--date",
        required=True,
        type=parse_event_date,
        help="Event date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--cadence",
        default="1,3,7,14",
        help='Comma-separated follow-up days. Default: "1,3,7,14".',
    )
    parser.add_argument(
        "--create-drafts",
        action="store_true",
        help="Create Gmail drafts for each touch via Composio.",
    )
    parser.add_argument(
        "--output",
        help="Write output to a file instead of stdout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview sequences without creating drafts.",
    )
    return parser.parse_args(argv)


def parse_event_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must be in YYYY-MM-DD format") from exc


def parse_cadence(value: str) -> tuple[int, int, int, int]:
    try:
        cadence = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise SystemExit("--cadence must contain comma-separated integers") from exc

    if len(cadence) != 4:
        raise SystemExit("--cadence must contain exactly four day offsets")
    if list(cadence) != sorted(cadence):
        raise SystemExit("--cadence must be in ascending order")
    return cadence


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_profiles(path_value: str) -> list[dict[str, Any]]:
    path = Path(path_value).expanduser()
    if not path.exists():
        raise SystemExit(f"Profiles file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        profiles = payload.get("profiles")
        if isinstance(profiles, list):
            return [item for item in profiles if isinstance(item, dict)]
    raise SystemExit("Profiles file must contain a profiles list or a top-level list")


def event_note(event_context: EventContext, role_type: str) -> str:
    days = event_context.days_until_event
    if role_type == "buyer":
        if days <= 14:
            return f"{event_context.event_name} is now close enough that attendee calendars and meeting plans are likely getting locked."
        return f"This is the window when teams decide whether an event will produce enough useful meetings to justify the time."
    if role_type == "sponsor":
        if days <= 30:
            return f"We are in the planning window where activation ideas become either sharper or more generic depending on how early they are scoped."
        return f"This is still early enough to shape a sponsorship around outcomes instead of a standard package."
    if role_type == "speaker":
        if days <= 30:
            return f"Programming, travel planning, and speaker logistics are moving from flexible to fixed as {event_context.event_name} gets closer."
        return f"This is the moment when programming conversations are still open enough to build around speaker fit."
    if role_type == "vendor":
        if days <= 30:
            return f"The closer an event gets, the more organizers prioritize vendor fit and reliability over wide-open discovery."
        return f"There is still time to position the relationship as longer-term pipeline, not only a one-event transaction."
    if days <= 30:
        return f"Editorial access gets more valuable as key conversations and interviews start to take shape around the event."
    return f"This is a good point to frame the event as a strong audience story rather than a recap opportunity."


def intro_subject(profile: dict[str, Any], event_name: str) -> str:
    company = first_text(profile.get("company"), profile.get("name"), "Your team")
    role_type = str(profile.get("role_type") or "buyer")
    if role_type == "sponsor":
        return f"{company} activation idea for {event_name}"
    if role_type == "speaker":
        return f"{event_name} audience fit for {company}"
    if role_type == "vendor":
        return f"{company} + {event_name} partnership fit"
    if role_type == "media":
        return f"{company} editorial angle around {event_name}"
    return f"{company} and the right room at {event_name}"


def first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return normalize_space(value)
    return ""


def sequence_for_profile(
    profile: dict[str, Any],
    event_context: EventContext,
    cadence: tuple[int, int, int, int],
) -> ProspectSequence:
    role_type = first_text(profile.get("role_type"), "buyer") or "buyer"
    company = first_text(profile.get("company"), "your team")
    name = first_text(profile.get("name"), company)
    role = first_text(profile.get("role"), "team")
    event_name = event_context.event_name
    hook = first_text(profile.get("personalization_hook"))
    value_proposition = first_text(profile.get("value_proposition"))
    angle_summary = first_text((profile.get("recommended_angle") or {}).get("summary"))
    cta_hint = first_text(profile.get("recommended_cta"))
    event_window_note = event_note(event_context, role_type)
    intro = build_intro_touch(
        profile=profile,
        name=name,
        company=company,
        role=role,
        role_type=role_type,
        event_name=event_name,
        day=cadence[0],
        hook=hook,
        value_proposition=value_proposition,
        cta_hint=cta_hint,
    )
    follow_up = build_follow_up_touch(
        company=company,
        role=role,
        role_type=role_type,
        event_name=event_name,
        day=cadence[1],
        intro_subject_line=intro.subject,
        event_window_note=event_window_note,
        angle_summary=angle_summary,
    )
    value_add = build_value_add_touch(
        company=company,
        role=role,
        role_type=role_type,
        event_name=event_name,
        day=cadence[2],
    )
    break_up = build_break_up_touch(
        company=company,
        role=role,
        role_type=role_type,
        event_name=event_name,
        day=cadence[3],
        intro_subject_line=intro.subject,
    )

    touches = [intro, follow_up, value_add, break_up]
    quality_check = run_quality_checks(profile, event_name, touches)
    return ProspectSequence(
        name=name,
        company=company,
        role=role,
        email=first_text(profile.get("email")),
        role_type=role_type,
        personalization_hook=hook,
        angle_summary=angle_summary,
        value_proposition=value_proposition,
        touches=touches,
        quality_check=quality_check,
    )


def build_intro_touch(
    profile: dict[str, Any],
    name: str,
    company: str,
    role: str,
    role_type: str,
    event_name: str,
    day: int,
    hook: str,
    value_proposition: str,
    cta_hint: str,
) -> EmailTouch:
    angle = profile.get("recommended_angle") or {}
    primary = first_text(angle.get("primary"), role_type)
    activation_line = role_specific_activation(role_type, company, event_name)
    intro_line = (
        f"{company} stood out to me because the strongest way to make {event_name} relevant for a {role} is to lead with {primary.replace('_', ' ')}."
    )
    body = "\n\n".join(
        [
            intro_line,
            f"{hook} {value_proposition} One specific idea: {activation_line}",
            single_cta_text(role_type, company, cta_hint),
            signature(event_name),
        ]
    )
    return EmailTouch(
        touch=1,
        day=day,
        purpose=PURPOSES[0],
        subject=intro_subject(profile, event_name),
        body=body,
        cta=single_cta_text(role_type, company, cta_hint),
        specificity_markers=[company, role, primary, event_name],
    )


def role_specific_activation(role_type: str, company: str, event_name: str) -> str:
    if role_type == "buyer":
        return f"a short list of the buyer meetings and sessions at {event_name} that would help {company} leave with clearer next steps"
    if role_type == "sponsor":
        return f"a sponsor activation that puts {company} inside the highest-value attendee conversations instead of on a passive logo line"
    if role_type == "speaker":
        return f"a format where {company}'s perspective lands as a practical session instead of a generic keynote pitch"
    if role_type == "vendor":
        return f"a partnership path where {company} can prove fit for this event and future ones rather than compete only on a one-off scope"
    return f"an editorial access plan that gives {company} a sharper story and better interview opportunities around {event_name}"


def single_cta_text(role_type: str, company: str, cta_hint: str) -> str:
    if cta_hint and not cta_hint.lower().startswith(("offer ", "invite ", "ask ")):
        return cta_hint.rstrip(".") + "?"
    if role_type == "buyer":
        return f"Would it be helpful if I sent the two conversations I think would be highest value for {company}?"
    if role_type == "sponsor":
        return f"Open to a quick look at the activation concept I think fits {company} best?"
    if role_type == "speaker":
        return "Would a short note on format, audience, and logistics be useful to review?"
    if role_type == "vendor":
        return f"Would it be useful to outline where {company} could fit across this event cycle?"
    return "Would it help if I sent the coverage angles and access points that look most differentiated?"


def build_follow_up_touch(
    company: str,
    role: str,
    role_type: str,
    event_name: str,
    day: int,
    intro_subject_line: str,
    event_window_note: str,
    angle_summary: str,
) -> EmailTouch:
    new_info = follow_up_information(role_type, company, event_name)
    cta = follow_up_cta(role_type, company)
    body = "\n\n".join(
        [
            f"One planning note from our side: {event_window_note}",
            f"That matters for {company} because {new_info} {angle_summary}".strip(),
            cta,
            signature(event_name),
        ]
    )
    return EmailTouch(
        touch=2,
        day=day,
        purpose=PURPOSES[1],
        subject=f"Re: {intro_subject_line}",
        body=body,
        cta=cta,
        specificity_markers=[company, role, role_type, event_window_note],
    )


def follow_up_information(role_type: str, company: str, event_name: str) -> str:
    if role_type == "buyer":
        return f"this is usually when travel approvals and meeting calendars start to harden, so buyer value is easier to justify when the event can already point to the right rooms and agenda moments for {company}."
    if role_type == "sponsor":
        return f"the best sponsor outcomes at {event_name} usually come from activation concepts that are scoped before inventory becomes generic and harder to tailor for {company}."
    if role_type == "speaker":
        return f"speaker conversations are strongest before the agenda is locked, because that is when format, audience fit, and travel or compensation details can still be shaped around {company}."
    if role_type == "vendor":
        return f"partner decisions tighten as timelines get shorter, which makes it more valuable to show where {company} fits operationally and across future event work."
    return f"media access becomes more useful when interview windows and editorial plans are still flexible enough to shape around {company}."


def follow_up_cta(role_type: str, company: str) -> str:
    if role_type == "buyer":
        return f"Happy to map out the shortlist of meetings and sessions I would prioritize for {company} in one note."
    if role_type == "sponsor":
        return f"Happy to outline the one activation concept I think would create the most value for {company}."
    if role_type == "speaker":
        return "Happy to sketch the format and audience outline in one short note."
    if role_type == "vendor":
        return f"Happy to outline where {company} appears strongest for this event cycle."
    return "Happy to outline the editorial angles and access plan in one short note."


def build_value_add_touch(
    company: str,
    role: str,
    role_type: str,
    event_name: str,
    day: int,
) -> EmailTouch:
    insight_title, insight_summary = INSIGHT_LIBRARY.get(role_type, INSIGHT_LIBRARY["buyer"])
    cta = value_add_cta(role_type, company)
    body = "\n\n".join(
        [
            f"One pattern worth noting for a {role}: {insight_summary}",
            f"That is part of why we are shaping {event_name} the way we are, and it is also why {company} feels like a strong fit for the conversation.",
            cta,
            signature(event_name),
        ]
    )
    return EmailTouch(
        touch=3,
        day=day,
        purpose=PURPOSES[2],
        subject=insight_title,
        body=body,
        cta=cta,
        specificity_markers=[company, role, insight_title, event_name],
    )


def value_add_cta(role_type: str, company: str) -> str:
    if role_type == "buyer":
        return f"Reply with 'framework' and I will send the one-page attendance ROI framework we use with teams like {company}."
    if role_type == "sponsor":
        return f"Reply with 'activation' and I will send the simple activation ROI lens we use before a sponsor commits budget at {company}."
    if role_type == "speaker":
        return "Reply with 'prompts' and I will send the audience prompts we use to shape practical speaker sessions."
    if role_type == "vendor":
        return f"Reply with 'scorecard' and I will send the scorecard we use when deciding whether a vendor relationship should expand beyond one event."
    return "Reply with 'access' and I will send the editorial access checklist we use when planning media conversations around the event."


def build_break_up_touch(
    company: str,
    role: str,
    role_type: str,
    event_name: str,
    day: int,
    intro_subject_line: str,
) -> EmailTouch:
    cta = break_up_cta(role_type)
    body = "\n\n".join(
        [
            f"I will close the loop here. {event_name} may simply not be the right fit for {company} right now, and no pressure at all if the timing is off.",
            f"I reached out because the match between {role} priorities and the event felt real, but I know inbox silence usually means focus is elsewhere.",
            cta,
            signature(event_name),
        ]
    )
    return EmailTouch(
        touch=4,
        day=day,
        purpose=PURPOSES[3],
        subject=f"Re: {intro_subject_line}",
        body=body,
        cta=cta,
        specificity_markers=[company, role, role_type, "break_up"],
    )


def break_up_cta(role_type: str) -> str:
    if role_type == "speaker":
        return "If the timing changes later, feel free to reply with 'later' and I can revisit it then."
    return "If the timing changes later, feel free to reply with 'later' and I can pick this up again when it is more useful."


def signature(event_name: str) -> str:
    return f"Best,\n{event_name} team"


def run_quality_checks(profile: dict[str, Any], event_name: str, touches: list[EmailTouch]) -> QualityCheckResult:
    issues: list[str] = []
    banned_hits: list[str] = []
    repeated_phrases = repeated_phrase_hits(profile, event_name, touches)

    for touch in touches:
        lowered = touch.body.lower()
        for phrase in BANNED_PHRASES:
            if phrase in lowered:
                banned_hits.append(f"touch_{touch.touch}:{phrase}")
        if specificity_score(profile, event_name, touch.body) < 2:
            issues.append(f"Touch {touch.touch} lacks specificity.")

    if repeated_phrases:
        issues.append("Repeated phrases detected across touches.")
    if banned_hits:
        issues.append("Banned opener or follow-up language detected.")
    if not touches[1].subject.startswith("Re: "):
        issues.append("Touch 2 should continue the original thread.")
    if touches[2].subject.startswith("Re: "):
        issues.append("Touch 3 should use a value-add subject line, not a thread reply subject.")
    if "close the loop" not in touches[3].body.lower() and "not the right fit" not in touches[3].body.lower():
        issues.append("Touch 4 does not read like a break-up email.")
    if not any(token in touches[1].body.lower() for token in ("planning note", "window", "timing", "agenda", "activation", "travel")):
        issues.append("Touch 2 does not introduce clearly new information.")
    if not any(token in touches[2].body.lower() for token in ("pattern", "framework", "checklist", "scorecard", "sessions")):
        issues.append("Touch 3 does not read like a value-add email.")

    return QualityCheckResult(
        passed=not issues,
        issues=issues,
        repeated_phrases=repeated_phrases,
        banned_phrase_hits=banned_hits,
    )


def specificity_score(profile: dict[str, Any], event_name: str, body: str) -> int:
    tokens = {
        first_text(profile.get("company")).lower(),
        first_text(profile.get("role")).lower(),
        first_text(profile.get("role_type")).lower(),
        event_name.lower(),
    }
    lowered = body.lower()
    score = 0
    for token in tokens:
        if token and token in lowered:
            score += 1
    if re.search(r"\b\d+\b", body):
        score += 1
    if any(word in lowered for word in ("audience", "activation", "meetings", "format", "access", "pipeline")):
        score += 1
    return score


def repeated_phrase_hits(profile: dict[str, Any], event_name: str, touches: list[EmailTouch]) -> list[str]:
    ignored_tokens = {
        first_text(profile.get("company")).lower(),
        first_text(profile.get("name")).lower(),
        first_text(profile.get("role")).lower(),
        first_text(profile.get("role_type")).lower(),
        event_name.lower(),
    }
    phrase_index: dict[str, set[int]] = {}
    for touch in touches:
        words = [word for word in re.findall(r"[a-z0-9']+", touch.body.lower()) if word not in STOPWORDS]
        for start in range(max(0, len(words) - 2)):
            phrase_words = words[start : start + 3]
            if len(phrase_words) < 3:
                continue
            phrase = " ".join(phrase_words)
            if len(phrase) < 18:
                continue
            if any(token and token in phrase for token in ignored_tokens):
                continue
            phrase_index.setdefault(phrase, set()).add(touch.touch)
    hits = [phrase for phrase, touch_ids in phrase_index.items() if len(touch_ids) > 1]
    return sorted(hits)[:5]


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


def create_drafts(client: EventComposioClient, sequence: ProspectSequence) -> None:
    if not sequence.email:
        sequence.quality_check.issues.append("Draft creation skipped because the prospect email is missing.")
        sequence.quality_check.passed = False
        return

    for touch in sequence.touches:
        result = unwrap_payload(
            client.create_draft(
                to=sequence.email,
                subject=touch.subject,
                body=touch.body,
                is_html=False,
            )
        )
        touch.draft = {
            "id": extract_draft_id(result),
            "raw": result,
        }


def extract_draft_id(result: Any) -> str:
    if isinstance(result, dict):
        for key in ("draft_id", "draftId", "id"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for nested in result.values():
            draft_id = extract_draft_id(nested)
            if draft_id:
                return draft_id
    return ""


def payload_output(
    sequences: list[ProspectSequence],
    event_context: EventContext,
    cadence: tuple[int, int, int, int],
    drafts_requested: bool,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "event": {
            "name": event_context.event_name,
            "date": event_context.event_date.date().isoformat(),
            "phase": event_context.phase_label,
            "days_until_event": event_context.days_until_event,
        },
        "cadence_days": list(cadence),
        "drafts_requested": drafts_requested,
        "dry_run": dry_run,
        "sequences": [sequence.as_dict() for sequence in sequences],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    event = payload["event"]
    lines = [
        f"# Outreach Sequences — {event['name']}",
        "",
        f"- Event date: {event['date']}",
        f"- Event phase: {event['phase']}",
        f"- Cadence: {', '.join(str(day) for day in payload['cadence_days'])}",
        f"- Drafts requested: {payload['drafts_requested']}",
        f"- Dry run: {payload['dry_run']}",
        "",
    ]

    for sequence in payload.get("sequences", []):
        if not isinstance(sequence, dict):
            continue
        quality = sequence.get("quality_check", {})
        lines.extend(
            [
                f"## {sequence.get('name', 'Unknown')} — {sequence.get('company', 'Unknown Company')} ({sequence.get('role_type', 'unknown')})",
                "",
                f"- Role: {sequence.get('role', '')}",
                f"- Email: {sequence.get('email') or 'missing'}",
                f"- Angle: {sequence.get('angle_summary', '')}",
                f"- Quality passed: {quality.get('passed', False)}",
            ]
        )
        issues = quality.get("issues", [])
        if isinstance(issues, list) and issues:
            lines.append("- Quality issues:")
            for issue in issues:
                lines.append(f"  - {issue}")
        lines.append("")

        touches = sequence.get("touches", [])
        for touch in touches:
            if not isinstance(touch, dict):
                continue
            lines.extend(
                [
                    f"### Touch {touch.get('touch')} — Day {touch.get('day')} ({touch.get('purpose')})",
                    f"Subject: {touch.get('subject', '')}",
                    "",
                    str(touch.get("body", "")),
                    "",
                ]
            )
            draft = touch.get("draft")
            if isinstance(draft, dict) and draft.get("id"):
                lines.append(f"Draft ID: {draft['id']}")
                lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_output(text: str, path_value: str | None) -> None:
    if not path_value:
        print(text)
        return
    path = Path(path_value).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def emit_json(output_path: str | None) -> bool:
    return bool(output_path and Path(output_path).suffix.lower() == ".json")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cadence = parse_cadence(args.cadence)
    profiles = load_profiles(args.profiles)
    event_context = EventContext(event_name=args.event, event_date=args.date)
    sequences = [sequence_for_profile(profile, event_context, cadence) for profile in profiles]

    if args.create_drafts and not args.dry_run:
        client = EventComposioClient()
        for sequence in sequences:
            if not sequence.quality_check.passed:
                continue
            create_drafts(client, sequence)

    payload = payload_output(
        sequences=sequences,
        event_context=event_context,
        cadence=cadence,
        drafts_requested=args.create_drafts,
        dry_run=args.dry_run,
    )
    if emit_json(args.output):
        text = json.dumps(payload, indent=2)
    else:
        text = render_markdown(payload)
    write_output(text, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

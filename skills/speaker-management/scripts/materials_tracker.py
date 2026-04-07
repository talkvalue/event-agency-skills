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


BIO_DEADLINE = 30
ABSTRACT_DEADLINE = 21
SLIDES_DEADLINE = 14
TRAVEL_DEADLINE = 7
UPCOMING_WINDOW_DAYS = 7
BANNED_FLUFF_WORDS = (
    "thought leader",
    "visionary",
    "guru",
    "passionate about",
    "world-class",
    "cutting-edge",
    "revolutionary",
    "groundbreaking",
    "leverage",
    "synergize",
    "transformative",
    "innovative",
    "disruptor",
)
WEAK_OUTCOME_VERBS = (
    "explore",
    "discuss",
    "learn about",
    "understand",
    "discover",
    "dive into",
    "unpack",
)
OUTPUT_JSON_SUFFIXES = {".json", ".jsonl"}
NAME_KEYS = ("speaker", "speaker_name", "name", "full_name")
COMPANY_KEYS = ("company", "organization", "employer")
TITLE_KEYS = ("title", "job_title", "role")
BIO25_KEYS = ("bio_25", "bio25", "short_bio", "emcee_bio", "intro_25")
BIO50_KEYS = ("bio_50", "bio50", "program_bio", "bio_medium", "intro_50")
BIO100_KEYS = ("bio_100", "bio100", "website_bio", "long_bio", "full_bio", "intro_100")
HEADSHOT_KEYS = ("headshot", "headshot_url", "headshot_link", "photo", "photo_url", "headshot_received")
ABSTRACT_KEYS = ("abstract", "session_abstract", "description", "session_description")
SLIDES_KEYS = ("slides", "slide_deck", "deck", "deck_url", "slides_link")
AV_KEYS = ("av_rider", "av_requirements", "tech_requirements", "technical_requirements")
TRAVEL_KEYS = ("travel_info", "travel", "travel_details", "flights", "hotel")
OUTCOMES_KEYS = ("learning_outcomes", "outcomes")


@dataclass(slots=True)
class MaterialStatus:
    label: str
    state: str
    deadline_day: int
    received: bool
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SpeakerStatus:
    speaker: str
    company: str
    title: str
    bio: MaterialStatus
    headshot: MaterialStatus
    abstract: MaterialStatus
    slides: MaterialStatus
    av_rider: MaterialStatus
    travel_info: MaterialStatus
    quality_notes: list[str]
    action_item: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["bio"] = self.bio.as_dict()
        payload["headshot"] = self.headshot.as_dict()
        payload["abstract"] = self.abstract.as_dict()
        payload["slides"] = self.slides.as_dict()
        payload["av_rider"] = self.av_rider.as_dict()
        payload["travel_info"] = self.travel_info.as_dict()
        return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a speaker materials dashboard from Google Sheets or JSON input."
    )
    parser.add_argument("--event", required=True, help="Event name.")
    parser.add_argument(
        "--date",
        required=True,
        type=parse_event_date,
        help="Event date in YYYY-MM-DD format.",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--spreadsheet", help="Google Sheets spreadsheet ID with speaker tracker data.")
    source_group.add_argument("--speakers", help="Path to a JSON file with speaker tracker data.")
    parser.add_argument("--output", help="Output file path or directory. Defaults to stdout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the tracker run without calling Composio. Works without COMPOSIO_API_KEY.",
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
        return path / f"{generated_at.date().isoformat()}-{slugify(event_name)}-speaker-materials{suffix}"
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


def extract_json_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item, __source=f"speakers[{index}]") for index, item in enumerate(payload, start=1) if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("speakers", "items", "records", "data"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return [dict(item, __source=f"{key}[{index}]") for index, item in enumerate(candidate, start=1) if isinstance(item, dict)]
        return [dict(payload, __source="speaker")]
    raise SystemExit("Speaker JSON must contain a list or an object with a speakers/items/records/data list")


def load_speaker_file(path_value: str) -> list[dict[str, Any]]:
    path = Path(path_value).expanduser()
    if not path.exists():
        raise SystemExit(f"Speaker file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return extract_json_records(payload)


def fetch_spreadsheet_records(spreadsheet_id: str) -> list[dict[str, Any]]:
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


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = normalize_space(value).lower()
    if not text:
        return None
    if text in {"true", "yes", "y", "1", "received", "complete", "completed", "submitted", "done"}:
        return True
    if text in {"false", "no", "n", "0", "missing", "pending", "not received", "overdue"}:
        return False
    return None


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def has_material(record: dict[str, Any], keys: tuple[str, ...]) -> tuple[bool, str]:
    text = first_text(record, keys)
    bool_value = parse_bool(text)
    if bool_value is not None:
        return bool_value, text
    return bool(text), text


def relative_due_label(deadline_day: int, days_until_event: int) -> str:
    if days_until_event > deadline_day:
        return f"due D-{deadline_day}"
    if days_until_event == deadline_day:
        return f"due today (D-{deadline_day})"
    return f"overdue since D-{deadline_day}"


def status_for_material(
    label: str,
    deadline_day: int,
    days_until_event: int,
    received: bool,
    notes: list[str] | None = None,
    needs_revision: bool = False,
) -> MaterialStatus:
    note_list = [normalize_space(note) for note in (notes or []) if normalize_space(note)]
    if received and not needs_revision:
        state = "OK"
    elif received:
        state = "REVISION"
    elif days_until_event <= deadline_day:
        state = f"MISSING ({relative_due_label(deadline_day, days_until_event)})"
    elif deadline_day - days_until_event <= UPCOMING_WINDOW_DAYS:
        state = f"UPCOMING (D-{deadline_day})"
    else:
        state = "NOT YET DUE"

    return MaterialStatus(
        label=label,
        state=state,
        deadline_day=deadline_day,
        received=received,
        notes=note_list,
    )


def bio_quality_notes(record: dict[str, Any]) -> tuple[list[str], bool]:
    notes: list[str] = []
    needs_revision = False
    bios = {
        "25": first_text(record, BIO25_KEYS),
        "50": first_text(record, BIO50_KEYS),
        "100": first_text(record, BIO100_KEYS),
    }
    ranges = {
        "25": (15, 35),
        "50": (35, 65),
        "100": (75, 130),
    }

    missing = [label for label, text in bios.items() if not text]
    if missing:
        notes.append(f"missing bio variant(s): {', '.join(missing)}")
        needs_revision = True

    combined = " ".join(text for text in bios.values() if text)
    lowered = combined.lower()
    banned_hits = [phrase for phrase in BANNED_FLUFF_WORDS if phrase in lowered]
    if banned_hits:
        notes.append(f"banned fluff: {', '.join(sorted(set(banned_hits)))}")
        needs_revision = True

    if re.search(r"\b(i|my|me|i'm|i’ve|i'll)\b", combined, flags=re.IGNORECASE):
        notes.append("bio uses first person; switch to third person")
        needs_revision = True

    for label, text in bios.items():
        if not text:
            continue
        minimum, maximum = ranges[label]
        count = word_count(text)
        if count < minimum or count > maximum:
            notes.append(f"bio {label} word count is {count}; target is approximately {label} words")
            needs_revision = True

    return notes, needs_revision


def outcome_quality_notes(record: dict[str, Any]) -> list[str]:
    outcomes = first_text(record, OUTCOMES_KEYS)
    if not outcomes:
        return []
    lowered = outcomes.lower()
    hits = [verb for verb in WEAK_OUTCOME_VERBS if verb in lowered]
    if not hits:
        return []
    return [f"learning outcomes use weak verbs: {', '.join(sorted(set(hits)))}"]


def build_bio_status(record: dict[str, Any], days_until_event: int) -> tuple[MaterialStatus, list[str]]:
    notes, needs_revision = bio_quality_notes(record)
    received = any(first_text(record, keys) for keys in (BIO25_KEYS, BIO50_KEYS, BIO100_KEYS))
    status = status_for_material("Bio", BIO_DEADLINE, days_until_event, received, notes, needs_revision)
    return status, notes


def build_speaker_status(record: dict[str, Any], event_context: EventContext) -> SpeakerStatus:
    speaker = first_text(record, NAME_KEYS) or "Unknown speaker"
    company = first_text(record, COMPANY_KEYS) or "—"
    title = first_text(record, TITLE_KEYS) or "—"
    days_until_event = event_context.days_until_event

    bio_status, quality_notes = build_bio_status(record, days_until_event)
    quality_notes.extend(outcome_quality_notes(record))

    headshot_received, headshot_text = has_material(record, HEADSHOT_KEYS)
    headshot_notes = []
    if headshot_text and not headshot_received and "300" in headshot_text:
        headshot_received = True
    headshot_status = status_for_material("Headshot", BIO_DEADLINE, days_until_event, headshot_received, headshot_notes)

    abstract_received, abstract_text = has_material(record, ABSTRACT_KEYS)
    abstract_notes = []
    if abstract_text and word_count(abstract_text) < 40:
        abstract_notes.append("abstract looks short; target is a clear attendee-focused session summary")
    abstract_status = status_for_material(
        "Abstract",
        ABSTRACT_DEADLINE,
        days_until_event,
        abstract_received,
        abstract_notes,
        bool(abstract_notes) and abstract_received,
    )

    slides_received, _ = has_material(record, SLIDES_KEYS)
    slides_status = status_for_material("Slides", SLIDES_DEADLINE, days_until_event, slides_received)

    av_received, _ = has_material(record, AV_KEYS)
    av_status = status_for_material("AV rider", ABSTRACT_DEADLINE, days_until_event, av_received)

    travel_received, _ = has_material(record, TRAVEL_KEYS)
    travel_status = status_for_material("Travel", TRAVEL_DEADLINE, days_until_event, travel_received)

    action_item = next_action_item(
        speaker=speaker,
        statuses=[bio_status, headshot_status, abstract_status, slides_status, av_status, travel_status],
    )

    return SpeakerStatus(
        speaker=speaker,
        company=company,
        title=title,
        bio=bio_status,
        headshot=headshot_status,
        abstract=abstract_status,
        slides=slides_status,
        av_rider=av_status,
        travel_info=travel_status,
        quality_notes=quality_notes[:5],
        action_item=action_item,
    )


def sort_priority(status: MaterialStatus) -> tuple[int, int]:
    if status.state.startswith("MISSING"):
        return (0, status.deadline_day)
    if status.state == "REVISION":
        return (1, status.deadline_day)
    if status.state.startswith("UPCOMING"):
        return (2, status.deadline_day)
    return (3, status.deadline_day)


def speaker_sort_key(status: SpeakerStatus) -> tuple[tuple[int, int], str]:
    priorities = [
        sort_priority(status.bio),
        sort_priority(status.headshot),
        sort_priority(status.abstract),
        sort_priority(status.slides),
        sort_priority(status.av_rider),
        sort_priority(status.travel_info),
    ]
    return min(priorities), status.speaker.lower()


def next_action_item(speaker: str, statuses: list[MaterialStatus]) -> str:
    ordered = sorted(statuses, key=sort_priority)
    top = ordered[0]
    if top.state == "OK":
        return f"{speaker}: no immediate speaker follow-up needed."
    if top.state.startswith("MISSING"):
        return f"{speaker}: request {top.label.lower()} now ({relative_due_label(top.deadline_day, -1 if 'overdue' in top.state else top.deadline_day)})."
    if top.state == "REVISION":
        detail = top.notes[0] if top.notes else "needs revision"
        return f"{speaker}: ask for a {top.label.lower()} revision — {detail}."
    return f"{speaker}: remind them that {top.label.lower()} is due soon (D-{top.deadline_day})."


def summary_counts(statuses: list[SpeakerStatus]) -> dict[str, int]:
    counts = {"speakers": len(statuses), "critical": 0, "revision": 0, "upcoming": 0, "clear": 0}
    for status in statuses:
        state_values = [
            status.bio.state,
            status.headshot.state,
            status.abstract.state,
            status.slides.state,
            status.av_rider.state,
            status.travel_info.state,
        ]
        if any(value.startswith("MISSING") for value in state_values):
            counts["critical"] += 1
        elif any(value == "REVISION" for value in state_values):
            counts["revision"] += 1
        elif any(value.startswith("UPCOMING") for value in state_values):
            counts["upcoming"] += 1
        else:
            counts["clear"] += 1
    return counts


def build_payload(event_name: str, generated_at: datetime, event_context: EventContext, source: dict[str, Any], statuses: list[SpeakerStatus]) -> dict[str, Any]:
    counts = summary_counts(statuses)
    return {
        "event": event_name,
        "event_date": event_context.event_date.date().isoformat(),
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "phase": event_context.phase.value,
        "phase_label": event_context.phase_label,
        "days_until_event": event_context.days_until_event,
        "source": source,
        "counts": counts,
        "speakers": [status.as_dict() for status in statuses],
        "action_items": [status.action_item for status in statuses if status.action_item][:5],
    }


def render_dry_run_markdown(event_name: str, generated_at: datetime, event_context: EventContext, source: dict[str, Any], as_json: bool) -> str:
    lines = [
        f"# Speaker Materials Tracker — {event_name}",
        f"Updated: {generated_at.isoformat(timespec='seconds')}",
        f"Event Date: {event_context.event_date.date().isoformat()} ({event_context.phase_label})",
        "",
        "## Dry Run",
        f"- Source: `{source['type']}`",
        f"- Output format: `{'json' if as_json else 'markdown'}`",
        "- Deadline checks that would run: D-30 bio/headshot, D-21 abstract/AV, D-14 slides, D-7 travel",
    ]
    if source["type"] == "spreadsheet":
        lines.append(f"- Spreadsheet: `{source['spreadsheet_id']}`")
        lines.append("- Composio read skipped")
    else:
        lines.append(f"- Speaker file: `{source['speakers_file']}`")
        lines.append("- Local parsing skipped")
    return "\n".join(lines)


def escape_cell(value: str) -> str:
    return normalize_space(value).replace("|", "\\|") or "—"


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Speaker Status — {payload['event']} ({payload['event_date']})",
        f"Updated: {payload['generated_at']}",
        f"Phase: {payload['phase_label']}",
        "",
        f"Speakers: {payload['counts']['speakers']}  |  Critical: {payload['counts']['critical']}  |  Revision: {payload['counts']['revision']}  |  Upcoming: {payload['counts']['upcoming']}  |  Clear: {payload['counts']['clear']}",
        "",
        "| Speaker | Company | Bio | Headshot | Abstract | Slides | AV Rider | Travel | Notes |",
        "|---------|---------|-----|----------|----------|--------|----------|--------|-------|",
    ]

    for speaker in payload["speakers"]:
        notes = speaker.get("quality_notes") or []
        notes_text = "; ".join(notes[:2]) if notes else "—"
        lines.append(
            "| {speaker} | {company} | {bio} | {headshot} | {abstract} | {slides} | {av} | {travel} | {notes} |".format(
                speaker=escape_cell(speaker["speaker"]),
                company=escape_cell(speaker["company"]),
                bio=escape_cell(speaker["bio"]["state"]),
                headshot=escape_cell(speaker["headshot"]["state"]),
                abstract=escape_cell(speaker["abstract"]["state"]),
                slides=escape_cell(speaker["slides"]["state"]),
                av=escape_cell(speaker["av_rider"]["state"]),
                travel=escape_cell(speaker["travel_info"]["state"]),
                notes=escape_cell(notes_text),
            )
        )

    lines.extend(["", "## Action Items"])
    if payload["action_items"]:
        for index, action in enumerate(payload["action_items"], start=1):
            lines.append(f"{index}. {action}")
    else:
        lines.append("1. No immediate speaker-materials actions needed.")

    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    generated_at = datetime.now(tz=UTC)
    event_context = EventContext(event_name=args.event, event_date=args.date, now=generated_at)
    output_as_json = should_emit_json(args)

    if args.spreadsheet:
        source = {"type": "spreadsheet", "spreadsheet_id": args.spreadsheet}
    else:
        source = {"type": "speakers_file", "speakers_file": str(Path(args.speakers).expanduser())}

    if args.dry_run:
        if output_as_json:
            content = json.dumps(
                {
                    "dry_run": True,
                    "event": args.event,
                    "event_date": args.date.date().isoformat(),
                    "generated_at": generated_at.isoformat(timespec="seconds"),
                    "source": source,
                    "phase": event_context.phase.value,
                    "phase_label": event_context.phase_label,
                },
                indent=2,
            )
        else:
            content = render_dry_run_markdown(args.event, generated_at, event_context, source, output_as_json)
        write_output(content, resolve_output_path(args.output, args.event, generated_at, output_as_json))
        return 0

    try:
        records = fetch_spreadsheet_records(args.spreadsheet) if args.spreadsheet else load_speaker_file(args.speakers)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        print(f"Failed to load speaker data: {exc}", file=sys.stderr)
        return 1

    statuses = [build_speaker_status(record, event_context) for record in records]
    statuses.sort(key=speaker_sort_key)
    payload = build_payload(args.event, generated_at, event_context, source, statuses)

    content = json.dumps(payload, indent=2) if output_as_json else render_markdown(payload)
    write_output(content, resolve_output_path(args.output, args.event, generated_at, output_as_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

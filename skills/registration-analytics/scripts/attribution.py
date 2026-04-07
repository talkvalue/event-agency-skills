# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedCallResult=false, reportUnusedParameter=false, reportUnusedVariable=false, reportUnknownLambdaType=false, reportImplicitStringConcatenation=false
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.composio_client import EventComposioClient


OUTPUT_JSON_SUFFIXES = {".json", ".jsonl"}
TOUCHPOINT_KEYS = ("touchpoints", "journey", "path", "attribution_path", "source_path")
SOURCE_KEYS = ("source", "utm_source", "registration_source", "channel", "referrer")
MEDIUM_KEYS = ("utm_medium", "medium")
ATTENDANCE_KEYS = ("attended", "attendance", "checked_in", "check_in", "showed_up", "status")
ID_KEYS = ("email", "registration_id", "registrant_id", "attendee_id", "id", "name")
INDUSTRY_KEYS = ("industry", "vertical")
ROLE_KEYS = ("role", "job_title", "title", "seniority")
GEOGRAPHY_KEYS = ("geography", "region", "country", "location", "state")


@dataclass(slots=True)
class Registrant:
    identifier: str
    touchpoints: list[str]
    attended: bool | None
    industry: str
    role: str
    geography: str
    source_present: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SegmentRow:
    dimension: str
    segment: str
    registrations: int
    attendees: int | None
    attendance_rate: float | None
    vs_average: float | None
    small_sample: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze event registration attribution with first-touch, last-touch, and multi-touch models."
    )
    parser.add_argument("--event", required=True, help="Event name.")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--spreadsheet", help="Google Sheets spreadsheet ID with registration data.")
    source_group.add_argument("--registrations", help="Path to a CSV or JSON registration export.")
    parser.add_argument(
        "--model",
        default="multi",
        choices=("last", "first", "multi"),
        help="Primary attribution model used for the summary callout. All three models are still reported.",
    )
    parser.add_argument("--output", help="Output file path or directory. Defaults to stdout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the analysis without calling Composio. Works without COMPOSIO_API_KEY.",
    )
    return parser.parse_args(argv)


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def canonicalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "event"


def resolve_output_path(output: str | None, event_name: str, as_json: bool) -> Path | None:
    if not output:
        return None
    path = Path(output).expanduser()
    suffix = ".json" if as_json else ".md"
    directory_like = output.endswith(("/", "\\")) or (path.suffix == "" and not path.exists()) or path.is_dir()
    if directory_like:
        return path / f"{slugify(event_name)}-registration-attribution{suffix}"
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


def fetch_spreadsheet_records(spreadsheet_id: str) -> list[dict[str, Any]]:
    client = EventComposioClient()
    rows = extract_sheet_rows(client.read_spreadsheet(spreadsheet_id, "Sheet1"))
    return rows_to_records(rows)


def load_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{canonicalize_header(str(key)): normalize_space(value) for key, value in row.items() if key is not None} for row in reader]


def load_json_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("registrations", "data", "records", "items"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
        return [payload]
    raise SystemExit("JSON registrations file must contain a list or an object with registrations/data/records/items")


def load_registration_file(path_value: str) -> list[dict[str, Any]]:
    path = Path(path_value).expanduser()
    if not path.exists():
        raise SystemExit(f"Registration file not found: {path}")
    if path.suffix.lower() == ".csv":
        return load_csv_records(path)
    if path.suffix.lower() == ".json":
        return load_json_records(path)
    raise SystemExit("--registrations must point to a .csv or .json file")


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
    if text in {"true", "yes", "y", "1", "attended", "checked in", "showed", "present", "complete"}:
        return True
    if text in {"false", "no", "n", "0", "registered", "no show", "cancelled", "absent"}:
        return False
    return None


def canonicalize_channel(source: str, medium: str = "") -> str:
    text = f"{source} {medium}".lower()
    if not text.strip():
        return "Direct/Unknown"
    if any(token in text for token in ("email", "newsletter", "invite", "drip")):
        return "Email"
    if any(token in text for token in ("partner", "referral", "association", "co-marketing", "affiliate")):
        return "Partner"
    if any(token in text for token in ("paid social", "cpc", "paid", "ad", "ads", "sponsored")) and any(token in text for token in ("linkedin", "facebook", "instagram", "social", "x", "twitter")):
        return "Paid Social"
    if any(token in text for token in ("linkedin", "facebook", "instagram", "social", "x", "twitter")):
        return "Social Media"
    if any(token in text for token in ("organic", "seo", "search", "google")):
        return "Organic / SEO"
    if any(token in text for token in ("direct", "none", "unknown", "n/a")):
        return "Direct/Unknown"
    return normalize_space(source) or "Direct/Unknown"


def split_touchpoint_string(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\s*(?:>|→|\||;)\s*", value)
    cleaned = [normalize_space(part) for part in parts if normalize_space(part)]
    return cleaned or [normalize_space(value)]


def parse_touchpoints(record: dict[str, Any]) -> list[str]:
    for key in TOUCHPOINT_KEYS:
        raw = record.get(key)
        parsed = maybe_parse_json(raw)
        if isinstance(parsed, list):
            touchpoints: list[str] = []
            for item in parsed:
                if isinstance(item, dict):
                    source = normalize_space(item.get("source") or item.get("channel") or item.get("utm_source"))
                    medium = normalize_space(item.get("medium") or item.get("utm_medium"))
                    touchpoints.append(canonicalize_channel(source, medium))
                elif isinstance(item, str):
                    touchpoints.append(canonicalize_channel(item))
            if touchpoints:
                return touchpoints
        if isinstance(parsed, dict):
            source = normalize_space(parsed.get("source") or parsed.get("channel") or parsed.get("utm_source"))
            medium = normalize_space(parsed.get("medium") or parsed.get("utm_medium"))
            if source or medium:
                return [canonicalize_channel(source, medium)]
        if isinstance(raw, str) and raw.strip():
            split = split_touchpoint_string(raw)
            if split:
                return [canonicalize_channel(item) for item in split]

    source = first_text(record, SOURCE_KEYS)
    medium = first_text(record, MEDIUM_KEYS)
    return [canonicalize_channel(source, medium)]


def identifier_for(record: dict[str, Any], fallback_index: int) -> str:
    for key in ID_KEYS:
        value = normalize_space(record.get(key))
        if value:
            return value.lower()
    return f"row-{fallback_index}"


def normalize_registrants(records: list[dict[str, Any]]) -> list[Registrant]:
    deduped: dict[str, Registrant] = {}
    for index, record in enumerate(records, start=1):
        identifier = identifier_for(record, index)
        attended = None
        for key in ATTENDANCE_KEYS:
            attended = parse_bool(record.get(key))
            if attended is not None:
                break
        source_present = any(normalize_space(record.get(key)) for key in (*SOURCE_KEYS, *TOUCHPOINT_KEYS))
        registrant = Registrant(
            identifier=identifier,
            touchpoints=parse_touchpoints(record),
            attended=attended,
            industry=first_text(record, INDUSTRY_KEYS) or "Unknown",
            role=first_text(record, ROLE_KEYS) or "Unknown",
            geography=first_text(record, GEOGRAPHY_KEYS) or "Unknown",
            source_present=source_present,
        )

        existing = deduped.get(identifier)
        if existing is None:
            deduped[identifier] = registrant
            continue
        combined_attended = registrant.attended if registrant.attended is not None else existing.attended
        deduped[identifier] = Registrant(
            identifier=identifier,
            touchpoints=registrant.touchpoints if registrant.touchpoints != ["Direct/Unknown"] else existing.touchpoints,
            attended=combined_attended,
            industry=registrant.industry if registrant.industry != "Unknown" else existing.industry,
            role=registrant.role if registrant.role != "Unknown" else existing.role,
            geography=registrant.geography if registrant.geography != "Unknown" else existing.geography,
            source_present=registrant.source_present or existing.source_present,
        )
    return list(deduped.values())


def compute_models(registrants: list[Registrant]) -> dict[str, dict[str, float]]:
    models = {"last": {}, "first": {}, "multi": {}}
    for registrant in registrants:
        path = registrant.touchpoints or ["Direct/Unknown"]
        first = path[0]
        last = path[-1]
        models["first"][first] = models["first"].get(first, 0.0) + 1.0
        models["last"][last] = models["last"].get(last, 0.0) + 1.0
        weight = 1.0 / len(path)
        for touchpoint in path:
            models["multi"][touchpoint] = models["multi"].get(touchpoint, 0.0) + weight
    return models


def attendance_summary(registrants: list[Registrant]) -> dict[str, Any]:
    total = len(registrants)
    with_source = sum(1 for registrant in registrants if registrant.source_present)
    known_attendance = [registrant for registrant in registrants if registrant.attended is not None]
    attendees = sum(1 for registrant in known_attendance if registrant.attended)
    rate = (attendees / len(known_attendance)) if known_attendance else None
    benchmark_note = "Attendance benchmark unavailable"
    if rate is not None:
        if rate < 0.40:
            benchmark_note = "Attendance rate is below 40%, which signals a registration-quality or show-up problem."
        elif 0.45 <= rate <= 0.60:
            benchmark_note = "Attendance rate sits inside the 45-60% healthy range."
        elif rate > 0.60:
            benchmark_note = "Attendance rate is above the 45-60% healthy range."
        else:
            benchmark_note = "Attendance rate is between the warning zone and healthy range; monitor registration quality closely."
    return {
        "registrations": total,
        "with_source": with_source,
        "attendance_records": len(known_attendance),
        "attendees": attendees if known_attendance else None,
        "attendance_rate": rate,
        "benchmark_note": benchmark_note,
    }


def channel_rows(models: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    channels = set(models["last"]) | set(models["first"]) | set(models["multi"])
    rows = []
    for channel in sorted(channels):
        rows.append(
            {
                "channel": channel,
                "last_touch": round(models["last"].get(channel, 0.0), 2),
                "first_touch": round(models["first"].get(channel, 0.0), 2),
                "multi_touch": round(models["multi"].get(channel, 0.0), 2),
            }
        )
    rows.sort(key=lambda item: (-item["multi_touch"], -item["last_touch"], item["channel"]))
    return rows


def segment_rows(registrants: list[Registrant], dimension: str, values: list[str], overall_rate: float | None) -> list[SegmentRow]:
    grouped: dict[str, list[Registrant]] = {}
    for registrant, value in zip(registrants, values, strict=False):
        grouped.setdefault(value or "Unknown", []).append(registrant)

    rows: list[SegmentRow] = []
    for segment, items in grouped.items():
        attendance_known = [item for item in items if item.attended is not None]
        attendees = sum(1 for item in attendance_known if item.attended)
        rate = (attendees / len(attendance_known)) if attendance_known else None
        rows.append(
            SegmentRow(
                dimension=dimension,
                segment=segment,
                registrations=len(items),
                attendees=attendees if attendance_known else None,
                attendance_rate=rate,
                vs_average=(rate - overall_rate) if rate is not None and overall_rate is not None else None,
                small_sample=len(items) < 20,
            )
        )
    rows.sort(key=lambda item: (-item.registrations, item.segment.lower()))
    return rows


def build_segments(registrants: list[Registrant], overall_rate: float | None) -> dict[str, list[dict[str, Any]]]:
    return {
        "industry": [row.as_dict() for row in segment_rows(registrants, "industry", [item.industry for item in registrants], overall_rate)],
        "role": [row.as_dict() for row in segment_rows(registrants, "role", [item.role for item in registrants], overall_rate)],
        "geography": [row.as_dict() for row in segment_rows(registrants, "geography", [item.geography for item in registrants], overall_rate)],
    }


def primary_model_winner(channel_data: list[dict[str, Any]], model: str) -> str:
    field = {"last": "last_touch", "first": "first_touch", "multi": "multi_touch"}[model]
    if not channel_data:
        return "No attributed channels"
    top = max(channel_data, key=lambda item: item[field])
    return f"{top['channel']} leads the {model}-touch view with {top[field]:.2f} attributed registrations."


def recommendations(channel_data: list[dict[str, Any]], segments: dict[str, list[dict[str, Any]]], attendance: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if attendance["attendance_rate"] is not None and attendance["attendance_rate"] < 0.40:
        items.append("Fix the registration-to-attendance handoff first. A sub-40% attendance rate means channel efficiency alone is not the main problem.")
    unattributed_share = 1 - (attendance["with_source"] / attendance["registrations"]) if attendance["registrations"] else 0
    if unattributed_share > 0.20:
        items.append("Tighten source capture. More than 20% of registrations are unattributed, which weakens every channel decision downstream.")
    if channel_data:
        top = channel_data[0]
        items.append(f"Protect {top['channel']} in the next campaign plan, but do not over-credit it without checking the first-touch and multi-touch spread alongside last-touch.")

    for dimension in ("industry", "role", "geography"):
        under = next(
            (
                row
                for row in segments[dimension]
                if row["vs_average"] is not None and row["vs_average"] <= -0.20 and not row["small_sample"]
            ),
            None,
        )
        if under is not None:
            items.append(f"Rework messaging for {dimension} segment '{under['segment']}'. It trails the average attendance rate by {under['vs_average'] * 100:.1f} points.")
            break

    while len(items) < 3:
        items.append("Keep reporting first-touch, last-touch, and multi-touch together. The spread between models is the most honest attribution answer.")
    return items[:3]


def build_payload(event_name: str, primary_model: str, registrants: list[Registrant]) -> dict[str, Any]:
    attendance = attendance_summary(registrants)
    models = compute_models(registrants)
    channel_data = channel_rows(models)
    segments = build_segments(registrants, attendance["attendance_rate"])
    return {
        "event": event_name,
        "primary_model": primary_model,
        "summary": primary_model_winner(channel_data, primary_model),
        "attendance": attendance,
        "models": models,
        "channels": channel_data,
        "segments": segments,
        "recommendations": recommendations(channel_data, segments, attendance),
    }


def escape_cell(value: str) -> str:
    return normalize_space(value).replace("|", "\\|") or "—"


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def render_markdown(payload: dict[str, Any]) -> str:
    attendance = payload["attendance"]
    lines = [
        f"## Registration Analytics Report: {payload['event']}",
        f"**Data Completeness:** {attendance['with_source']}/{attendance['registrations']} registrants with source attribution, {attendance['attendance_records']} with attendance data.",
        f"**Primary Summary:** {payload['summary']}",
        f"**Attendance Benchmark:** {attendance['benchmark_note']}",
        "",
        "### Funnel Summary",
        "| Stage | Volume | Conversion | Benchmark |",
        "|-------|--------|-----------|-----------|",
        f"| Registration | {attendance['registrations']} | {format_percent(attendance['attendance_rate'])} → Attendance | 45-60% healthy; <40% signals problems |",
        f"| Attendance | {attendance['attendees'] if attendance['attendees'] is not None else 'n/a'} | n/a | n/a |",
        "",
        "### Attribution Summary",
        "| Channel | Last-Touch | First-Touch | Multi-Touch |",
        "|---------|-----------:|------------:|------------:|",
    ]
    for row in payload["channels"]:
        lines.append(
            f"| {escape_cell(row['channel'])} | {row['last_touch']:.2f} | {row['first_touch']:.2f} | {row['multi_touch']:.2f} |"
        )
    if not payload["channels"]:
        lines.append("| Direct/Unknown | 0.00 | 0.00 | 0.00 |")

    for dimension in ("industry", "role", "geography"):
        lines.extend(
            [
                "",
                f"### {dimension.title()} Segments",
                "| Segment | Registrations | Attendance Rate | vs. Average | Notes |",
                "|---------|---------------|-----------------|------------:|-------|",
            ]
        )
        rows = payload["segments"][dimension]
        for row in rows[:10]:
            notes = "small sample" if row["small_sample"] else ""
            vs_average = f"{row['vs_average'] * 100:+.1f} pts" if row["vs_average"] is not None else "n/a"
            lines.append(
                f"| {escape_cell(row['segment'])} | {row['registrations']} | {format_percent(row['attendance_rate'])} | {vs_average} | {notes or '—'} |"
            )
        if not rows:
            lines.append("| n/a | 0 | n/a | n/a | no data |")

    lines.extend(["", "### Recommendations"])
    for index, item in enumerate(payload["recommendations"], start=1):
        lines.append(f"{index}. {item}")

    return "\n".join(lines).strip() + "\n"


def render_dry_run_markdown(event_name: str, source: dict[str, Any], as_json: bool, model: str) -> str:
    lines = [
        f"# Registration Attribution — {event_name}",
        "",
        "## Dry Run",
        f"- Source: `{source['type']}`",
        f"- Primary model: `{model}`",
        f"- Output format: `{'json' if as_json else 'markdown'}`",
        "- Models that would be calculated: last-touch, first-touch, multi-touch (linear)",
    ]
    if source["type"] == "spreadsheet":
        lines.append(f"- Spreadsheet: `{source['spreadsheet_id']}`")
        lines.append("- Composio read skipped")
    else:
        lines.append(f"- Registration file: `{source['registrations_path']}`")
        lines.append("- Local parsing skipped")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_as_json = should_emit_json(args)
    source = (
        {"type": "spreadsheet", "spreadsheet_id": args.spreadsheet}
        if args.spreadsheet
        else {"type": "registrations_file", "registrations_path": str(Path(args.registrations).expanduser())}
    )

    if args.dry_run:
        if output_as_json:
            content = json.dumps(
                {
                    "dry_run": True,
                    "event": args.event,
                    "source": source,
                    "primary_model": args.model,
                },
                indent=2,
            )
        else:
            content = render_dry_run_markdown(args.event, source, output_as_json, args.model)
        write_output(content, resolve_output_path(args.output, args.event, output_as_json))
        return 0

    try:
        records = fetch_spreadsheet_records(args.spreadsheet) if args.spreadsheet else load_registration_file(args.registrations)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:
        print(f"Failed to load registration data: {exc}", file=sys.stderr)
        return 1

    registrants = normalize_registrants(records)
    payload = build_payload(args.event, args.model, registrants)
    content = json.dumps(payload, indent=2) if output_as_json else render_markdown(payload)
    write_output(content, resolve_output_path(args.output, args.event, output_as_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

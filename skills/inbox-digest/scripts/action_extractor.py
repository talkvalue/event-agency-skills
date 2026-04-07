#!/usr/bin/env python3
# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedCallResult=false
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from html import unescape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.composio_client import EventComposioClient
from lib.event_context import extract_dates, has_deadline_signals


THREAD_ID_KEYS = ("thread_id", "threadId", "gmail_thread_id", "gmailThreadId")
SUBJECT_KEYS = ("subject", "thread_subject", "threadSubject", "title")
TIER_KEYS = ("tier", "priority_tier", "priorityTier", "priority", "bucket", "section")
OUTPUT_LABELS = {
    "your": "YOUR ACTION",
    "awaiting": "AWAITING",
    "approval": "APPROVAL",
}
TIER_ALIASES = {
    "1": "1",
    "tier1": "1",
    "tier01": "1",
    "immediate": "1",
    "immediateactionrequired": "1",
    "urgent": "1",
    "2": "2",
    "tier2": "2",
    "tier02": "2",
    "today": "2",
    "actiontoday": "2",
    "3": "3",
    "tier3": "3",
    "tier03": "3",
    "tracking": "3",
    "track": "3",
    "fyi": "3",
}
DEADLINE_PHRASE_RE = re.compile(
    r"\b(?:eod|end of day|end of business|cob|close of business|today|tomorrow|tonight|this friday|this week|before load-?in|before the event|before show day)\b",
    re.IGNORECASE,
)
FIRST_PERSON_RE = re.compile(
    r"\b(?:i(?:'ll| will| can| am going to)|we(?:'ll| will| can| are going to)|let me|let us)\b",
    re.IGNORECASE,
)
COMMITMENT_RE = re.compile(
    r"\b(?:sending over|sharing|confirming by|circling back|following up|follow up|revert|deliver|provide|send|share|confirm|review|finalize|upload|submit|schedule|arrange|get back|check|update|advise|coordinate|return)\b",
    re.IGNORECASE,
)
APPROVAL_RE = re.compile(
    r"\b(?:approve|approval(?: needed)?|sign[ -]?off|signoff|signature|signatures|countersign|counter-sign|review and approve|pending approval|awaiting approval|awaiting your approval|contract|invoice|purchase order|\bpo\b|assets?|artwork|proof)\b",
    re.IGNORECASE,
)
LEADING_COMMITMENT_RE = re.compile(
    r"^(?:please\s+|kindly\s+|just\s+)?(?:i(?:'ll| will| can| am going to)|we(?:'ll| will| can| are going to)|they(?:'ll| will)|he(?:'ll| will)|she(?:'ll| will)|let me|let us|sending over|sharing|confirming by|following up|follow up(?:ing)?(?:\s+here)?|circling back)\s+",
    re.IGNORECASE,
)
DEADLINE_TRAIL_RE = re.compile(
    r"\s*(?:—|-|;|,)?\s*(?:by|before|due|confirm by|no later than)\s+[^.\n;]+$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ThreadTarget:
    thread_id: str
    subject: str | None = None
    tier: str | None = None


@dataclass(frozen=True)
class MessageView:
    sender_name: str
    sender_email: str
    subject: str
    body: str
    labels: tuple[str, ...]
    outgoing: bool


@dataclass(frozen=True)
class ActionItem:
    category: str
    description: str
    subject: str
    deadline: str | None = None
    who: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--digest", help="Path to triage digest JSON")
    source_group.add_argument("--threads", help="Comma-separated Gmail thread IDs")
    parser.add_argument("--event", required=True, help="Event name")
    parser.add_argument("--date", required=True, help="Event date (YYYY-MM-DD)")
    parser.add_argument("--output", help="Write markdown output to file instead of stdout")
    parser.add_argument(
        "--tiers",
        default="1,2",
        help='Tiers to process: "1", "1,2", or "1,2,3"',
    )
    return parser.parse_args()


def parse_event_date(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid --date value: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_tiers(value: str) -> tuple[str, ...]:
    tiers = tuple(sorted({part.strip() for part in value.split(",") if part.strip()}, key=int))
    if not tiers or set(tiers) - {"1", "2", "3"}:
        raise SystemExit('Invalid --tiers value. Use "1", "1,2", or "1,2,3".')
    return tiers


def maybe_parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def unwrap_action_result(value: Any) -> Any:
    current = maybe_parse_json(value)
    for _ in range(5):
        current = maybe_parse_json(current)
        if isinstance(current, dict) and "data" in current and any(
            key in current for key in ("successful", "error")
        ):
            current = current["data"]
            continue
        if isinstance(current, dict) and "response" in current:
            current = current["response"]
            continue
        break
    return maybe_parse_json(current)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_tier(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        return str(value) if value in (1, 2, 3) else None
    text = re.sub(r"[^a-z0-9]+", "", str(value).lower())
    if text in TIER_ALIASES:
        return TIER_ALIASES[text]
    match = re.search(r"([123])", text)
    return match.group(1) if match else None


def load_digest(path: str) -> Any:
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_thread_id(record: dict[str, Any]) -> str | None:
    for key in THREAD_ID_KEYS:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    generic_id = record.get("id")
    if isinstance(generic_id, str) and generic_id.strip() and any(
        key in record for key in (*SUBJECT_KEYS, "snippet", "body_preview", "sender_email", "sender")
    ):
        return generic_id.strip()
    return None


def extract_subject(record: dict[str, Any]) -> str | None:
    for key in SUBJECT_KEYS:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_space(value)
    return None


def iter_thread_targets(node: Any, inherited_tier: str | None = None) -> list[ThreadTarget]:
    results: list[ThreadTarget] = []
    if isinstance(node, dict):
        tier = inherited_tier
        for key in TIER_KEYS:
            direct = normalize_tier(node.get(key))
            if direct:
                tier = direct
                break
        thread_id = extract_thread_id(node)
        if thread_id:
            results.append(ThreadTarget(thread_id=thread_id, subject=extract_subject(node), tier=tier))
        for key, value in node.items():
            child_tier = tier or normalize_tier(key)
            results.extend(iter_thread_targets(value, child_tier))
    elif isinstance(node, list):
        for item in node:
            results.extend(iter_thread_targets(item, inherited_tier))
    return results


def thread_targets_from_digest(digest: Any, selected_tiers: tuple[str, ...]) -> list[ThreadTarget]:
    collected = iter_thread_targets(digest)
    deduped: dict[str, ThreadTarget] = {}
    for item in collected:
        if item.tier and item.tier not in selected_tiers:
            continue
        existing = deduped.get(item.thread_id)
        if existing is None:
            deduped[item.thread_id] = item
            continue
        deduped[item.thread_id] = ThreadTarget(
            thread_id=item.thread_id,
            subject=existing.subject or item.subject,
            tier=existing.tier or item.tier,
        )
    return list(deduped.values())


def direct_thread_targets(raw: str) -> list[ThreadTarget]:
    targets = [ThreadTarget(thread_id=part.strip()) for part in raw.split(",") if part.strip()]
    if not targets:
        raise SystemExit("No thread IDs provided via --threads")
    return targets


def extract_messages(payload: Any) -> list[dict[str, Any]]:
    data = unwrap_action_result(payload)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        messages = data.get("messages")
        if isinstance(messages, list):
            return [item for item in messages if isinstance(item, dict)]
        for key in ("thread", "result", "message"):
            nested = data.get(key)
            nested_messages = extract_messages(nested)
            if nested_messages:
                return nested_messages
        if any(key in data for key in ("payload", "snippet", "labelIds", "headers", "subject", "body")):
            return [data]
    if isinstance(data, str) and data.strip():
        return [{"body": data.strip()}]
    return []


def decode_body(data: str) -> str:
    stripped = data.strip()
    if not stripped:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9_\-+/=\s]+", stripped):
        return stripped
    candidate = stripped.replace("-", "+").replace("_", "/")
    candidate += "=" * (-len(candidate) % 4)
    try:
        decoded = base64.b64decode(candidate, validate=False).decode("utf-8")
    except Exception:
        return stripped
    return decoded if decoded.strip() else stripped


def strip_html(text: str) -> str:
    without_breaks = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.IGNORECASE)
    without_blocks = re.sub(r"</?(?:p|div|li|tr|td|h\d)[^>]*>", "\n", without_breaks, flags=re.IGNORECASE)
    stripped = re.sub(r"<[^>]+>", " ", without_blocks)
    return unescape(stripped)


def message_headers(message: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {}
    candidates = []
    if isinstance(message.get("headers"), list):
        candidates.extend(message["headers"])
    payload = message.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("headers"), list):
        candidates.extend(payload["headers"])
    for header in candidates:
        if isinstance(header, dict):
            name = header.get("name")
            value = header.get("value")
            if isinstance(name, str) and isinstance(value, str):
                headers[name.lower()] = value
    return headers


def collect_payload_text(part: dict[str, Any]) -> tuple[list[str], list[str]]:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    mime_type = str(part.get("mimeType") or "").lower()
    body = part.get("body")
    raw_data = None
    if isinstance(body, dict):
        raw_data = body.get("data")
    elif isinstance(body, str):
        raw_data = body
    if isinstance(raw_data, str) and raw_data.strip():
        decoded = decode_body(raw_data)
        if "html" in mime_type:
            html_parts.append(strip_html(decoded))
        else:
            plain_parts.append(decoded)
    for child in part.get("parts", []) if isinstance(part.get("parts"), list) else []:
        if not isinstance(child, dict):
            continue
        child_plain, child_html = collect_payload_text(child)
        plain_parts.extend(child_plain)
        html_parts.extend(child_html)
    return plain_parts, html_parts


def clean_body_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if line.startswith(">"):
            continue
        if re.match(r"^On .+ wrote:$", line, flags=re.IGNORECASE):
            break
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_message_body(message: dict[str, Any]) -> str:
    direct_fields = [
        message.get("plainTextBody"),
        message.get("bodyPreview"),
        message.get("body_preview"),
        message.get("bodyText"),
        message.get("body_text"),
        message.get("text"),
        message.get("snippet"),
    ]
    parts = [value for value in direct_fields if isinstance(value, str) and value.strip()]
    raw_body = message.get("body")
    if isinstance(raw_body, str) and raw_body.strip():
        parts.insert(0, decode_body(raw_body))
    elif isinstance(raw_body, dict) and isinstance(raw_body.get("data"), str):
        parts.insert(0, decode_body(raw_body["data"]))
    payload = message.get("payload")
    if isinstance(payload, dict):
        plain_parts, html_parts = collect_payload_text(payload)
        parts = plain_parts + html_parts + parts
    merged = "\n\n".join(clean_body_text(part) for part in parts if clean_body_text(part))
    return clean_body_text(merged)


def message_sender(message: dict[str, Any], headers: dict[str, str]) -> tuple[str, str]:
    from_header = headers.get("from")
    if isinstance(from_header, str) and from_header.strip():
        name, email = parseaddr(from_header)
        resolved_name = normalize_space(name) if name else email or "Unknown"
        return resolved_name, email.strip().lower()
    sender_name = message.get("sender_name") or message.get("senderName") or message.get("from_name")
    sender_email = message.get("sender_email") or message.get("senderEmail") or message.get("from")
    resolved_name = normalize_space(str(sender_name)) if sender_name else "Unknown"
    resolved_email = str(sender_email).strip().lower() if sender_email else ""
    return resolved_name, resolved_email


def message_subject(message: dict[str, Any], headers: dict[str, str], fallback: str | None) -> str:
    if isinstance(headers.get("subject"), str) and headers["subject"].strip():
        return normalize_space(headers["subject"])
    for key in SUBJECT_KEYS:
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_space(value)
    return fallback or "(No subject)"


def message_labels(message: dict[str, Any]) -> tuple[str, ...]:
    labels = message.get("labelIds") or message.get("labels") or []
    if isinstance(labels, list):
        return tuple(str(label) for label in labels)
    return ()


def build_message_views(messages: list[dict[str, Any]], fallback_subject: str | None) -> list[MessageView]:
    provisional: list[tuple[str, str, str, str, tuple[str, ...]]] = []
    self_emails: set[str] = set()
    for message in messages:
        headers = message_headers(message)
        sender_name, sender_email = message_sender(message, headers)
        subject = message_subject(message, headers, fallback_subject)
        body = extract_message_body(message)
        labels = message_labels(message)
        provisional.append((sender_name, sender_email, subject, body, labels))
        if "SENT" in labels and sender_email:
            self_emails.add(sender_email)
    views: list[MessageView] = []
    for sender_name, sender_email, subject, body, labels in provisional:
        outgoing = "SENT" in labels or (sender_email in self_emails and bool(sender_email))
        views.append(
            MessageView(
                sender_name=sender_name,
                sender_email=sender_email,
                subject=subject,
                body=body,
                labels=labels,
                outgoing=outgoing,
            )
        )
    return views


def candidate_sentences(subject: str, body: str) -> list[str]:
    parts = [subject] if subject and subject != "(No subject)" else []
    parts.extend(body.splitlines())
    sentences: list[str] = []
    seen: set[str] = set()
    for part in parts:
        for chunk in re.split(r"(?<=[.!?])\s+", part):
            cleaned = normalize_space(chunk.strip("-•* "))
            if len(cleaned) < 8:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            sentences.append(cleaned)
    return sentences


def clean_description(text: str) -> str:
    cleaned = re.sub(r"^(?:please|kindly|just)\s+", "", text, flags=re.IGNORECASE)
    cleaned = LEADING_COMMITMENT_RE.sub("", cleaned).strip(" -—;:,.\t")
    cleaned = DEADLINE_TRAIL_RE.sub("", cleaned).strip(" -—;:,.\t")
    cleaned = normalize_space(cleaned)
    if not cleaned:
        cleaned = normalize_space(text)
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def detect_deadline(text: str, message_text: str, event_date: datetime) -> str | None:
    for source in (text, message_text):
        dates = extract_dates(source)
        if dates:
            return dates[0]
    combined = f"{text}\n{message_text}"
    phrase_match = DEADLINE_PHRASE_RE.search(combined)
    if phrase_match:
        phrase = phrase_match.group(0).lower()
        if phrase in {"before load-in", "before load in"}:
            return f"before load-in ({(event_date - timedelta(days=1)).date().isoformat()})"
        if phrase in {"before the event", "before show day"}:
            return event_date.date().isoformat()
        return phrase_match.group(0)
    if has_deadline_signals(combined):
        clause = re.search(
            r"\b(?:by|before|due|confirm by|no later than)\s+([^.;\n]+)",
            combined,
            flags=re.IGNORECASE,
        )
        if clause:
            return normalize_space(clause.group(0))
        return "deadline mentioned"
    return None


def approval_from(message: MessageView) -> str:
    if message.sender_name and message.sender_name != "Unknown":
        return message.sender_name
    if message.sender_email:
        return message.sender_email
    return "You" if message.outgoing else "Thread participant"


def add_action_item(items: list[ActionItem], seen: set[tuple[str, str, str]], item: ActionItem) -> None:
    key = (item.category, item.subject.lower(), normalize_space(item.description).lower())
    if key in seen:
        return
    seen.add(key)
    items.append(item)


def extract_actions_from_messages(messages: list[MessageView], event_date: datetime) -> list[ActionItem]:
    items: list[ActionItem] = []
    seen: set[tuple[str, str, str]] = set()
    for message in messages:
        if not message.body and not message.subject:
            continue
        sentences = candidate_sentences(message.subject, message.body)
        message_text = "\n".join(sentences) if sentences else message.body
        for sentence in sentences:
            description = clean_description(sentence)
            if not description:
                continue
            deadline = detect_deadline(sentence, message_text, event_date)
            if message.outgoing and FIRST_PERSON_RE.search(sentence) and COMMITMENT_RE.search(sentence):
                add_action_item(
                    items,
                    seen,
                    ActionItem(
                        category="your",
                        description=description,
                        subject=message.subject,
                        deadline=deadline,
                    ),
                )
            elif (not message.outgoing) and COMMITMENT_RE.search(sentence):
                add_action_item(
                    items,
                    seen,
                    ActionItem(
                        category="awaiting",
                        description=description,
                        subject=message.subject,
                        deadline=deadline,
                        who=approval_from(message),
                    ),
                )
            if APPROVAL_RE.search(sentence):
                add_action_item(
                    items,
                    seen,
                    ActionItem(
                        category="approval",
                        description=description,
                        subject=message.subject,
                        deadline=deadline,
                        who=approval_from(message),
                    ),
                )
    return items


def render_item(index: int, item: ActionItem) -> str:
    if item.category == "your":
        line = f"{index}. [{OUTPUT_LABELS[item.category]}] {item.description}"
    elif item.category == "awaiting":
        who = item.who or "Someone"
        line = f"{index}. [{OUTPUT_LABELS[item.category]}] {who} to {item.description}"
    else:
        who = item.who or "Thread participant"
        line = f"{index}. [{OUTPUT_LABELS[item.category]}] {item.description} — from {who}"
    if item.deadline:
        line += f" — by {item.deadline}"
    line += f" — thread: {item.subject}"
    return line


def render_section(title: str, items: list[ActionItem]) -> list[str]:
    lines = [f"### {title}"]
    if not items:
        lines.append("_None found._")
        return lines
    for index, item in enumerate(items, start=1):
        lines.append(render_item(index, item))
    return lines


def build_markdown(event_name: str, tiers: tuple[str, ...], thread_count: int, items: list[ActionItem]) -> str:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    your_actions = [item for item in items if item.category == "your"]
    awaiting = [item for item in items if item.category == "awaiting"]
    approvals = [item for item in items if item.category == "approval"]
    lines = [
        f"## Action Items — {event_name}",
        f"Extracted: {timestamp}",
        f"Source: {thread_count} threads (Tier {','.join(tiers)})",
        "",
        *render_section("Your Actions", your_actions),
        "",
        *render_section("Awaiting Others", awaiting),
        "",
        *render_section("Approval Gates", approvals),
    ]
    return "\n".join(lines).rstrip() + "\n"


def resolve_targets(args: argparse.Namespace, tiers: tuple[str, ...]) -> list[ThreadTarget]:
    if args.digest:
        targets = thread_targets_from_digest(load_digest(args.digest), tiers)
        if targets:
            return targets
        raise SystemExit("No matching thread IDs found in digest JSON")
    return direct_thread_targets(args.threads)


def write_output(markdown: str, output_path: str | None) -> None:
    if not output_path:
        sys.stdout.write(markdown)
        return
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def main() -> int:
    args = parse_args()
    tiers = parse_tiers(args.tiers)
    event_date = parse_event_date(args.date)
    client = EventComposioClient()
    targets = resolve_targets(args, tiers)
    all_items: list[ActionItem] = []
    for target in targets:
        thread_payload = client.read_thread(target.thread_id)
        messages = build_message_views(extract_messages(thread_payload), target.subject)
        all_items.extend(extract_actions_from_messages(messages, event_date))
    markdown = build_markdown(args.event, tiers, len(targets), all_items)
    write_output(markdown, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Event context — phase calculation, urgency thresholds, stakeholder classification.

Shared domain logic used across all event agency skills.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class EventPhase(Enum):
    """Production phase based on days until event."""

    NORMAL = "normal"          # T-30+
    PLANNING = "planning"      # T-30 to T-8
    ADVANCE = "advance"        # T-7 to T-2
    LOAD_IN = "load_in"        # T-1
    SHOW_DAY = "show_day"      # T-0
    POST_EVENT = "post_event"  # T+1+

    @classmethod
    def from_days_out(cls, days: int) -> EventPhase:
        if days < 0:
            return cls.POST_EVENT
        if days == 0:
            return cls.SHOW_DAY
        if days == 1:
            return cls.LOAD_IN
        if days <= 7:
            return cls.ADVANCE
        if days <= 30:
            return cls.PLANNING
        return cls.NORMAL


class StakeholderType(Enum):
    """Event stakeholder classification."""

    VENDOR = "vendor"
    CLIENT = "client"
    SPONSOR = "sponsor"
    SPEAKER = "speaker"
    VENUE = "venue"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class PriorityTier(Enum):
    """Priority tier for email/task classification."""

    IMMEDIATE = 1   # Response needed within 1-2 hours
    TODAY = 2       # Needs attention this business day
    TRACKING = 3    # No action needed now


# ── Stakeholder detection signals ─────────────────────────────────

STAKEHOLDER_SIGNALS: dict[StakeholderType, list[str]] = {
    StakeholderType.VENDOR: [
        "av", "audio", "video", "lighting", "catering", "f&b",
        "food and beverage", "security", "decor", "floral",
        "florist", "transport", "logistics", "trucking",
        "staffing", "rentals", "print", "signage", "entertainment",
        "production company", "staging", "rigging",
    ],
    StakeholderType.CLIENT: [
        "contract", "fee", "payment", "invoice", "scope",
        "deliverable", "approval", "sign-off", "budget",
    ],
    StakeholderType.SPONSOR: [
        "activation", "booth", "logo", "sponsor", "sponsorship",
        "branding", "exhibit", "partnership", "package",
    ],
    StakeholderType.SPEAKER: [
        "speaker", "keynote", "session", "presentation",
        "bureau", "rider", "bio", "headshot", "abstract",
        "talk", "panel", "moderator", "fireside",
    ],
    StakeholderType.VENUE: [
        "venue", "hotel", "convention center", "ballroom",
        "dock", "load-in", "load in", "coi", "certificate of insurance",
        "floor plan", "site visit", "banquet", "catering manager",
    ],
}

# Keywords that signal urgency regardless of stakeholder type
URGENCY_KEYWORDS: list[str] = [
    "urgent", "asap", "immediately", "emergency", "critical",
    "deadline", "overdue", "past due", "final notice",
    "cancellation", "cancelled", "cancel", "delay", "delayed",
    "safety", "compliance", "violation", "insurance", "coi",
    "load-in", "load in", "strike", "delivery window",
    "rider", "run-of-show", "ros", "confirmation needed",
]

# Keywords that suggest a deadline exists in the body
DEADLINE_KEYWORDS: list[str] = [
    "by", "before", "deadline", "due", "confirm by",
    "no later than", "eod", "end of day", "end of business",
    "cob", "close of business", "this friday", "this week",
    "tomorrow", "today", "tonight",
]


@dataclass
class EventContext:
    """Context for an event — drives phase-aware urgency calculations."""

    event_name: str
    event_date: datetime
    now: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @property
    def days_until_event(self) -> int:
        delta = self.event_date.date() - self.now.date()
        return delta.days

    @property
    def phase(self) -> EventPhase:
        return EventPhase.from_days_out(self.days_until_event)

    @property
    def phase_label(self) -> str:
        days = self.days_until_event
        phase = self.phase
        labels = {
            EventPhase.NORMAL: f"Normal (T-{days})",
            EventPhase.PLANNING: f"Planning (T-{days})",
            EventPhase.ADVANCE: f"Advance Week (T-{days})",
            EventPhase.LOAD_IN: "Load-In (T-1)",
            EventPhase.SHOW_DAY: "Show Day (T-0)",
            EventPhase.POST_EVENT: f"Post-Event (T+{abs(days)})",
        }
        return labels[phase]

    def overdue_threshold_hours(self, stakeholder: StakeholderType) -> int:
        """Response time threshold in hours before an item is considered overdue."""
        phase = self.phase
        base_thresholds = {
            EventPhase.NORMAL: 48,
            EventPhase.PLANNING: 24,
            EventPhase.ADVANCE: 12,
            EventPhase.LOAD_IN: 2,
            EventPhase.SHOW_DAY: 1,
            EventPhase.POST_EVENT: 72,
        }
        base = base_thresholds[phase]

        # AV and venue get tighter thresholds
        if stakeholder in (StakeholderType.VENDOR, StakeholderType.VENUE):
            if phase in (EventPhase.ADVANCE, EventPhase.LOAD_IN, EventPhase.SHOW_DAY):
                return max(1, base // 2)
        return base

    def stale_threshold_hours(self, stakeholder: StakeholderType) -> int:
        """Hours after which a thread with no reply is flagged as stale."""
        phase = self.phase
        if phase == EventPhase.SHOW_DAY:
            return 1
        if phase == EventPhase.LOAD_IN:
            return 4
        if phase == EventPhase.ADVANCE:
            return 12

        # Default stale thresholds by stakeholder
        stale_defaults = {
            StakeholderType.VENDOR: 24,
            StakeholderType.CLIENT: 12,
            StakeholderType.VENUE: 24,
            StakeholderType.SPEAKER: 48,
            StakeholderType.SPONSOR: 48,
            StakeholderType.INTERNAL: 72,
            StakeholderType.UNKNOWN: 48,
        }
        return stale_defaults.get(stakeholder, 48)


def classify_stakeholder(
    sender_email: str,
    sender_name: str,
    subject: str,
    body_preview: str,
    known_domains: dict[str, StakeholderType] | None = None,
) -> StakeholderType:
    """Classify an email sender by stakeholder type.

    Args:
        sender_email: Sender's email address.
        sender_name: Sender's display name.
        subject: Email subject line.
        body_preview: First ~300 characters of the email body.
        known_domains: Optional mapping of domains to stakeholder types
                       (e.g., from a vendor/client contact list).
    """
    domain = sender_email.split("@")[-1].lower() if "@" in sender_email else ""

    # 1. Check known domains first (most reliable)
    if known_domains and domain in known_domains:
        return known_domains[domain]

    # 2. Scan signals in subject + body + sender name
    text = f"{sender_name} {subject} {body_preview}".lower()
    scores: dict[StakeholderType, int] = {st: 0 for st in StakeholderType}

    for stakeholder, signals in STAKEHOLDER_SIGNALS.items():
        for signal in signals:
            if signal in text:
                scores[stakeholder] += 1

    # 3. Pick highest-scoring type, with production-impact tiebreaker
    priority_order = [
        StakeholderType.VENDOR,
        StakeholderType.VENUE,
        StakeholderType.CLIENT,
        StakeholderType.SPEAKER,
        StakeholderType.SPONSOR,
        StakeholderType.INTERNAL,
    ]

    max_score = max(scores.values())
    if max_score == 0:
        return StakeholderType.UNKNOWN

    for st in priority_order:
        if scores[st] == max_score:
            return st

    return StakeholderType.UNKNOWN


def assign_priority(
    stakeholder: StakeholderType,
    subject: str,
    body_preview: str,
    thread_age_hours: float,
    event_context: EventContext,
) -> PriorityTier:
    """Assign priority tier to an email thread.

    Applies temporal overrides: vendor emails escalate when event is within 14 days.
    """
    text = f"{subject} {body_preview}".lower()
    days_out = event_context.days_until_event

    # Rule: Any vendor email mentioning load-in/rider/delivery within 14 days → Tier 1
    if stakeholder == StakeholderType.VENDOR and days_out <= 14:
        vendor_urgent = ["load-in", "load in", "rider", "delivery", "compliance", "install"]
        if any(kw in text for kw in vendor_urgent):
            return PriorityTier.IMMEDIATE

    # Rule: Any client email with a question → Tier 1
    if stakeholder == StakeholderType.CLIENT and "?" in f"{subject} {body_preview}":
        return PriorityTier.IMMEDIATE

    # Rule: Any urgency keyword → Tier 1
    if any(kw in text for kw in URGENCY_KEYWORDS):
        return PriorityTier.IMMEDIATE

    # Rule: Venue within 7 days → minimum Tier 1
    if stakeholder == StakeholderType.VENUE and days_out <= 7:
        return PriorityTier.IMMEDIATE

    # Rule: Stale threads (no reply past threshold) → escalate
    stale_hours = event_context.stale_threshold_hours(stakeholder)
    if thread_age_hours > stale_hours:
        if stakeholder in (StakeholderType.VENDOR, StakeholderType.CLIENT, StakeholderType.VENUE):
            return PriorityTier.IMMEDIATE

    # Default tiers by stakeholder
    default_tiers = {
        StakeholderType.VENDOR: PriorityTier.TODAY,
        StakeholderType.CLIENT: PriorityTier.TODAY,
        StakeholderType.VENUE: PriorityTier.TODAY,
        StakeholderType.SPEAKER: PriorityTier.TRACKING,
        StakeholderType.SPONSOR: PriorityTier.TRACKING,
        StakeholderType.INTERNAL: PriorityTier.TRACKING,
        StakeholderType.UNKNOWN: PriorityTier.TRACKING,
    }
    return default_tiers.get(stakeholder, PriorityTier.TRACKING)


def has_deadline_signals(text: str) -> bool:
    """Check if text contains deadline-related language."""
    lower = text.lower()
    return any(kw in lower for kw in DEADLINE_KEYWORDS)


def extract_dates(text: str) -> list[str]:
    """Extract date-like strings from text (basic pattern matching)."""
    patterns = [
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",  # 2026-03-28, 2026/03/28
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2}",  # March 28
        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*",  # 28 March
    ]
    dates = []
    for pattern in patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    return dates

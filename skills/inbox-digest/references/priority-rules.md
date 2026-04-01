# Priority Classification Rules

Emails are assigned to one of three tiers. Tiers determine when the production team must act and in what order items surface in the daily digest.

---

## Base Tier Definitions

| Tier | Label | Expected Response Window | Description |
|------|-------|--------------------------|-------------|
| **1** | Immediate | Within 1–2 hours | Threatens the event, requires urgent decision |
| **2** | Today | Within business hours | Needs action today to avoid downstream delays |
| **3** | Tracking | No action required | FYI, informational, or no pending decision |

---

## Tier 1 — Immediate

Apply Tier 1 when any of the following keywords appear in the subject or body:

| Keyword / Phrase | Scenario |
|------------------|---------|
| "cancel" / "cancellation" | Vendor, venue, or speaker canceling |
| "delay" / "delayed" | Critical shipment, load-in, or arrival delay |
| "urgent" / "URGENT" | Sender has flagged as time-critical |
| "deadline moved" | Contract, permit, or deliverable due date changed |
| "safety" / "safety concern" / "incident" | On-site or pre-event safety issue |
| "budget overrun" / "over budget" | Financial threshold exceeded |
| "COI expired" / "insurance lapsed" | Vendor cannot be on-site without valid COI |
| "permit denied" / "permit rejected" | Required permit not approved |
| "force majeure" | Contract clause invoked — legal + logistics impact |
| "breach" / "breach of contract" | Legal escalation signal |
| "not available" (from venue/vendor) | Availability conflict with confirmed booking |
| "venue closure" | Property closed or inaccessible |
| "weather hold" / "weather advisory" | Outdoor or transport-related weather risk |

**Action**: Surface at top of digest with red flag. Generate summary + suggested immediate response options.

---

## Tier 2 — Today

Apply Tier 2 when emails require a decision or response within the current business day:

| Keyword / Phrase | Scenario |
|------------------|---------|
| "confirm" / "please confirm" | Awaiting our confirmation |
| "approve" / "approval needed" | Requires sign-off from our team |
| "pending" | Item blocked until we respond |
| "schedule change" / "time change" | Logistics update requiring acknowledgment |
| "question about" | Vendor or client seeking clarification |
| "need by [date/time]" | Hard deadline attached to request |
| "awaiting" / "waiting on" | Our reply is the bottleneck |
| "revised proposal" / "updated quote" | New version needs review |
| "contract sent" | Signature or review needed |
| "final headcount" | Catering, seating, or credentialing confirmation |
| "advance sheet" | Advance documents ready for review |

**Action**: Surface in Today section. Group by stakeholder type.

---

## Tier 3 — Tracking

Apply Tier 3 when emails are informational with no pending decision:

| Keyword / Phrase | Scenario |
|------------------|---------|
| "FYI" | No action expected |
| "update" / "status update" | Progress report, no ask |
| "newsletter" | Marketing or industry newsletter |
| "recap" / "event recap" | Post-event summary |
| "attached for reference" | Document shared for awareness |
| "no action needed" | Explicitly flagged as informational |
| "save the date" | Calendar awareness only |
| "thank you" (standalone) | Courtesy reply, no open item |
| "out of office" | Auto-reply, may indicate delayed response |
| "introduction" | New contact introduction — no urgent ask |

**Action**: Group at bottom of digest. Collapse by default unless user preference is expanded.

---

## Stakeholder Default Tiers

When keyword signals are absent or ambiguous, default tiers apply by stakeholder type:

| Stakeholder Type | Default Tier | Rationale |
|-----------------|-------------|-----------|
| Vendor | Tier 2 | Vendor delays have direct operational impact |
| Client / Stakeholder | Tier 2 | Client satisfaction and approval chains are time-sensitive |
| Venue | Tier 2 | Venue holds dependencies for all other vendors |
| Sponsor | Tier 3 | Unless activation deadline or asset deadline is present |
| Speaker / Talent | Tier 3 | Unless rider, session details, or day-of logistics are outstanding |
| Internal | Tier 3 | Internal FYI unless flagged as decision-required |

**Override rule**: If any Tier 1 keyword is present, always escalate to Tier 1 regardless of stakeholder default.

---

## Temporal Override Rules

Standard tier assignments are modified based on proximity to event date.

### Advance Week Override (T-7 to T-1)

**Rule**: Beginning 7 days before the event, all vendor emails are bumped up one tier.

| Original Tier | Override Tier |
|--------------|--------------|
| Tier 3 | Tier 2 |
| Tier 2 | Tier 1 |
| Tier 1 | Tier 1 (unchanged) |

**Applies to**: Vendor emails only during the advance week window.

**Rationale**: In advance week, vendor non-responses cascade into production failures with no time to recover.

### Show Day Override (Event Day)

**Rule**: On event day, all emails from venue and vendor senders are automatically Tier 1.

| Stakeholder | Show Day Tier |
|------------|--------------|
| Venue | Tier 1 (always) |
| Vendor | Tier 1 (always) |
| Client | Tier 2 (unless Tier 1 keywords present) |
| Speaker / Talent | Tier 1 (if within 4 hours of set time) |
| Internal | Tier 2 (all-hands active) |

**Rationale**: On show day, every vendor and venue communication may affect the live event. There is no time for queued responses.

---

## Multi-Signal Conflicts

When an email triggers signals from multiple tiers, always apply the **highest tier** (lowest number):

```
Tier 1 keyword present → always Tier 1
Tier 1 absent + Tier 2 keyword present → Tier 2
Tier 1 and Tier 2 absent → Tier 3
```

**Example**: An email subject reads "FYI — vendor schedule change." "FYI" is Tier 3; "schedule change" is Tier 2. Result: **Tier 2**.

---

## Digest Ordering Within Tiers

Within each tier, sort by:

1. Event date proximity (nearest event first)
2. Stakeholder type (Venue > Client > Vendor > Sponsor > Speaker > Internal)
3. Timestamp (oldest unanswered first — longest-pending surfaces first)

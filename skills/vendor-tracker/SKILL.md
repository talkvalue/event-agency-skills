---
name: vendor-tracker
version: 2.0.0
description: "Event vendor status tracking — monitor contracts, deliverables, and deadlines with phase-aware escalation for live event productions. Use when checking vendor status, tracking deliverables, or managing vendor communications. Triggers: 'vendor status', 'vendor tracker', 'check vendors', 'vendor follow-up', 'vendor deliverables'."
tools: ["composio:GOOGLESHEETS_BATCH_GET", "composio:GOOGLESHEETS_BATCH_UPDATE", "composio:GMAIL_FETCH_EMAILS", "composio:GMAIL_CREATE_EMAIL_DRAFT", "composio:GOOGLECALENDAR_EVENTS_LIST"]
scripts: ["scripts/status_check.py", "scripts/escalation.py"]
---

# Vendor Tracker

## Purpose

Track vendor deliverables, contracts, and confirmations so nothing falls through the cracks in the final weeks before an event.

Event production depends on dozens of vendors delivering on time — AV, catering, florals, signage, security, staffing, transport. Each has different lead times, different failure modes, and different escalation paths. A late linen delivery is an inconvenience. A late AV crew is a catastrophe. This skill applies vendor-type-aware urgency and phase-based escalation to keep the production on track.

## When to Use

- Checking the status of all vendors for an upcoming event
- Identifying overdue deliverables before they become emergencies
- Preparing for a production meeting — "what's outstanding?"
- Managing the advance week (T-7 to T-1) when vendor urgency escalates
- Tracking contract and payment status across multiple vendors
- After a vendor misses a deadline — determining escalation path

## When NOT to Use

- **Not for initial vendor sourcing or RFP creation.** This skill tracks existing vendor relationships and deliverables, not vendor discovery or procurement.
- **Not for contract negotiation.** Use this to flag overdue contracts, not to negotiate terms or pricing.
- **Not for vendor payment processing.** Payment status is tracked for context, but actual payment execution is outside this skill's scope. Use budget-tracker for invoice management.
- **Not for on-site vendor management.** Day-of vendor coordination (where's the truck, who's on dock) is real-time operations, not status tracking.

## Inputs

| Input | Required | Default | Notes |
|-------|----------|---------|-------|
| Event name | Yes | — | For context and file naming |
| Event date | Yes | — | YYYY-MM-DD; drives phase detection and urgency calculations |
| Vendor data source | Yes | — | Spreadsheet ID, JSON file path, or verbal summary |
| Vendor list | No | — | If not provided, skill will ask for vendor names, types, and outstanding items |

## Quick Reference

### Vendor Types and Default Lead Times

| Type | Typical Lead Time | Failure Impact |
|------|-------------------|----------------|
| AV / Technical | 2-4 weeks | Critical — no AV = no event |
| Venue | Contracted months ahead | Critical — venue holds all vendor access |
| Catering / F&B | 2-3 weeks (final count 72h) | High — dietary/count changes cascade |
| Security | 1-2 weeks | High — compliance and safety |
| Decor / Floral | 1-2 weeks | Medium — visual but not operational |
| Signage / Print | 5-10 business days | Medium — wayfinding and branding |
| Transport / Logistics | 1-2 weeks | High — gear and people movement |
| Staffing Agencies | 1-2 weeks | Medium — replaceable if flagged early |
| Entertainment / Talent | Varies (rider-dependent) | High — contracted and non-fungible |
| Rentals | 1 week | Medium — tables, chairs, linens |

### Phase-Based Urgency Thresholds

| Phase | Window | Overdue Threshold | Escalation Speed |
|-------|--------|-------------------|------------------|
| Normal (T-30+) | 30+ days out | 48 hours no response | Standard: email → wait → follow-up |
| Planning (T-30 to T-8) | Planning period | 24 hours no response | Accelerated: email → same-day follow-up |
| Advance (T-7 to T-2) | Final prep week | 12 hours no response | Urgent: email → phone within 4 hours |
| Load-in (T-1) | Move-in day | 2 hours no response | Emergency: phone immediately, escalate to production lead |
| Show day (T-0) | Event day | 1 hour no response | Emergency: phone + contingency plan activation |

## Workflow by Task

### Task 1: Build Vendor Status Overview

**Script mode** (recommended):
```bash
python skills/vendor-tracker/scripts/status_check.py \
  --event "Summit 2026" \
  --date 2026-05-10 \
  --spreadsheet "SPREADSHEET_ID" \
  --output vendor-status.md
```

**Interactive mode** (Claude-guided with Composio tools):

1. Collect vendor data from the provided source.
   - Spreadsheet: `GOOGLESHEETS_BATCH_GET: spreadsheet_id={ID}, ranges="Sheet1"`
   - Or accept a JSON file / verbal list from user
2. For each vendor, capture:
   - **Vendor name and type** (AV, catering, venue, etc.)
   - **Contract status**: Signed / Pending / Not started
   - **Key deliverables**: What's expected and by when
   - **Payment status**: Deposit paid / Balance due / Fully paid
   - **Last communication date**: When was the last email or confirmation?
   - **Outstanding items**: What's still needed from them OR from us
3. Calculate current event phase based on event date.
4. Apply phase-based urgency to each outstanding item.
5. Sort vendors by urgency: Critical items first, then by vendor type impact.

### Task 2: Flag Overdue Items

1. For each vendor with outstanding items, check:
   - **Days since last communication** vs. phase-based threshold
   - **Days until deliverable deadline** — is there still time to recover?
   - **Vendor type impact** — AV/venue overdue is more critical than signage overdue
2. Flag items as:
   - **OVERDUE** — past deadline with no confirmation
   - **AT RISK** — approaching deadline, last communication exceeds threshold
   - **ON TRACK** — confirmed or within normal response window
   - **BLOCKED** — waiting on us, not the vendor
3. For BLOCKED items, clearly state what action our team needs to take to unblock.

### Task 3: Generate Escalation Actions

**Script mode:**
```bash
python skills/vendor-tracker/scripts/status_check.py \
  --event "Summit 2026" --date 2026-05-10 \
  --spreadsheet "ID" --json --output status.json

python skills/vendor-tracker/scripts/escalation.py \
  --status status.json --event "Summit 2026" --date 2026-05-10 \
  --create-drafts
```

For each OVERDUE or AT RISK item, recommend the appropriate escalation:

**Escalation path by vendor type:**

| Attempt | AV/Venue/Catering | Decor/Signage/Rentals | Staffing/Transport |
|---------|--------------------|-----------------------|--------------------|
| 1st | Follow-up email with original request quoted | Follow-up email | Follow-up email |
| 2nd | Phone call to account manager within 4h | Phone call next business day | Phone call next business day |
| 3rd | Escalate to production lead + contingency research | Source backup vendor | Source backup vendor |

For show day overdue: **Skip email. Phone call immediately.** **NEVER** send follow-up emails on show day — phone call or in-person only.

### Task 4: Generate Follow-Up Communications

For each vendor requiring follow-up:
1. Draft an email via Composio:
   ```
   GMAIL_CREATE_EMAIL_DRAFT: to={vendor_email}, subject="RE: {original_subject}", body={draft}
   ```
   The draft must:
   - Reference the original request or deliverable specifically
   - State the deadline clearly
   - Ask for a specific response ("Can you confirm delivery by [date]?")
   - Does NOT use guilt or pressure language — vendors respond better to clarity
2. For phone follow-ups, prepare a brief:
   - Vendor name and account manager
   - Specific item needed
   - Deadline and why it matters
   - Fallback question: "If [original plan] isn't possible, what's the alternative?"

## Output Format

### Vendor Status Dashboard

```
# Vendor Status — {Event Name}
Updated: {timestamp}
Event Date: {date} ({X days away} — {phase})
Vendors: {n} total · {n} on track · {n} at risk · {n} overdue · {n} blocked

## OVERDUE — Immediate Action Required

| Vendor | Type | Item | Due Date | Days Over | Last Contact | Action |
|--------|------|------|----------|-----------|--------------|--------|
| Sound Systems Inc | AV | Final equipment list | Mar 25 | 3 days | Mar 22 | Phone call to AM — [name] |
| Grand Hotel | Venue | COI confirmation | Mar 24 | 4 days | Mar 20 | Email + cc venue sales manager |

## AT RISK — Monitor Closely

| Vendor | Type | Item | Due Date | Last Contact | Risk |
|--------|------|------|----------|--------------|------|
| Bloom Florals | Decor | Centerpiece final count | Mar 28 | Mar 23 | Waiting on our headcount |

## ON TRACK

| Vendor | Type | Status | Next Milestone |
|--------|------|--------|----------------|
| SecureTeam | Security | Contract signed, crew confirmed | Badge list due Mar 30 |
| PrintCo | Signage | Proofs approved | Delivery Mar 29 |

## BLOCKED — Waiting on Us

| Vendor | Type | What They Need | Who Owns It | Deadline |
|--------|------|----------------|-------------|----------|
| City Catering | F&B | Final headcount | [Our team] | Mar 28 |
```

## Principles

1. **Vendor non-response is not neutral.** In event production, silence from a vendor means one of two things: they're handling it (good) or they've forgotten (bad). After the threshold, assume the latter and act. Waiting costs more than a redundant follow-up.

2. **Phase changes everything.** A 48-hour response gap in month one is fine. The same gap in advance week is a production risk. Always calculate urgency relative to event proximity, not absolute time.

3. **BLOCKED items are your team's problem, not the vendor's.** When a vendor is waiting on your headcount, your floor plan, or your approval — that's not a vendor issue. Surface these prominently so your team can act.

4. **Escalation is not confrontation.** The escalation path exists to get answers, not to punish vendors. Phone calls are faster than emails. Cc'ing a sales manager surfaces priority. Contingency research is preparation, not threat.

5. **AV and venue are never "medium" priority.** If AV or venue has an outstanding item within 14 days of the event, it's critical. Everything else can be worked around. These two cannot.

## What to Avoid

1. **Treating all vendors with the same urgency threshold.** AV overdue by 24 hours in advance week is a crisis. Rental linens overdue by 24 hours is a phone call. **MUST** apply vendor-type impact to every urgency assessment — AV overdue ≠ linen overdue.

2. **Sending follow-up emails on show day.** On event day, email is too slow. Phone call or in-person only. If you're emailing a vendor on show day, you've already lost time.

3. **Flagging vendor items as overdue when WE are the bottleneck.** **ALWAYS** check the BLOCKED column before flagging vendor items as overdue. If we haven't sent the headcount, the caterer can't confirm the menu. That's on us.

4. **Generic follow-up language.** "Just checking in on the status" doesn't get results. Name the specific deliverable, the specific deadline, and the specific ask: "Can you confirm the lighting plot will be delivered by Thursday 3/28?"

5. **Losing track of payment status alongside deliverable status.** A vendor with an unpaid balance may deprioritize your event. Track payment alongside deliverables — an overdue invoice is a production risk.

## Examples

**Follow-up email:**
- BAD: "Just checking in on the status of our order."
- GOOD: "Can you confirm the lighting plot will be delivered by Thursday 3/28? We need it to finalize the venue floor plan before Friday's walkthrough."

**Escalation tone:**
- BAD: "This is the third time we've reached out and we still haven't received confirmation."
- GOOD: "I know it's a busy season — want to confirm the March 28 delivery is still on track, or if the timeline has shifted so we can adjust our production schedule."

## Tool Integration

### Composio Tools (Primary)

| Tool | Action | Purpose | Safety Tier |
|------|--------|---------|-------------|
| **Sheets — read** | `GOOGLESHEETS_BATCH_GET` | Load vendor tracker spreadsheet | T1 Read |
| **Sheets — update** | `GOOGLESHEETS_BATCH_UPDATE` | Update vendor status rows | T2 Write |
| **Gmail — fetch** | `GMAIL_FETCH_EMAILS` | Check latest vendor communications | T1 Read |
| **Gmail — draft** | `GMAIL_CREATE_EMAIL_DRAFT` | Generate follow-up drafts | T2 Write |
| **Calendar — events** | `GOOGLECALENDAR_EVENTS_LIST` | Cross-reference event date for phase calculation | T1 Read |

### Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| **status_check.py** | `python skills/vendor-tracker/scripts/status_check.py --event "..." --date YYYY-MM-DD --spreadsheet ID` | Build vendor status dashboard with phase-aware urgency |
| **escalation.py** | `python skills/vendor-tracker/scripts/escalation.py --status status.json --event "..." --date YYYY-MM-DD` | Generate escalation communications and optionally create Gmail drafts |

## Composio Notes

### Sheets Read Pattern
```
GOOGLESHEETS_BATCH_GET: spreadsheet_id="ID", ranges="Sheet1!A:H"
```
Returns a 2D array. First row is typically headers. Map columns to vendor fields.

### Sheets Update Pattern
To update a specific vendor's status:
```
GOOGLESHEETS_BATCH_UPDATE: spreadsheet_id="ID", range="Sheet1!F3", values=[["CONFIRMED"]]
```

### Gmail Vendor Communication Check
Search for recent vendor emails:
```
GMAIL_FETCH_EMAILS: query="from:vendor@soundco.com", max_results=5
```

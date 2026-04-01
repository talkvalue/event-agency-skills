---
name: inbox-digest
version: 1.0.0
description: "Event inbox digest — classify emails by stakeholder type (vendor/client/sponsor/speaker/venue) and priority tier with temporal overrides. Use when triaging event email, starting your day on an event project, or before a production meeting. Triggers: 'triage inbox', 'email digest', 'inbox digest', 'event email', 'check my email'."
---

# Inbox Digest

## Purpose

Turn a chaotic event inbox into a prioritized, actionable digest classified by event stakeholder type.

Generic inbox triage tools treat all emails the same. Event production doesn't work that way. A venue contract revision three days before load-in outranks a sponsor asset submission with a two-week lead. A client asking "are we still on?" needs a same-hour response. A speaker requesting AV changes needs to reach your production team, not sit in your read pile.

This skill applies event production logic to your Gmail so you can walk into every production meeting, client call, or load-in day knowing exactly what needs to happen before anything else moves.

---

## When to Use

- **Starting your day on an active event project.** Run this before opening anything else. Classify the overnight and early-morning messages before context-switching fragments your attention.
- **Before a production meeting or client call.** Pull a fresh digest for the specific event so you can speak to every open thread without scrambling through your inbox during the call.
- **When you've been away and need to catch up.** Extended time range (48h, 72h, or custom). Get a full picture of what moved while you were out and identify anything that stalled waiting on you.
- **When multiple vendors, clients, and sponsors are emailing simultaneously.** The final week before an event. Conflicting timelines, overlapping asks, everyone wants confirmation. Classification prevents you from mis-prioritizing based on email volume rather than production impact.

---

## When NOT to Use

- **Not for composing or drafting email replies.** This skill triages and classifies — it does not write responses. Use it to decide what to respond to, then compose separately.
- **Not for non-event email.** Personal inbox, newsletters, or unrelated project threads should not be mixed in. Run this skill scoped to a specific event or project name.
- **Not for real-time event monitoring.** Use this for periodic triage (start of day, pre-meeting), not continuous inbox watching. It produces a point-in-time snapshot, not a live feed.
- **Not for email migration or cleanup.** This produces a prioritized digest, not inbox organization. It does not archive, label, move, or delete any messages.

---

## Inputs

| Input | Required | Default | Notes |
|-------|----------|---------|-------|
| Event / project name | Yes | — | Used as Gmail search query; match your email subject conventions (e.g., "Summit 2026", "Gala Oct") |
| Time range | No | 24h | Accepts: `24h`, `48h`, `72h`, `1w`, or custom date range `YYYY/MM/DD:YYYY/MM/DD` |
| Sender domains | No | — | Comma-separated list to narrow scope (e.g., `venuegroup.com,floraltrio.com`) |
| Save path | No | `{event-name}/digests/` | Override destination folder for the dated digest file |

---

## Quick Reference

#### Stakeholder Types
| Type | Key Signals |
|------|------------|
| Vendor | AV, catering, security, decor, transport, staffing, rentals |
| Client | Paying organization, corporate domain, C-suite/VP titles |
| Sponsor | Activation, booth, logo placement, sponsor deck |
| Speaker | Bureau domain, rider, session, keynote, bio and headshot |
| Venue | Hotel/convention center, dock, load-in, COI, floor plan |
| Internal | Own domain, team aliases, automated notifications |

#### Priority Tiers
| Tier | Response Window | Default |
|------|----------------|---------|
| 1 — Immediate | 1-2 hours | Vendor D-14, any cancellation/delay/safety |
| 2 — Today | Business hours | Vendor (default), Client, Venue |
| 3 — Tracking | No action | Sponsor, Speaker, Internal |

---

## Workflow by Task

### Task 1: Event Inbox Triage

**Objective:** Pull all relevant email for the event and classify each thread by stakeholder type and priority tier.

1. Ask the user: "Which event or project should I triage?" Accept a name or project code.
2. Confirm time range (default 24h) and any sender domain filters.
3. Run the triage query:
   ```
   gws gmail +triage --query "{event_name}" --max 50
   ```
   If a time range other than 24h is specified, append: `--after {start_date} --before {end_date}`
4. For each thread returned, parse:
   - **Sender name and domain**
   - **Subject line** — scan for keywords: advance, rider, COI, contract, invoice, PO, load-in, run-of-show, ROS, confirmation, revision, approval, hold, deposit, balance, dietary, accreditation, credential, badge, AV, logistics
   - **Thread age** — time since last message
   - **Body excerpt** — first 300 characters for deadline/commitment signals

   **MUST** apply temporal override rules before finalizing tier assignments.

5. Classify each thread by **Stakeholder Type**:

   | Type | Signals |
   |------|---------|
   | **Vendor** | Catering, AV, production company, trucking, decor, florist, entertainment, security, staffing agency, rentals, print shop |
   | **Client** | The contracting organization; often the event sponsor company paying the agency fee |
   | **Sponsor** | Brand partners contributing activation budgets or in-kind; distinct from the client even when the client also sponsors |
   | **Speaker** | Confirmed or prospective presenter; bureau reps count as Speaker-adjacent |
   | **Venue** | Hotel, convention center, outdoor site, venue coordinator, catering manager (venue-employed) |
   | **Internal** | Your own team, subcontractors on your roster, partner agencies on the same side of the table |

   When classification is ambiguous, default to the stakeholder type with the higher production impact (Vendor > Speaker > Venue for operational threads).

6. Assign **Priority Tier**:

   | Tier | Label | Criteria |
   |------|-------|---------|
   | **1** | Immediate | Requires response or action today. Blocked deliverable, time-sensitive approval, payment deadline within 48h, venue or vendor escalation, client waiting on confirmation, load-in logistics unresolved within 72h of event |
   | **2** | Today | Needs attention this workday but not this hour. Advancing information requests, asset submissions for review, draft approvals, speaker logistics confirmations more than 72h out |
   | **3** | Tracking | No action needed now. FYIs, confirmations of receipt, vendor acknowledgments, automated notifications, threads you're CC'd on |

   **Special rules:**
   - Any vendor email mentioning load-in, install, delivery window, or rider compliance is automatically Tier 1 if the event is within 14 days.
   - Any client email with a question mark in the subject or body is Tier 1.
   - Stale Tier 1 threads (no reply sent in 24h+) escalate to flagged status regardless of original priority.

---

### Task 2: Generate Digest

**Objective:** Format the classified threads into a structured digest document and save it.

1. Use the output format defined in the [Output Format](#output-format) section.
2. Check every thread for **stale status**: last message older than 24h with no outbound reply from your address. Flag these in the Stale Threads section.
3. Add a **digest header** with:
   - Event name
   - Digest generated timestamp
   - Time range covered
   - Total thread count by tier (e.g., "4 Immediate · 7 Today · 12 Tracking")
4. Save to a dated file:
   ```
   {save_path}/YYYY-MM-DD-{event-slug}-inbox-digest.md
   ```
   Example: `summit-2026/digests/2026-03-23-summit-2026-inbox-digest.md`
5. Confirm save path to user and offer to open the file.

---

### Task 3: Action Item Extraction (Optional)

**Objective:** Surface concrete commitments and deadlines buried in Tier 1 and Tier 2 threads.

Ask the user: "Would you like me to extract action items from Tier 1 and Tier 2 threads?"

If yes:
1. Re-read the body of each Tier 1 and Tier 2 thread using `gws gmail +read --thread-id {id}`.
2. Scan for:
   - **Commitments you made** ("I'll send", "we'll confirm", "will follow up")
   - **Commitments others made** ("will deliver", "sending over", "confirming by")
   - **Hard deadlines** (date + time mentions, "by EOD", "before load-in", "by Friday")
   - **Approval gates** (contracts awaiting signature, invoices awaiting PO, assets awaiting sign-off)
3. Format as a numbered action list appended to the digest:
   ```
   ## Action Items
   1. [YOUR ACTION] Send COI to Venue by 2026-03-24 — thread: RE: Insurance Requirements
   2. [AWAITING] AV vendor to deliver run-of-show by 2026-03-25 — thread: ROS Final Draft
   3. [APPROVAL NEEDED] Client sign-off on revised stage plot — thread: Stage Layout v3
   ```

---

## Output Format

### Digest Header
```
# Inbox Digest — {Event Name}
Generated: {timestamp}
Period: Last {time_range}
Threads: {n} Immediate · {n} Today · {n} Tracking · {n} Stale Flagged
```

### Tier 1 — Immediate Action Required

| Sender | Type | Subject | Action Needed | Deadline |
|--------|------|---------|---------------|----------|
| Sound Co. / soundco.com | Vendor | RE: Load-in window Tuesday | Confirm 6am access or request alternative | Today EOD |
| Sarah Chen (Client) | Client | Are we confirmed for AV walkthrough? | Reply with confirmation + logistics | ASAP |
| Grand Ballroom Venue | Venue | Certificate of Insurance — URGENT | Forward COI from broker | 2026-03-24 |

### Tier 2 — Action Today

| Sender | Type | Subject | Status |
|--------|------|---------|--------|
| Bloom Florals | Vendor | Centerpiece final count | Awaiting your headcount confirmation |
| Marcus Webb (Speaker) | Speaker | AV rider — updated version | Review and forward to AV vendor |
| TechCorp Sponsorship | Sponsor | Logo file submission | Assets received, needs review |

### Tier 3 — Tracking

- Sound Co. — RE: Contract countersigned _(receipt confirmation, no action)_
- Venue Catering — Menu confirmation _(acknowledged previous selection)_
- Badge Printer — Order #4821 processing _(automated update)_

### Stale Threads — No Reply 24h+

| Thread | Type | Age | Last Outbound | Recommended Action |
|--------|------|-----|---------------|--------------------|
| RE: Vendor rider compliance | Vendor | 36h | None | Send acknowledgment + ETA |
| Dressing room logistics | Venue | 48h | None | Follow up; confirm details locked |

---

## Principles

1. **Vendor emails are never low-priority.** A late response to a vendor in the final days before an event doesn't cause a delay — it causes a crisis. A florist who doesn't hear back may not show up. An AV company whose rider questions go unanswered may arrive under-staffed. Vendor threads default to Tier 2 at minimum, and Tier 1 any time the event is within 14 days or the subject touches load-in, delivery, compliance, or payment.

2. **Classify by what the email NEEDS, not who sent it.** A venue coordinator sending a friendly check-in that contains a contract revision question is a Tier 1 thread, not a Tier 3 one. Read the ask. The stakeholder type determines your response channel and urgency framing; the content determines the tier.

3. **Flag stale threads proactively.** **NEVER** generate a digest without checking stale threads. The stale thread section is the highest-value output. In event production, silence is interpreted as confirmation or abandonment. A thread you haven't replied to in 24h is actively creating risk: the vendor assumes you approved their timeline, the client assumes you're handling it, the speaker assumes they don't need to prepare. Surface stale threads every time, without exception.

4. **One digest, one event.** Do not mix threads from multiple events in a single digest. If you're running parallel events, run separate digests. Cross-event context collapse is how production details fall through the cracks.

---

## What to Avoid

1. **Listing without classification.** A raw email list sorted by time is not a digest — it's your inbox. Every thread in the output must have a stakeholder type and a tier. If you can't classify a thread, flag it as "Unclassified — review manually" rather than leaving it untagged.

2. **Treating all vendor emails as urgent.** Tier 1 is for threads that require action today. A vendor submitting their W-9 three weeks before the event is Tier 2 or Tier 3 depending on your payment timeline. Crying wolf on vendor urgency trains you to ignore the tier system the week it actually matters.

3. **Missing timeline and deadline mentions in the body.** Subject lines lie. **ALWAYS** scan the first 300 characters of every Tier 1 and Tier 2 thread body. "Quick question" subject lines often contain hard deadlines. "FYI" threads sometimes contain delivery windows that need verbal confirmation. If the body contains a date, a time, or the words "by", "before", "deadline", "due", or "confirm by" — that thread's tier may need to be upgraded.

4. **Generating a digest without checking stale threads.** The stale thread section is not optional. It is the highest-value output in the digest for active events. Skip it and you are producing a document that actively obscures risk.

5. **Generic classification ignoring event context.** A "catering" email from the hotel means something different when you're 72 hours from a 500-person gala than when you're 6 weeks out. Apply the event timeline. Apply the production phase (site visit, advance, production week, load-in, day-of, strike). A thread that would be Tier 3 in month one may be Tier 1 in week one.

---

## Tool Integration

| Tool | Command Pattern | Purpose |
|------|----------------|---------|
| **Gmail — triage** | `gws gmail +triage --query "{event_name}" --max 50` | Pull and classify event threads |
| **Gmail — read** | `gws gmail +read --thread-id {id}` | Read full thread body for action item extraction |
| **Calendar — agenda** | `gws calendar +agenda --query "{event_name}" --days 14` | Cross-reference email threads against event milestones; confirm load-in dates for tier escalation |
| **Sheets — read** | `gws sheets +read --spreadsheet-id {id}` | Load vendor/client/sponsor contact list to validate sender classification |
| **Drive — upload** | `gws drive +upload --file {digest_path} --folder {project_folder_id}` | Save completed digest to project Drive folder for team access |

**Workflow note:** Run Calendar cross-reference before finalizing tier assignments. An email that looks like Tier 2 may escalate to Tier 1 when you confirm the event is 5 days away, not 3 weeks.

---

## GWS Gotchas

### Gmail Search Scope
`--query` searches **subject + body** by default. Use `subject:` to narrow to subject only. For broad event match, use `"event_name" label:inbox`.

```bash
# WRONG — misses emails where keyword is only in body
gws gmail +triage --query 'subject:Summit'
# CORRECT — catches body mentions too
gws gmail +triage --query '"Summit 2026" label:inbox'
```

### Reply Without Message ID
When triaging emails from a **different inbox** (no message ID available):
1. Use `+send` instead of `+reply` (no threading possible)
2. **Ask for original subject line** — never guess
3. Save as `--draft` first for review

### Stale Detection Requires Full Thread
`+triage` returns summaries only. To check stale status accurately, read the full thread:
```bash
gws gmail +read --thread-id {id}
```
Check the last message timestamp against phase-based thresholds in `references/stale-thread-thresholds.md`.

### Shared Drive Digest Storage
When saving digest to a Shared Drive folder, include `supportsAllDrives`:
```bash
gws drive files create --json '{"name":"digest.md","parents":["FOLDER_ID"]}' \
  --upload ./digest.md --params '{"supportsAllDrives":true}'
```

---

## Resources

- [`references/event-email-patterns.md`](references/event-email-patterns.md) — Subject line patterns, sender domain conventions, and keyword lists for each stakeholder type. Use when classification is ambiguous.
- [`references/priority-rules.md`](references/priority-rules.md) — Full decision tree for tier assignment including event-phase overrides, payment deadline escalation logic, and client communication SLAs.
- [`references/stale-thread-thresholds.md`](references/stale-thread-thresholds.md) — Stale thresholds by stakeholder type and event phase. Vendor stale threshold differs from sponsor stale threshold. Day-of thresholds differ from advance thresholds.

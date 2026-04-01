# Stale Thread Thresholds

A thread is **stale** when a reply is expected but has not been received within the defined threshold. Staleness detection drives proactive escalation — waiting is not an option in event production.

---

## Staleness Thresholds by Production Phase

| Phase | Window | Description |
|-------|--------|-------------|
| **Normal operations** | 24 hours | Standard pre-event planning period (T-30 to T-8) |
| **Advance week** | 4 hours | T-7 to T-2 before event |
| **Load-in / Show day** | 1 hour | T-1 move-in day through event end |

**Clock starts** when the last message in the thread contains an unanswered question or a pending request directed at the other party.

---

## Detection Logic

A thread is flagged as stale when **all three conditions** are met:

### Condition 1 — Thread ends with an open question

The most recent message in the thread (before the elapsed threshold) contains:

| Signal type | Examples |
|-------------|---------|
| Direct question to recipient | "Can you confirm…?", "Are you available…?", "What is the status of…?" |
| Request with implied response needed | "Please send over…", "We need the COI by…", "Kindly confirm receipt" |
| Approval request | "Does this work for you?", "Please approve by…", "Awaiting your sign-off" |
| Ball explicitly in their court | "Over to you on this", "Let us know how you'd like to proceed" |

### Condition 2 — The unanswered party is identifiable

- Message was sent from our team's domain to an external party, **and** no reply has arrived; **or**
- External party sent a message tagging our team (by name, email, or role), and we have not replied

### Condition 3 — Threshold elapsed with no reply

- No message from the other party has been added to the thread within the defined window
- Out-of-office auto-replies **do not** count as a reply — they extend the stale flag with a note: "OOO — expected return [date]"

---

## Escalation Actions by Stakeholder Type

When a thread is confirmed stale, apply the following escalation path:

### Vendor

| Attempt | Action |
|---------|--------|
| First flag | Send follow-up email with original request quoted |
| Second flag (threshold elapsed again) | **Phone call** to vendor account manager or site ops contact |
| Third flag | Escalate internally to production lead; begin contingency vendor research |

**Note**: For show day stale vendor threads, skip to phone call immediately. Do not send a follow-up email first.

### Client

| Attempt | Action |
|---------|--------|
| First flag | Send gentle email nudge — acknowledge they may be busy, restate the ask clearly |
| Second flag | Follow up with a direct contact (if multiple client contacts exist) |
| Third flag | Escalate to account lead; flag for executive outreach if approval is blocking critical path |

**Tone guideline**: Client nudges must remain warm and professional. Do not express urgency or impatience in the message text — convey the operational need factually.

### Venue

| Attempt | Action |
|---------|--------|
| First flag | **Immediate escalation to production lead** — venue non-response has the highest downstream impact |
| Concurrent action | Send follow-up email to venue coordinator AND copy venue sales manager |
| If still unresolved | Production lead contacts venue directly by phone |

**Rationale**: Venue holds keys to all other vendor access. A stale venue thread on load-in day is a production emergency.

### Speaker / Talent

| Attempt | Action |
|---------|--------|
| First flag | Send follow-up to speaker's direct email (if available) |
| Second flag | **Contact bureau or agent directly** — do not wait for speaker to self-resolve |
| Third flag | Escalate to production lead; confirm backup plan for session if applicable |

**Note**: For keynote speakers, apply advance-week thresholds (4 hours) starting T-14, not T-7. Keynote logistics have longer lead requirements.

### Internal

| Attempt | Action |
|---------|--------|
| First flag | Ping on team Slack or project management tool (not email) |
| Second flag | Tag manager or project lead |

**Note**: Internal stale threads are lower severity unless they are blocking external vendor or client communications.

---

## Special Cases

### Out-of-Office Replies

- Do **not** reset the stale clock
- Add a note to the thread summary: "OOO reply received — contact returns [date]"
- If OOO return date is **after** a critical deadline, immediately escalate to the next available contact or their backup

### Partial Replies

- A reply that acknowledges receipt but does not answer the question **restarts the clock** for a new 24-hour / 4-hour / 1-hour window
- Log the partial reply as "acknowledged, pending full response"
- If the follow-up question remains unanswered after the new window, resume normal escalation path

### Chain Emails with Multiple Open Questions

- If a single thread contains multiple open questions from different senders, the **oldest unanswered question** determines staleness
- Surface all open questions in the digest summary, not just the most recent

### Threads Marked Stale in Error

- If a reply exists outside the tracked thread (e.g., a phone call was made, or a response came via Slack), mark the thread as **resolved externally** and log the resolution channel
- Production lead can dismiss stale flags manually with a note

---

## Threshold Reference Card

| Phase | Vendor | Client | Venue | Speaker | Internal |
|-------|--------|--------|-------|---------|----------|
| Normal (T-30 to T-8) | 24 hrs | 24 hrs | 24 hrs | 24 hrs | 24 hrs |
| Advance week (T-7 to T-2) | 4 hrs | 24 hrs | 4 hrs | 4 hrs | 24 hrs |
| Load-in (T-1) | 1 hr | 4 hrs | 1 hr | 1 hr | 4 hrs |
| Show day | 1 hr | 2 hrs | 1 hr | 1 hr | 2 hrs |

> Keynote speakers: use advance-week thresholds (4 hrs) from T-14 onward.

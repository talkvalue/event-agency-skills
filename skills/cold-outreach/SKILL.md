---
name: cold-outreach
version: 1.0.0
description: "Personalized B2B cold outreach for events — craft buyer, sponsor, and speaker prospecting emails with proven 4-touch follow-up sequences. Covers target profiling, role-specific angles, and quality checks for each email in the cadence. Triggers: 'cold email', 'outreach', 'prospecting', 'buyer email', 'sponsor outreach', 'speaker invitation'."
---

# Cold Outreach

## Purpose

Write cold emails that get replies — not by tricking recipients, but by making the event relevant to them specifically.

Event outreach fails when it reads like a mass blast. A wine importer doesn't care about your conference's "world-class programming." They care whether the buyers in the room match their distribution targets. A potential sponsor doesn't care about your attendee count. They care whether those attendees are the decision-makers they're trying to reach.

This skill takes a target list and event context, then produces personalized outreach with role-specific angles and a proven follow-up cadence.

## When to Use

- Prospecting buyers, sponsors, or speakers for an upcoming event
- Building a multi-touch outreach sequence (not just a single email)
- Re-engaging contacts from a previous event for a new edition
- Writing sponsor prospecting emails with activation-focused value propositions
- Personalizing speaker invitations with audience and topic alignment

## When NOT to Use

- **Not for warm leads or existing client relationships.** Cold outreach is for first contact. If you have an active relationship, use a different tone and approach — not this skill's templates.
- **Not for event logistics emails.** Vendor coordination, speaker travel, or venue communications are operational, not prospecting.
- **Not for mass email blasts.** This skill produces personalized, individual outreach. If you need to send the same message to 500 people, use a marketing automation tool.
- **Not for post-event follow-up.** Post-event thank-you's and re-engagement sequences have different timing and tone.

## Inputs

| Input | Required | Default | Notes |
|-------|----------|---------|-------|
| Target list | Yes | — | Names, companies, roles. From a spreadsheet, CRM export, or verbal list |
| Event context | Yes | — | Event name, dates, location, audience profile, value proposition |
| Target role | Yes | — | buyer / sponsor / speaker — determines the angle |
| Personalization data | No | — | Past attendance, industry, specific interests, mutual connections |
| Sequence length | No | 4-touch | D1 intro → D3 follow-up → D7 value-add → D14 break-up |

## Quick Reference

#### Role-Specific Angles
| Target Role | Lead With | CTA |
|------------|----------|-----|
| Buyer | Who else is in the room — attendees, speakers, exhibitors | Register / Schedule 1:1 |
| Sponsor | Audience match — "X% of attendees are [their target]" | Review deck / Schedule call |
| Speaker | Audience alignment — "attendees are [role/industry]" | Confirm interest / Share availability |

#### Sequence Cadence
| Email | Timing | Purpose |
|-------|--------|---------|
| 1 — Intro | Day 1 | Full personalized pitch, single CTA |
| 2 — Follow-up | Day 3-5 | One new piece of info, no repeat of pitch |
| 3 — Value-add | Day 7 | Share something useful, light event reference |
| 4 — Break-up | Day 14 | Acknowledge silence, remove pressure, leave door open |

## Workflow by Task

### Task 1: Target Profiling

1. Review the target list. For each contact, identify:
   - **Role relevance**: Why would this person care about this event?
   - **Personalization hook**: Past attendance, industry overlap, mutual connection, recent news
   - **Angle**: What's the ONE thing about this event that maps to their goals?
2. Group targets by role type (buyer / sponsor / speaker) — each gets a different angle.
3. Flag targets with insufficient personalization data — these need research before outreach.

### Task 2: Draft Role-Specific Emails

**For Buyers:**
- Lead with who else is in the room (other attendees, speakers, exhibitors they'd want to meet)
- Mention specific sessions or content tracks relevant to their industry
- CTA: Register / Schedule a 1:1 meeting / Join a specific session

**For Sponsors:**
- Lead with audience match: "X% of attendees are [their target demographic]"
- Offer specific activation ideas, not just "sponsorship opportunities"
- Include one concrete proof point (past sponsor results, attendee engagement data)
- CTA: Review the sponsorship deck / Schedule a call to discuss activation

**For Speakers:**
- Lead with audience alignment: "Our attendees are [role/industry] — your expertise in [topic] is exactly what they need"
- Mention the specific session format (keynote, panel, workshop, fireside chat)
- Be transparent about compensation/travel if applicable
- CTA: Confirm interest / Share availability for [date range]

For each email:
1. Write subject line — specific, no clickbait. Formula: `[Their Company/Name] + [Event Connection]`
2. Opening line — never "I hope this finds you well." Start with why you're reaching out to THEM specifically.
3. Body — one paragraph max. The value proposition for THEM, not for your event.
4. CTA — one ask, one action. Not "let me know if you're interested or if you'd prefer to chat or if you want the deck."
5. Signature — real person, real title, real contact info.

### Task 3: Build Follow-Up Sequence

For each target, generate a 4-touch sequence:

**Email 1 — Day 1 (Intro):**
- Full personalized pitch as drafted in Task 2
- Clear single CTA

**Email 2 — Day 3-5 (Follow-up):**
- Short. Add ONE new piece of information not in Email 1 (a speaker announcement, an early-bird deadline, a relevant attendee stat)
- Do NOT repeat the pitch from Email 1
- Do NOT open with "Just following up" or "Circling back"

**Email 3 — Day 7 (Value-add):**
- Share something genuinely useful — an industry insight, a relevant article, a case study from a past event
- Light reference to the event but lead with the value
- The subtext is "I'm being helpful, not just selling"

**Email 4 — Day 14 (Break-up):**
- Acknowledge the silence respectfully: "I know you're busy and [event] may not be the right fit right now"
- Offer an easy out: "If the timing isn't right, no worries at all"
- Leave the door open: "If things change, I'm here"
- This email often gets the highest reply rate because it removes pressure

### Task 4: Review and Quality Check

1. Read each email in the sequence back-to-back. Does the thread feel human or templated?
2. Check for **repeated phrases** across the sequence — the recipient sees the full thread. If Email 1 closes with "Looking forward to having [Company] at the table" and Email 3 says "Looking forward to connecting," that's a flag.
3. Verify every email has exactly ONE CTA.
4. Check subject lines — do they get more specific as the sequence progresses?
5. Confirm personalization hooks are accurate (company name, role, industry).

## Output Format

**Per target, produce the full 4-email sequence with subject lines and complete bodies:**

```
### [Contact Name] — [Company] ([Role Type])
**Angle:** [One sentence — why this event matters to them]
**Personalization hook:** [Specific detail — recent news, mutual connection, past attendance, industry overlap]

---

**Email 1 (Day 1 — Intro)**
Subject: [Specific, no clickbait. Formula: Their Company/Name + Event Connection]

[Opening line — reference something specific to THEM, never generic]
[One paragraph — the value proposition for THEM at this event]
[Single CTA — one ask, one action]
[Signature — real person, title, contact]

---

**Email 2 (Day 3-5 — Follow-up)**
Subject: Re: [Email 1 subject]

[Short — 2-3 sentences max]
[ONE new piece of information not in Email 1: speaker announcement, deadline, attendee stat]
[Restate CTA or offer a lower-friction alternative]

---

**Email 3 (Day 7 — Value-add)**
Subject: [New subject — tied to the value being shared, not the event pitch]

[Lead with something genuinely useful: industry insight, article, case study]
[Light reference to event — "this is also why we built [session/track] at [Event]"]
[Soft CTA or no CTA — the value IS the message]

---

**Email 4 (Day 14 — Break-up)**
Subject: Re: [Email 1 subject]

[Acknowledge silence respectfully — "I know [Event] may not be the right fit right now"]
[Offer an easy out — remove all pressure]
[Leave the door open — one sentence, warm close]
[No hard CTA — just availability if things change]
```

## Principles

1. **Personalization is not "Hi {First Name}."** Real personalization means the email could not have been sent to anyone else. Reference their company, their role, their industry, or something specific about why THIS event is relevant to THEM.

2. **One email, one ask.** **ALWAYS** include exactly one CTA per email. Multiple CTAs in a single email result in no action. Pick the one thing you want them to do.

3. **The break-up email is the closer.** Email 4 — the one where you say "no worries if not" — consistently gets the highest reply rate. It removes pressure and triggers reciprocity. Never skip it.

4. **Sequence emails must stand alone.** The recipient may not have read the previous email. Each message should make sense independently. Never reference "my last email" or "as I mentioned."

5. **Subject lines are promises.** A subject that says "Quick question" better contain an actual question. A subject that says "Invitation" better contain an actual invitation. Bait-and-switch subjects destroy trust.

## What to Avoid

1. **NEVER** open with "I hope this finds you well" or "Just following up." These openers signal a mass blast. Start with why you're contacting THIS person.

2. **Leading with your event's credentials instead of their benefit.** "We've been running events for 15 years" doesn't help the recipient. "87% of last year's attendees were C-suite in your industry" does.

3. **Repeating phrases across the sequence.** The recipient sees the full email thread. If you used "excited to connect" in Email 1, don't use it in Email 3. Vary naturally.

4. **Sending without reviewing the full thread.** **MUST** read all prior sent messages in the thread before drafting Email 2+. Never reuse closing lines, openers, or distinctive phrases from earlier messages.

5. **Generic sponsor pitches.** "We'd love to discuss sponsorship opportunities" is not an outreach email. Name a specific activation idea that maps to their brand. "A branded networking lounge targeting the 200 procurement leaders attending" beats "gold sponsorship package" every time.

## Examples

**Opening lines:**
- BAD: "I hope this finds you well. I wanted to reach out about an exciting opportunity..."
- GOOD: "Your team's expansion into Southeast Asian markets caught my eye — 40% of SommCon attendees are distributors in that region."

**Subject lines:**
- BAD: "Partnership Opportunity"
- GOOD: "SommCon 2026 — 200 wine distributors, [Company] should be there"

**Sponsor pitch:**
- BAD: "We'd love to discuss sponsorship opportunities for our upcoming conference."
- GOOD: "A branded tasting lounge in front of 200 procurement directors — here's what that looks like at SommCon."

## Tool Integration

| Tool | Command Pattern | Purpose |
|------|----------------|---------|
| **Sheets — read** | `gws sheets +read --spreadsheet {ID}` | Load target list with contact details and personalization data |
| **Gmail — draft** | `gws gmail +send --to {email} --subject {subj} --body {body} --draft` | Save emails as drafts for review before sending (T2) |
| **Gmail — send** | `gws gmail +send --to {email} --subject {subj} --body {body}` | Send after user approval (T3 — requires --dry-run first) |
| **Gmail — triage** | `gws gmail +triage --query "to:{email}" --max 10` | Check if prior outreach exists before sending |

## GWS Gotchas

### Email Body Formatting
- **Plain text**: use `\n\n` between paragraphs only. One paragraph = one continuous line.
- **HTML mode** (`--html`): use `<p>` tags. `\n` in HTML mode renders as literal text, not line breaks.
- Default to plain text for cold outreach — HTML formatting can trigger spam filters.

### Draft Management
No helper command for listing or deleting drafts. Use raw API:
```bash
GWS_ACCOUNT=user@domain.com gws gmail users drafts list --params '{"userId":"me"}'
```

### T3 Safety for Sends
Every `+send` (non-draft) requires `--dry-run` first:
```bash
gws gmail +send --to buyer@co.com --subject "..." --body "..." --dry-run
# Review preview, then:
gws gmail +send --to buyer@co.com --subject "..." --body "..."
```

### Multi-Account Sends
When sending from a non-default account, set `GWS_ACCOUNT`:
```bash
GWS_ACCOUNT=sales@agency.com gws gmail +send --from sales@agency.com ...
```

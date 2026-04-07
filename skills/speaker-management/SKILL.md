---
name: speaker-management
version: 2.0.0
description: "Speaker materials tracking, content quality, and deadline management for events. Tracks bios, headshots, session abstracts, learning outcomes, slide decks, and travel logistics with quality gates, reminder cadence, and deadline enforcement. Triggers: 'speaker management', 'speaker materials', 'speaker tracker', 'speaker status', 'speaker bio', 'speaker deadline', 'speaker reminder', 'session abstract', 'learning outcomes'."
tools: ["composio:GOOGLESHEETS_BATCH_GET", "composio:GOOGLESHEETS_BATCH_UPDATE", "composio:GMAIL_CREATE_EMAIL_DRAFT", "composio:GMAIL_SEND_DRAFT", "composio:GMAIL_FETCH_EMAILS", "composio:GOOGLEDRIVE_LIST_FILES", "composio:GOOGLEDRIVE_UPLOAD_FILE", "composio:GOOGLEDOCS_CREATE_DOCUMENT"]
scripts: ["scripts/materials_tracker.py"]
---

# Speaker Management

## Purpose

Keep every speaker on track — materials collected, content polished, deadlines hit — so the event team never scrambles the week before the conference.

Speaker management breaks down when it's treated as a one-time ask. You send the speaker form, they half-fill it, you chase them three times, and the week before the event you're still missing headshots and session abstracts. Meanwhile, the bios that did come in are full of "thought leader" and "passionate about" filler that nobody wants to read from stage.

This skill turns speaker management into a system: a clear deadline framework, a materials checklist with quality gates, and automated reminders that escalate as deadlines approach. Every speaker asset — bio, headshot, abstract, slides — gets tracked, quality-checked, and finalized before it becomes someone else's emergency.

## When to Use

- Onboarding new speakers and collecting their materials package
- Tracking which speakers have submitted what (and what's still missing)
- Quality-checking bios, session descriptions, and learning outcomes before publication
- Generating reminder emails for overdue or upcoming speaker deadlines
- Preparing the speaker roster for the program, website, or emcee run-of-show
- Auditing speaker content for fluff words, weak verbs, or inconsistent formatting

## When NOT to Use

- **Not for speaker recruitment or topic selection.** This skill manages materials from confirmed speakers. For finding and inviting speakers, use cold-outreach.
- **Not for session scheduling or agenda building.** This tracks speaker content deliverables, not which session goes in which time slot.
- **Not for speaker travel booking.** Travel info is tracked as a deliverable, but actual booking is outside scope.
- **Not for audience-facing content creation.** This quality-checks speaker-submitted content. It does not create marketing copy, social posts, or promotional materials about speakers.

## Inputs

| Input | Required | Default | Notes |
|-------|----------|---------|-------|
| Speaker list | Yes | — | Names, titles, companies, session topics. From a spreadsheet, CRM, or verbal list |
| Event context | Yes | — | Event name, dates, location, audience profile |
| Event date | Yes | — | Anchor date for the deadline framework (D-30, D-21, etc.) |
| Materials tracker | No | — | Existing spreadsheet or sheet tracking submission status |
| Speaker submissions | No | — | Raw bios, abstracts, headshots already received |

## Quick Reference

### Bio Format Variants

- **25-word emcee intro**: "Please welcome [Name], [credential] who [achievement]." Must be speakable — read it aloud before finalizing.
- **50-word program bio**: Name + expertise + 1-2 achievements + one humanizing detail. Third person.
- **100-word website bio**: Expanded credentials, professional-approachable tone, third person. Slight warmth, no fluff.
- **LinkedIn teaser** (for event promotion): First-person, 2-3 sentences, ends with a hook that makes people want to attend.

### Materials Checklist

| Material | Spec | Deadline |
|----------|------|----------|
| Bio (all formats) | 25 / 50 / 100-word variants, third person | D-30 |
| Headshot | Min 300x300px, professional, high-res preferred | D-30 |
| Session title + abstract | 75-word abstract, attendee-focused | D-21 |
| Learning outcomes | 3 outcomes, action verbs ONLY | D-21 |
| AV / tech requirements | Mic type, demo needs, special setup | D-21 |
| Slide deck | Final version, event template applied | D-14 |
| Travel info | Flights, hotel, ground transport | D-7 |
| Dietary / accessibility | Allergies, mobility, accommodations | D-7 |
| Final confirmation | Attendance + schedule confirmed | D-1 |

### Deadline Framework

| Milestone | Deadline | What's Due |
|-----------|----------|------------|
| D-30 | 30 days before event | Bio (all formats) + headshot |
| D-21 | 21 days before event | Session abstract + learning outcomes + AV requirements |
| D-14 | 14 days before event | Final slide deck |
| D-7 | 7 days before event | Travel info + dietary/accessibility |
| D-1 | 1 day before event | Final confirmation |

### Session Description Formula

1. **Opening hook** — what's at stake or what problem this solves (15 words)
2. **What attendees will learn or do** (30 words)
3. **Specific takeaways** they'll leave with (20 words)
4. **Why it matters right now** (10 words)

### Learning Outcome Verbs

**ALWAYS use:** Implement, Apply, Build, Create, Deploy, Evaluate, Identify, Master

**NEVER use:** Explore, Discuss, Learn about, Understand, Discover, Dive into, Unpack

### Banned Fluff Words

Never allow these in any speaker bio or session description:

thought leader, visionary, guru, passionate about, world-class, cutting-edge, revolutionary, groundbreaking, leverage, synergize, transformative, innovative

**Replace with:** specific numbers, named clients or events, measurable outcomes, concrete credentials.

## Workflow by Task

### Task 1: Status Review

1. Load the speaker list from the tracker spreadsheet or CRM.
2. For each speaker, check which materials have been received:
   - Bio (25 / 50 / 100-word) — received? quality-checked?
   - Headshot — received? meets 300x300 minimum?
   - Session title + abstract — received? attendee-focused?
   - Learning outcomes — received? action verbs only?
   - Slides — received? event template applied?
   - Travel + dietary — received?
   - Final confirmation — received?
3. Flag speakers with overdue materials based on the deadline framework.
4. Generate a status dashboard (see Output Format below).

### Task 2: Materials Gap Analysis

1. Compare the materials checklist against what's been received for each speaker.
2. Identify gaps by urgency:
   - **Critical** (past deadline): Materials that should have been submitted by now
   - **Upcoming** (within 7 days of deadline): Materials due soon
   - **On track**: Materials not yet due
3. For each gap, note what's missing and the contact to follow up with.
4. Prioritize: speakers with the most missing materials or closest deadlines first.

### Task 3: Bio / Content Quality Check

For each submitted bio:
1. Verify all three format variants exist (25-word, 50-word, 100-word).
2. Check for banned fluff words — flag and suggest replacements.
3. Confirm third-person consistency throughout.
4. Read the 25-word emcee intro aloud — does it flow naturally when spoken? No tongue-twisters, no awkward pauses.
5. Verify the narrative is consistent across all bio lengths — same core story, different depths.

For each session description:
1. Is it attendee-focused? Test: does it describe what the ATTENDEE gains, not what the SPEAKER shares?
   - **Bad**: "In this session, I'll share my 10 years of experience..."
   - **Good**: "Walk away with a tested framework you can implement next week."
2. Does it follow the session description formula (hook → learn → takeaways → why now)?
3. Are learning outcomes written with action verbs from the ALWAYS list?
4. Flag any outcomes using verbs from the NEVER list.
5. Does this description make someone want to attend?

### Task 4: Reminder Draft Generation

Generate reminder emails based on the gap analysis:

**First reminder (at deadline):**
- Friendly, specific. Name the exact materials that are missing.
- Include the original deadline and why the materials matter.
- Provide a direct link or clear instructions for submission.
- Single CTA: "Please submit [specific item] by [date]."

**Second reminder (deadline + 3 days):**
- Shorter. Acknowledge they're busy.
- Restate what's missing — don't make them hunt for the original email.
- Escalate the urgency: "We're finalizing the program on [date] and need your [item] to include your session."

**Final reminder (deadline + 7 days):**
- Direct. "We haven't received [item]. Without it by [date], we'll need to [consequence]."
- Keep the tone respectful but clear about impact.
- Offer help: "If you're having trouble with [item], I'm happy to assist."

For each reminder:
1. Personalize with speaker name, session title, and specific missing items.
2. Never use "Just following up" or "Circling back" as openers.
3. One email, one ask — don't bundle multiple missing items into a vague request.

## Output Format

**Speaker Status Dashboard:**

```
## Speaker Status — [Event Name] ([Event Date])
Updated: [current date]

| Speaker | Company | Bio | Headshot | Abstract | Outcomes | Slides | Travel | Dietary | Confirmed |
|---------|---------|-----|----------|----------|----------|--------|--------|---------|-----------|
| Jane Kim | Acme Corp | ✅ | ✅ | ✅ | ⚠️ weak verbs | ❌ D-14 | ❌ D-7 | ❌ D-7 | — |
| Alex Park | Neo4j | ✅ | ❌ overdue | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sam Lee | DataCo | ❌ D-30 | ❌ D-30 | — | — | — | — | — | — |

### Legend
- ✅ Received and quality-checked
- ⚠️ Received but needs revision (see notes)
- ❌ Missing (deadline shown)
- — Not yet due

### Action Items
1. **Jane Kim**: Learning outcomes use "Explore" and "Understand" — rewrite with action verbs. Slides due D-14. Send travel/dietary reminder.
2. **Alex Park**: Headshot missing — overdue. Send second reminder.
3. **Sam Lee**: No materials received. Send first reminder for bio + headshot (D-30 passed).
```

**Per-speaker quality report (when running Task 3):**

```
### [Speaker Name] — Content Quality Report

**Bio (25-word):** ✅ Speakable, clean
**Bio (50-word):** ⚠️ Contains "thought leader" — replace with specific credential
**Bio (100-word):** ⚠️ Switches to first person in sentence 3 — fix to third person
**Session abstract:** ✅ Attendee-focused, follows formula
**Learning outcomes:**
  - ✅ "Implement a graph-based data model for supply chain visibility"
  - ❌ "Explore best practices for data governance" → rewrite: "Evaluate three data governance frameworks and select the best fit for your org"
  - ✅ "Build a working prototype using Neo4j and Python"
```

## Principles

1. **Attendee-focused, always.** Session descriptions and learning outcomes exist to help the attendee decide whether to attend. If a description talks about what the speaker will "share" or "discuss," rewrite it around what the attendee will GAIN, BUILD, or APPLY.

2. **Speakable emcee intros.** The 25-word bio will be read aloud by an emcee who may have never met the speaker. Read it out loud. If you stumble, rewrite it. No jargon-dense titles, no acronym soup, no sentences that require a breath mid-clause.

3. **Consistency across assets.** The same speaker should sound cohesive whether their bio appears in the app, on the website, in the printed program, or in an email. Same core narrative, different lengths. Not three different people.

4. **Deadlines are walls, not suggestions.** The deadline framework exists because downstream teams (design, print, web, emcee) depend on speaker materials at specific points. A late headshot means a blank square in the program. A late abstract means a generic session listing. Communicate this to speakers clearly.

5. **One reminder, one ask.** Don't send a reminder that says "please submit your bio, headshot, abstract, outcomes, and slides." Send a reminder for the one thing that's most overdue. Stacking asks in a single email results in nothing submitted.

## What to Avoid

1. **Fluff words in bios.** "Thought leader," "visionary," "guru," "passionate about," "world-class," "cutting-edge," "revolutionary," "groundbreaking," "leverage," "synergize," "transformative," "innovative." Replace every instance with a specific number, named client, or measurable outcome.

2. **Weak learning outcome verbs.** "Explore," "Discuss," "Learn about," "Understand," "Discover," "Dive into," "Unpack." These describe the speaker's activity, not the attendee's outcome. Use: Implement, Apply, Build, Create, Deploy, Evaluate, Identify, Master.

3. **Speaker-centered session descriptions.** "In this talk, I'll share..." focuses on the speaker. "Walk away with a tested framework you can deploy Monday morning" focuses on the attendee. Always the latter.

4. **Inconsistent narrative across bio lengths.** If the 50-word bio leads with their role at Company X, the 100-word bio shouldn't lead with their academic background. Same person, same story, different depths.

5. **Chasing without a system.** Sending ad-hoc "hey, any update?" emails leads to materials falling through the cracks. Use the deadline framework and reminder cadence. Track every touchpoint.

6. **Accepting raw speaker bios without editing.** Speakers submit bios written for their own websites, not for your event. Always rewrite into event-ready format — third person, no fluff, correct lengths.

## Tool Integration

### Composio Tools (Primary)

| Tool | Action | Purpose | Safety Tier |
|------|--------|---------|-------------|
| **Sheets — read** | `GOOGLESHEETS_BATCH_GET` | Load speaker roster and materials tracker | T1 Read |
| **Sheets — update** | `GOOGLESHEETS_BATCH_UPDATE` | Update submission status | T2 Write |
| **Gmail — check** | `GMAIL_FETCH_EMAILS` | Check prior correspondence with a speaker | T1 Read |
| **Gmail — draft** | `GMAIL_CREATE_EMAIL_DRAFT` | Save reminder emails as drafts | T2 Write |
| **Gmail — send** | `GMAIL_SEND_DRAFT` | Send reminders after approval | T3 Dangerous |
| **Drive — find** | `GOOGLEDRIVE_LIST_FILES` | Find submitted headshots, slides, bios | T1 Read |
| **Drive — upload** | `GOOGLEDRIVE_UPLOAD_FILE` | Upload processed speaker assets | T2 Write |
| **Docs — create** | `GOOGLEDOCS_CREATE_DOCUMENT` | Create speaker content documents | T2 Write |

### Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| **materials_tracker.py** | `python skills/speaker-management/scripts/materials_tracker.py --event "..." --date YYYY-MM-DD --spreadsheet ID` | Speaker materials status dashboard with deadline compliance and quality checks |

## Composio Notes

### Speaker File Search
Search for speaker assets across Drive:
```
GOOGLEDRIVE_LIST_FILES: query="name contains 'headshot' and 'Kim'"
```

### Reminder Email Safety
Reminder sends are T3 operations. Always create a draft first (`GMAIL_CREATE_EMAIL_DRAFT`), preview with the user, then send (`GMAIL_SEND_DRAFT`) after explicit approval.

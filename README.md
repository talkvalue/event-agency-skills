# Event Agency Skills

**AI skills for event professionals — inbox triage, vendor management, and production coordination.**

![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Claude Code Compatible](https://img.shields.io/badge/Claude%20Code-compatible-blueviolet)

> Built by **[TalkValue](https://trytalkvalue.com)** — Event AI Consulting

---

## What Is This?

A collection of AI skills built for event professionals. Each skill encodes real event production knowledge — stakeholder classification, production priority logic, vendor management workflows — so your AI assistant works like someone who's actually run events, not a generic chatbot.

Generic inbox tools don't know that a venue contract revision three days before load-in outranks a sponsor asset submission with a two-week buffer. These skills do. They connect to your Gmail, Calendar, and Drive through the [gws CLI](https://github.com/googleworkspace/cli) and apply event-specific reasoning automatically.

---

## Prerequisites

```bash
# Install the official Google Workspace CLI
brew install gws  # or: npm i -g @google-workspace/cli

# Authenticate and generate base skills
gws auth login
gws generate-skills
```

This pack requires the `gws` base skills to be generated before use. The `gws-gmail`, `gws-gmail-triage`, `gws-calendar`, `gws-drive`, `gws-sheets`, and `gws-docs` skills must be available in your Claude Code environment.

---

## Quick Start

```bash
# Add the marketplace and install
claude plugin marketplace add talkvalue/event-agency-skills
claude plugin install event-agency-skills
```

Once installed, invoke skills by name in any Claude Code session:

```
/recipe-event-inbox-digest
/persona-event-coordinator
```

---

## Skills

| Skill | Type | What It Does | When to Use |
|-------|------|--------------|-------------|
| [`recipe-event-inbox-digest`](skills/recipe-event-inbox-digest/SKILL.md) | Recipe | Triages Gmail for a specific event project, classifies threads by stakeholder type (vendor/client/sponsor/speaker/venue), assigns priority tiers, flags stale threads, and outputs a structured digest | Start of day on an active event, before a production meeting, catching up after time away |
| [`persona-event-coordinator`](skills/persona-event-coordinator/SKILL.md) | Persona | Activates a full event coordination operating model across Gmail, Calendar, Drive, Sheets, and Docs — daily morning routine, vendor thread management, document control, and stakeholder updates | Ongoing event project coordination from kickoff through post-event wrap |

---

## How It Works

Each skill combines two things: **gws CLI commands** (the data layer) and **event domain logic** (the expertise layer).

- **Recipe skills** run multi-step workflows — they fetch data from Gmail/Calendar/Sheets, apply event-specific classification rules, and produce structured output.
- **Persona skills** activate an operating model — they set daily routines, define response SLAs, and connect multiple tools into a coherent coordination workflow.

### Example: `/recipe-event-inbox-digest`

1. You invoke the skill. It asks: "Which event or project should I triage?"
2. It runs `gws gmail +triage` to pull relevant threads from your inbox.
3. Event production logic classifies each thread by stakeholder type (vendor, client, sponsor, speaker, venue) and assigns a priority tier based on content signals — not just recency or sender.
4. The output is a structured digest with stale threads flagged, saved to a dated file.

---

## Example Session

```
> /recipe-event-inbox-digest

Which event or project should I triage? I'll use the name as a Gmail search query.

> Summit 2026

Time range? (default: 24h)

> 48h

Running: gws gmail +triage --query "Summit 2026" --max 50

---

# Event Inbox Digest — Summit 2026
Generated: 2026-03-23 09:14
Period: Last 48h
Threads: 3 Immediate · 5 Today · 8 Tracking · 2 Stale Flagged

## Tier 1 — Immediate Action Required

| Sender | Type | Subject | Action Needed | Deadline |
|--------|------|---------|---------------|----------|
| Grand Ballroom | Venue | Certificate of Insurance — URGENT | Forward COI from broker | 2026-03-24 |
| Sound Co. | Vendor | Load-in window Tuesday | Confirm 6am access | Today EOD |
| Sarah Chen | Client | Are we still confirmed for AV walkthrough? | Reply with confirmation | ASAP |

## Tier 2 — Action Today
...

## Stale Threads — No Reply 24h+

| Thread | Type | Age | Recommended Action |
|--------|------|-----|-------------------|
| RE: Rider compliance | Vendor | 36h | Send acknowledgment + ETA |
```

---

## Safety: GWS Permission Tiers

All `gws` commands are classified into 3 tiers. This is enforced automatically via `.claude/rules/gws-safety.md` and `.claude/settings.json`.

| Tier | Operations | Behavior |
|------|-----------|----------|
| **T1 READ** | `+triage`, `+read`, `+agenda`, `list`, `get`, `schema` | Auto-allowed. No confirmation needed. |
| **T2 WRITE** | `+create`, `+write`, `+append`, `+upload`, `+insert` | Shows what will be written. Asks for confirmation. |
| **T3 DANGEROUS** | `+send`, `+reply`, `+delete`, `+share`, `+permission` | `--dry-run` first, full preview, explicit confirmation required. |

Read operations run seamlessly. Write and dangerous operations always require your approval — no exceptions.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding skills, proposing new recipes, and reporting issues.

---

## License

[Apache-2.0](LICENSE)

---

<div align="center">

### Need custom event workflows?

We build tailored GWS skill packs for event companies.

**[Contact TalkValue](https://trytalkvalue.com)** | support@trytalkvalue.com

</div>

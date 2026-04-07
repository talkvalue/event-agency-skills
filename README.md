# Event Agency Skills

Event production runs on 47 email threads, 12 vendor deadlines, and one coordinator who remembers everything. We replaced the remembering part.

**Open-source AI skills for live event production** — inbox triage, vendor escalation, speaker wrangling, budget tracking, and post-event reporting. Built by [TalkValue](https://trytalkvalue.com?utm_source=github&utm_medium=skill_repo&utm_campaign=event_agency_skills), tested on real conferences, trade shows, and galas.

---

## Skills

| Category | What It Does | Key Skills |
|----------|-------------|------------|
| [**Inbox Digest**](skills/inbox-digest/) | Turn 50 unread event emails into a prioritized action list in 60 seconds | Stakeholder Classifier, Priority Triage, Action Extractor |
| [**Vendor Tracker**](skills/vendor-tracker/) | Catch vendor non-response before it becomes a production crisis | Status Dashboard, Phase-Aware Escalation, Follow-Up Drafter |
| [**Cold Outreach**](skills/cold-outreach/) | Role-specific prospecting that turns cold sponsors into confirmed partners | Prospect Researcher, Sequence Builder, Quality Checker |
| [**Speaker Management**](skills/speaker-management/) | Zero missing bios, headshots, or rider forms the week before your event | Materials Tracker, Deadline Enforcer, Bio Quality Gate |
| [**Budget Tracker**](skills/budget-tracker/) | Spot the $12K catering overrun before it hits the client invoice | Variance Analyzer, Invoice Aging, Category Thresholds |
| [**Post-Event Report**](skills/post-event-report/) | Honest performance reports that answer "did we hit the goal?" first | Session Ranker, Sponsor ROI, Channel Attribution |
| [**Registration Analytics**](skills/registration-analytics/) | Know which campaign actually drove tickets — not which got the most clicks | Multi-Touch Attribution, Segment Analysis, Attendance Benchmarks |

---

## Quick Start

Each skill has its own `SKILL.md` with detailed workflows. The general pattern:

```bash
# 1. Clone the repo
git clone https://github.com/talkvalue/event-agency-skills.git
cd event-agency-skills

# 2. Install dependencies
pip install -r requirements.txt

# 3. Connect your Google Workspace via Composio (one-time OAuth)
# Visit https://composio.dev and connect Gmail, Calendar, Sheets

# 4. Run a skill
python skills/inbox-digest/scripts/triage.py \
  --event "Summit 2026" --date 2026-05-15 --dry-run
```

---

## Usage with Claude Code

Every skill includes a `SKILL.md` file. Install as a plugin or drop individual skills into your project:

```bash
# As a plugin (all 7 skills)
claude plugin install talkvalue/event-agency-skills

# Or copy one skill
cp -r skills/inbox-digest/ your-project/.claude/skills/
```

Ask Claude *"Triage my event inbox and flag stale vendor threads"* — it classifies by stakeholder type, applies phase-aware urgency, and generates a prioritized digest.

---

## Why Event-Specific

Generic AI doesn't know that a venue COI revision at T-3 outranks a sponsor logo submission at T-21. These skills do, because they encode the production logic that event coordinators carry in their heads:

- **Inbox Digest** classifies emails by 6 stakeholder types and applies temporal overrides — a vendor email that's Tier 2 at T-30 automatically becomes Tier 1 at T-7 when the event is a week away
- **Vendor Tracker** has phase-aware urgency thresholds: 48h response window during planning, 12h during advance week, 2h on load-in day — and enforces "phone call, not email" on show day
- **Cold Outreach** builds role-specific angles for 5 prospect types (buyer/sponsor/speaker/vendor/media) with a quality checker that catches the 24 most common AI slop phrases across a 4-touch sequence
- **Budget Tracker** applies category-aware variance thresholds — Venue alerts at 5% because it's the largest line item, Marketing at 15% because it's the most flexible — then diagnoses *why* each variance occurred
- **Speaker Management** bans "thought leader," "passionate about," and 11 other fluff words — and enforces the rule that a 25-word emcee intro must be speakable out loud without stumbling

---

## When to Use What

| Event Phase | What's Happening | Skills to Run |
|-------------|-----------------|---------------|
| **T-90** Contracting | Sponsors cold, vendors unsigned | **Cold Outreach** → build prospect list, send sequences |
| **T-30** Planning | Vendors confirmed, speakers invited | **Speaker Management** → track materials, enforce deadlines |
| **T-14** Advance | Deliverables due, budgets tightening | **Vendor Tracker** → flag overdue, escalate. **Budget Tracker** → variance check |
| **T-7** Final Week | Everything accelerates | **Inbox Digest** → daily triage. **Vendor Tracker** → 12h thresholds |
| **T-1** Load-In | Phone calls, not emails | **Vendor Tracker** → 2h thresholds, phone-only escalation |
| **T+3** Post-Event | Debrief and report | **Post-Event Report** → honest assessment. **Registration Analytics** → attribution |

---

## Repository Structure

```
event-agency-skills/
├── README.md              ← You are here
├── lib/
│   ├── composio_client.py         # Composio v3 SDK wrapper
│   └── event_context.py           # Phase calculator, stakeholder classifier
├── skills/
│   ├── inbox-digest/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/
│   ├── vendor-tracker/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── cold-outreach/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── budget-tracker/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── speaker-management/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── post-event-report/
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── registration-analytics/
│       ├── SKILL.md
│       └── scripts/
├── .claude-plugin/        # Claude Code plugin config
├── .claude/rules/         # 3-tier safety enforcement
├── .mcp.json              # Composio MCP server config
├── CONTRIBUTING.md
└── requirements.txt
```

---

## Privacy & Safety

Every skill is built with data safety in mind:

- **3-tier safety model** enforces Read / Write / Dangerous classifications on all Composio tool operations
- **No send without preview** — email sends require dry-run first, explicit approval second
- **No bulk operations** without itemized preview — batch actions over 3 items show every item before executing
- **`--dry-run` on every script** — preview operations without making API calls

See [`.claude/rules/composio-safety.md`](.claude/rules/composio-safety.md) for the full safety spec.

---

## Contributing

Event industry expertise welcome. PRs welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for the skill template, quality bar, and PR process.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/better-triage`)
3. Follow the skill template in CONTRIBUTING.md
4. Open a Pull Request

---

## License

[Apache-2.0](LICENSE). Use these however you want.

---

*Star this repo if you run events. It helps other production teams find these tools.*

---

<div align="center">

**[Want these built and managed for your events? Book a call ->](https://trytalkvalue.com/book-a-call?utm_source=github&utm_medium=skill_repo&utm_campaign=event_agency_skills)**

*This is how we run event production at [TalkValue](https://trytalkvalue.com?utm_source=github&utm_medium=skill_repo&utm_campaign=event_agency_skills).*

[Event Intelligence Playbook](https://www.linkedin.com/newsletters/event-intelligence-playbook-7432120487045926912/?utm_source=github&utm_medium=skill_repo&utm_campaign=event_agency_skills) · our weekly newsletter on AI + events

</div>

# Event Agency Skills

**Your AI assistant doesn't know that a venue contract revision three days before load-in outranks a sponsor asset submission with a two-week buffer. These skills do.**

> Built by **[TalkValue](https://trytalkvalue.com)** — we run events with AI-native workflows and open-source what works.

---

## Quick Start

```bash
claude plugin marketplace add talkvalue/event-agency-skills
claude plugin install event-agency-skills
```

Then in any Claude Code session:

```
/inbox-digest
```

> Which event should I triage?

```
KGC 2026
```

> Running: gws gmail +triage --query "KGC 2026" --max 50
>
> **3 Immediate** -- Venue COI expired, AV load-in unconfirmed, client waiting on walkthrough confirmation
> **5 Today** -- Florist final count, speaker AV rider update, sponsor logo submission
> **2 Stale** -- Vendor rider compliance (36h no reply), dressing room logistics (48h)

---

## What This Is

7 skills that encode real event production knowledge -- stakeholder classification, vendor escalation logic, budget variance thresholds, speaker materials checklists, outreach cadence, and post-event analysis frameworks.

Each skill is **domain knowledge first, tools second.** They work as standalone expert guides. If you also use the [Google Workspace CLI](https://github.com/googleworkspace/cli), skills can read your Gmail, Sheets, Calendar, and Drive directly.

---

## Skills

| Skill | What It Does |
|-------|--------------|
| [`inbox-digest`](skills/inbox-digest/SKILL.md) | Classify event emails by stakeholder type and priority tier. Temporal overrides bump vendor emails to urgent as event date approaches. Flags stale threads with escalation paths. |
| [`cold-outreach`](skills/cold-outreach/SKILL.md) | Personalized prospecting for event buyers, sponsors, and speakers. Role-specific angles, 4-touch follow-up sequences (D1/D3/D7/D14), and quality checks against repeated phrases. |
| [`vendor-tracker`](skills/vendor-tracker/SKILL.md) | Track vendor deliverables and contracts with phase-aware urgency. Normal ops: 48h threshold. Advance week: 12h. Show day: phone call, not email. |
| [`speaker-management`](skills/speaker-management/SKILL.md) | Speaker materials collection and content quality. Bio format variants (25/50/100 word), deadline tracking (D-30 bio, D-14 slides), banned fluff words, learning outcome verb rules. |
| [`budget-tracker`](skills/budget-tracker/SKILL.md) | Budget vs actuals with category-aware thresholds. Venue 5% overage = alert. Marketing 15% = note. Invoice aging at 30/60/90 days with tone-matched follow-ups. |
| [`post-event-report`](skills/post-event-report/SKILL.md) | Post-event performance analysis. Registration vs attendance, session rankings, sponsor ROI for renewals, channel attribution. Honest about what didn't work. |
| [`registration-analytics`](skills/registration-analytics/SKILL.md) | Campaign-to-registration attribution with multiple models (last-touch, first-touch, multi-touch). Segment analysis by industry, role, geography. Benchmarks included. |

---

## See It Work

**Vendor tracking in advance week (T-5):**

```
Check vendor status for Summit 2026 — event is May 10
```

> **Phase: Advance Week (T-5)** -- urgency thresholds tightened
>
> OVERDUE (2):
> | Vendor | Type | Item | Days Over | Action |
> |--------|------|------|-----------|--------|
> | Sound Systems Inc | AV | Final equipment list | 3 days | Phone call to AM immediately |
> | Grand Hotel | Venue | COI confirmation | 4 days | Email + cc venue sales manager |
>
> BLOCKED -- Waiting on Us (1):
> | City Catering | F&B | Final headcount | Our team owes this by May 7 |

**Cold outreach for sponsors:**

```
Draft cold emails for this sponsor list — SommCon 2026, wine industry conference
```

> **Target: Napa Valley Vintners** -- Sponsor angle
> "40% of SommCon attendees are wine distributors actively sourcing new labels. A branded tasting lounge puts your portfolio in front of 200 procurement directors."
>
> Email 1 (Day 1): Personalized pitch with activation idea
> Email 2 (Day 3): New info -- early-bird sponsor deadline
> Email 3 (Day 7): Industry insight article, light event reference
> Email 4 (Day 14): Break-up -- removes pressure, highest reply rate

---

## Prerequisites

**Required:**
- [Claude Code](https://claude.ai/code) -- CLI, desktop app, or IDE extension

**Optional (for Gmail/Calendar/Drive/Sheets integration):**
```bash
brew install gws && gws auth login
```

Skills work without GWS. Domain knowledge is the core value. GWS adds live data access.

---

## Safety

Skills that use GWS commands follow a 3-tier safety model:

| Tier | Risk | What Happens |
|------|------|--------------|
| **T1 Read** | None | Runs automatically -- triage, agenda, list, get |
| **T2 Write** | Low | Shows preview, asks confirmation -- create, append, upload |
| **T3 Dangerous** | High | `--dry-run` first, full preview, explicit approval -- send, reply, delete |

Enforced via `.claude/rules/gws-safety.md`. No exceptions, even if you say "just do it."

---

## Contributing

We welcome event industry expertise. See [CONTRIBUTING.md](CONTRIBUTING.md) for the skill template, quality bar, and PR process.

---

## License

[Apache-2.0](LICENSE)

---

<div align="center">

**[TalkValue](https://trytalkvalue.com)** -- Event AI Consulting | support@trytalkvalue.com

</div>

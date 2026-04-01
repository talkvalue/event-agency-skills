---
name: registration-analytics
version: 1.0.0
description: "Registration funnel analysis, campaign attribution, and segment-level conversion reporting for events. Use when analyzing registration data, measuring campaign performance, comparing attendee segments, or building post-registration reports. Triggers: 'registration analytics', 'funnel analysis', 'campaign attribution', 'registration report', 'conversion analysis', 'attendee segments'."
---

# Registration Analytics

## Purpose

Turn raw registration data into decisions — which campaigns actually drove registrations, which segments converted, and where the funnel leaks.

Event teams drown in registration numbers but starve for insight. Knowing that 1,200 people registered tells you nothing. Knowing that 60% came from a single LinkedIn campaign, that C-suite registrants converted at 3x the rate of individual contributors, and that your third email in the sequence had zero incremental lift — that's what changes your next event's strategy.

This skill takes registration and campaign data, runs it through funnel analysis, attribution modeling, and segment comparison, then produces actionable recommendations — not just charts.

## When to Use

- After an event to analyze what drove registrations and attendance
- Mid-campaign to assess which channels are converting and where to shift budget
- When comparing registration performance across multiple events or editions
- When a stakeholder asks "what worked?" and needs more than vanity metrics
- Before planning the next event's marketing strategy based on historical data

## When NOT to Use

- **Not for marketing campaign creation.** This analyzes campaign results — it does not write emails, design ads, or plan marketing strategies.
- **Not for individual attendee lookup.** This produces segment-level analysis, not per-person data retrieval.
- **Not for real-time registration monitoring.** This is a periodic analysis tool for completed or ongoing campaigns, not a live dashboard.
- **Not for financial analysis.** For cost-per-registration ROI against budget, use budget-tracker. This skill focuses on conversion and attribution, not spend.

## Inputs

| Input | Required | Default | Notes |
|-------|----------|---------|-------|
| Registration data | Yes | --- | Registrant list with timestamps, source/UTM, ticket type. CSV, spreadsheet, or CRM export |
| Campaign data | Yes | --- | Email sends, ad spend, social posts with dates and metrics (opens, clicks, impressions) |
| Attendance data | No | --- | Check-in or badge scan data. Without this, analysis stops at registration (noted in output) |
| Event context | No | --- | Event type (paid/free), dates, ticket tiers, target audience. Improves benchmark comparisons |
| Historical data | No | --- | Prior edition registration data for year-over-year comparison |

## Quick Reference

### Event Funnel Stages

```
Awareness (impressions, reach)
  → Interest (clicks, page views)
    → Registration
      → Confirmation (payment / email confirm)
        → Attendance (badge scan / check-in)
          → Engagement (sessions, networking, app usage)
```

### Key Benchmarks

| Metric | Benchmark | Source |
|--------|-----------|--------|
| Email open rate (event) | 20-25% standard, 65.6% SommCon peak | Industry + SommCon data |
| Email click-through | 2-5% | Industry average |
| Registration-to-attendance (paid) | 60-70% (up to 70-80% for premium) | Industry average |
| Registration-to-attendance (free) | 30-40% | Industry average |
| Early bird registration share | 20-35% of total | Varies by event type |

### Attribution Models

| Model | What It Credits | Best For |
|-------|----------------|----------|
| Last-touch | Final campaign before registration | "What closed the deal?" |
| First-touch | First known interaction | "What started the relationship?" |
| Multi-touch (weighted) | Distributed credit across touchpoints | Full picture, but harder to action |

No model is perfect. Present all three when data supports it. Let the team decide which to weight for budget decisions.

## Workflow by Task

### Task 1: Data Ingestion & Validation

1. Load registration data. For each registrant, confirm these fields exist:
   - **Registration date/time** -- needed for timing analysis
   - **Source/channel** -- needed for attribution (UTM parameters, referral source, manual tag)
   - **Ticket type** -- needed for segment analysis (early bird, regular, late, VIP, comp)
   - **Contact details** -- name, email, company, role, industry (whatever is available)
2. Load campaign data. For each campaign/send, confirm:
   - **Send date** -- needed to match campaigns to registration spikes
   - **Channel** -- email, paid social, organic social, partner referral, direct
   - **Metrics** -- opens, clicks, impressions, spend (whatever is available)
3. If attendance data is provided, match registrants to check-ins by email or registration ID.
4. Flag data quality issues before proceeding:
   - Registrants with no source/UTM (report as "Direct/Unknown" -- do not discard)
   - Duplicate registrations (same email, different timestamps)
   - Campaign data gaps (sends with no open/click tracking)
5. Report data completeness: "X of Y registrants have source attribution. Z have attendance confirmation."

### Task 2: Funnel Analysis

1. Build the funnel stage by stage. For each transition, calculate:
   - **Volume**: How many entered this stage
   - **Conversion rate**: What percentage moved to the next stage
   - **Drop-off**: Where and how many were lost
2. Calculate overall funnel metrics:
   - **Awareness → Registration rate**: Of all people reached, what percentage registered
   - **Registration → Attendance rate**: Compare against benchmarks (paid 60-70%, free 30-40%)
   - **Time-to-registration**: Median days from first touch to registration
3. Identify the biggest funnel leak -- the stage with the largest absolute drop-off.
4. If attendance data is missing, note it explicitly: "Funnel analysis stops at Registration. Attendance data needed to complete the picture."
5. Break the funnel by ticket type -- early bird, regular, and late registrants often have very different attendance rates.

### Task 3: Campaign Attribution

1. **Last-touch attribution**: For each registrant with source data, credit the campaign/channel that was the final touchpoint before registration.
   - Match registration timestamps to the most recent campaign touchpoint (email click, ad click, page visit)
   - Group by channel and campaign to find top converters
2. **First-touch attribution**: Credit the earliest known touchpoint for each registrant.
   - This often differs significantly from last-touch -- surface the delta
3. **Multi-touch attribution** (if data supports it): Distribute credit across all touchpoints.
   - Use linear weighting (equal credit) as default unless the team specifies otherwise
   - Note which touchpoints consistently appear in converting paths vs. non-converting paths
4. For each channel, calculate:
   - **Registrations attributed** (by each model)
   - **Cost-per-registration** (if spend data available)
   - **Conversion rate** (clicks-to-registration, impressions-to-registration)
5. Present results side by side -- the differences between models are the insight.

### Task 4: Segment Comparison

Analyze registrations across these dimensions (use whichever the data supports):

1. **By industry/vertical**: Which industries registered at highest rates? Which are underrepresented vs. target audience?
2. **By role/seniority**: C-suite vs. director vs. manager vs. individual contributor. Did seniority affect conversion or attendance rate?
3. **By geography**: Regional breakdown. Any unexpected clusters or gaps?
4. **By registration source**: Organic vs. paid vs. partner referral vs. direct. Which source brought the highest-quality registrants (measured by attendance rate, not just volume)?
5. **By ticket type**: Early bird vs. regular vs. late vs. comp. What was the revenue mix? Which tier had the best attendance rate?
6. **By company size**: Enterprise vs. mid-market vs. SMB (if company data available)

For each segment:
- Report volume, conversion rate, and attendance rate (if available)
- Compare to overall averages -- flag segments that over- or under-perform by more than 20%
- Note segments with small sample sizes (n < 20) -- do not draw conclusions from them

### Task 5: Timing Analysis & Recommendations

**Timing Analysis:**
1. Plot registrations over time -- identify spikes and correlate with campaigns, deadlines, or announcements
2. Identify optimal send windows -- which days of week and times of day had the highest click-to-registration conversion
3. Assess sequence fatigue -- did later emails in a sequence show diminishing returns? At what point did unsubscribes spike?
4. Map the registration push timeline: 6 weeks out (early bird), 3 weeks (main push), 1 week (urgency), day-of (virtual events only)

**Recommendations:**
1. **Channel allocation**: Based on cost-per-registration and conversion data, recommend where to increase/decrease spend for the next event
2. **Segment targeting**: Which segments are underperforming? Should they be targeted differently or deprioritized?
3. **Timing optimization**: When should key campaigns deploy based on historical conversion windows?
4. **Funnel fixes**: For the biggest drop-off point, suggest 2-3 specific interventions
5. Frame every recommendation with the data behind it -- "We recommend X because the data shows Y." No unsupported opinions.

## Output Format

```
## Registration Analytics Report: [Event Name]
**Period:** [Start Date] — [End Date]
**Data Completeness:** [X/Y registrants with source attribution, Z with attendance data]

### Funnel Summary
| Stage | Volume | Conversion | Benchmark |
|-------|--------|-----------|-----------|
| Awareness | ... | ... | ... |
| Interest | ... | ...% → Registration | ... |
| Registration | ... | ...% → Attendance | Paid: 60-70%, Free: 30-40% |
| Attendance | ... | | |

**Biggest leak:** [Stage] — [X] drop-off ([Y]% of previous stage)

### Attribution Summary
| Channel | Last-Touch | First-Touch | Multi-Touch | Cost/Reg |
|---------|-----------|-------------|-------------|----------|
| Email | ... | ... | ... | ... |
| Paid Social | ... | ... | ... | ... |
| Organic | ... | ... | ... | ... |
| Partner | ... | ... | ... | ... |
| Direct/Unknown | ... | ... | ... | n/a |

### Top Segments
| Segment | Registrations | Conversion Rate | vs. Average |
|---------|--------------|-----------------|-------------|
| ... | ... | ... | +/-...% |

### Recommendations
1. [Recommendation with supporting data]
2. [Recommendation with supporting data]
3. [Recommendation with supporting data]
```

## Principles

1. **Attribution is imperfect -- present the range, not the number.** No attribution model captures reality perfectly. Show last-touch, first-touch, and multi-touch side by side. The spread between them is the honest answer. A channel that shows 40 registrations on last-touch and 120 on first-touch is telling you something different than one that shows 80 on both.

2. **Segment before aggregating.** Aggregate numbers hide the story. "45% registration-to-attendance rate" could mean 80% for paid and 20% for free. Always break down by the dimensions that matter before reporting a topline number.

3. **"What drove registrations" > "what felt busy."** A campaign that generated 10,000 impressions and 5 registrations is not a success. A targeted email to 200 people that converted 40 is. Measure what moved the needle, not what made noise.

4. **Registration is not attendance -- always report both.** A 2,000-registration event with 800 attendees is a different story than a 1,000-registration event with 900 attendees. Never report registration numbers without noting the attendance conversion, or explicitly flagging that attendance data is unavailable.

5. **Small samples deserve skepticism.** A segment with 8 registrants and a 100% attendance rate is not a finding -- it's noise. Flag small samples (n < 20) and avoid drawing conclusions from them.

6. **ALWAYS** present multiple attribution models (last-touch, first-touch, multi-touch) — no single model tells the full story.

7. **NEVER** report aggregate conversion rates without segment breakdown — the average hides the insight.

## What to Avoid

1. **Reporting aggregate numbers without segments.** "We had 1,500 registrations" is not analysis. Break it down by source, ticket type, role, and geography. The aggregates hide everything useful.

2. **Assuming email opens equal interest.** Open rates are unreliable (Apple Mail Privacy Protection inflates them, plain-text emails may not track). Use click-through as the engagement signal. Opens are directional at best, misleading at worst.

3. **Conflating registration with attendance.** These are fundamentally different metrics with different drivers. A campaign that drives registrations but not attendance is solving a different problem than one that drives attendance from already-registered contacts. Treat them separately.

4. **Single-channel attribution when reality is multi-touch.** Crediting the last email before registration ignores the LinkedIn ad that created awareness and the colleague recommendation that built trust. Always present multiple attribution models. If you can only run one, say so and note the limitation.

5. **Drawing conclusions from one event.** A single event is one data point. Note when recommendations are based on a single event vs. cross-event patterns. "This worked at SommCon" is a hypothesis, not a rule.

6. **MUST** report both registration AND attendance numbers — registration alone overstates event success.

## Examples

### Attribution Reporting

**BAD:**
"Email drove 120 registrations."

**GOOD:**
"Email was the last touch for 120 registrations (last-touch model). However, 67 of those registrants first encountered the event through LinkedIn ads (first-touch). Multi-touch weighted attribution: Email 45%, LinkedIn 30%, Organic 15%, Partner 10%."

### Segment Analysis

**BAD:**
"The overall registration-to-attendance rate was 68%."

**GOOD:**
"Overall show rate was 68%, but this masks a significant split: paid registrants showed at 82% while free/comp registrants showed at 41%. Early-bird registrants (6+ weeks out) had the highest show rate at 89%."

## Tool Integration

| Tool | Command Pattern | Purpose |
|------|----------------|---------|
| **Sheets -- read** | `gws sheets +read --spreadsheet {ID}` | Load registration data, campaign metrics, or attendance records from Google Sheets |
| **Sheets -- read range** | `gws sheets +read --spreadsheet {ID} --range "Sheet1!A1:Z"` | Read a specific tab or range when the spreadsheet has multiple data sets |

GWS integration is optional. This skill works with any data source -- CSV files, CRM exports, or manually provided data. Sheets read is the most common integration for teams using Google Workspace.

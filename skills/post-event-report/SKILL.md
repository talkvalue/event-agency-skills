---
name: post-event-report
version: 2.0.0
description: "Post-event performance reporting — analyze attendance, sessions, sponsor ROI, and channel attribution. Compares actuals to goals, diagnoses what worked and what didn't, and produces actionable recommendations. Triggers: 'post-event report', 'event report', 'how did the event go', 'event performance', 'post-event analysis', 'sponsor ROI', 'event debrief'."
tools: ["composio:GOOGLESHEETS_BATCH_GET", "composio:GOOGLEDOCS_CREATE_DOCUMENT"]
scripts: ["scripts/report_generator.py"]
---

# Post-Event Report

## Purpose

Turn event data into a report that answers two questions: did we hit our goals, and what do we do differently next time?

Post-event reports fail when they're either a victory lap or a data dump. A client doesn't need 40 rows of session data — they need to know whether the event delivered on its promise. An internal team doesn't need polished spin — they need honest diagnosis of what broke so they can fix it. A sponsor doesn't need impressions counts alone — they need to know whether their investment generated pipeline.

This skill takes whatever data you have — registration numbers, attendance, session metrics, feedback scores, sponsor deliverables, or even just your own observations — and produces a structured report tailored to the audience.

## When to Use

- Reviewing post-event data to assess performance against goals
- Preparing a client-facing or executive post-event report
- Analyzing session-level performance and engagement patterns
- Evaluating sponsor ROI for renewal conversations
- Mapping the attendee journey to identify friction and drop-off points
- Running an internal debrief or retrospective
- Planning improvements for a recurring event based on prior data

## When NOT to Use

- **Not for real-time event monitoring or day-of operations.** This is a post-event analysis tool. For live event tracking, use other operational workflows.
- **Not for marketing campaign creation.** This analyzes what happened — it does not create promotional content for future events.
- **Not for individual attendee lookup.** This produces aggregate analysis, not per-person reports. For individual registration questions, query the data directly.
- **Not for financial reconciliation.** This reports on ROI and performance metrics. For budget vs actuals and invoice management, use budget-tracker.

## Inputs

| Input | Required | Default | Notes |
|-------|----------|---------|-------|
| Event data | Yes | — | Registration counts, attendance, session metrics, feedback scores, NPS — whatever is available |
| Event goals / targets | No | Industry benchmarks | If goals were set pre-event, compare against them. If not, use benchmarks |
| Report audience | No | Client | Who reads this: client, internal team, executive leadership, board, sponsor |
| Session-level data | No | — | Attendance per session, fill rates, ratings, engagement metrics |
| Sponsor deliverables | No | — | Logo placements, booth traffic, lead scans, survey results |
| Channel / attribution data | No | — | How attendees heard about the event — registration source, UTM data, survey responses |
| Qualitative context | No | — | On-the-ground observations, notable moments, speaker feedback, things the data won't capture |

## Quick Reference

### Performance Tiers

- **Exceeded**: Actual beat goal by 10%+ across primary metrics
- **Met**: Within 10% of goals on primary metrics
- **Missed**: More than 10% below goal on one or more primary metrics
- **Mixed**: Hit some metrics, missed others — dig into the split and explain why

### KPIs by Event Type

- **Conference**: Registration rate, attendance rate (reg-to-show), session fill rates, NPS, sponsor satisfaction
- **Virtual**: Registration, attendance rate, average watch time, engagement rate (polls, Q&A, chat), replay views
- **Hybrid**: In-person + virtual metrics compared side-by-side, tech experience ratings, cross-audience engagement
- **Corporate / Internal**: Participation rate, pre/post knowledge scores (if measured), manager feedback, action completion rate
- **Fundraiser / Gala**: Attendance, dollars raised vs. goal, per-attendee giving, donor retention rate, new donor acquisition

### Channel Attribution Categories

- **Direct**: Typed URL, bookmarked, or direct navigation
- **Email campaign**: Newsletter, drip sequence, or invitation email
- **Social media**: LinkedIn, Instagram, X, Facebook — track by platform when possible
- **Partner referral**: Co-marketing, sponsor promotion, association cross-promotion
- **Organic / SEO**: Search engine traffic to event landing page
- **Word of mouth**: Reported in post-event survey or registration form "how did you hear about us"

Note: Attribution is inherently imperfect. Most attendees encounter multiple touchpoints before registering. Present the data honestly, acknowledge mixed sources, and avoid over-crediting any single channel.

## Workflow by Task

### Task 1: Post-Event Performance Analysis

1. Review all available data: registration vs. attendance, session-level metrics, feedback scores, NPS.
2. Compare actuals to stated goals. If no goals were set, compare to industry benchmarks for the event type.
3. Assign a performance tier: Exceeded, Met, Missed, or Mixed.
4. Identify what outperformed expectations and the likely reasons — be specific. "Keynote session hit 95% capacity because the speaker was announced 3 weeks before the event" is useful. "Good attendance" is not.
5. Identify what underperformed and the likely causes. "Workshop track averaged 40% fill rate — sessions were scheduled against the networking lunch" is actionable. "Some sessions had low turnout" is not.
6. Extract 3-5 actionable insights the team can implement for the next event.
7. Map channel attribution if source data is available — which channels drove registrations and at what cost.

### Task 2: Session Breakdown

1. Review session attendance, fill rates, and engagement data (if available).
2. Rank sessions by performance across available metrics.
3. Identify standout sessions — what worked: format, topic, speaker, time slot, or room placement.
4. Identify weak sessions — and the likely contributing factors (competing sessions, poor time slot, unclear description, niche topic).
5. Analyze format performance: did panels outperform workshops? Did morning sessions outperform afternoon?
6. Recommend session mix, format ratios, or scheduling changes for the next event.

### Task 3: Sponsor ROI Analysis

1. For each sponsor tier, compile deliverables against promised benefits:
   - **Impressions**: Logo views (signage, digital, email), booth traffic, session attendance for sponsored content
   - **Leads**: Badge scans, meeting requests, demo sign-ups, contact form submissions
   - **Satisfaction**: Sponsor survey scores, qualitative feedback, on-site experience
   - **Cost-per-lead**: Total sponsorship investment / qualified leads generated
   - **Renewal recommendation**: Based on ROI data plus relationship context, recommend renew / renegotiate / decline
2. Compare sponsor outcomes across tiers — did higher-tier sponsors get proportionally better results?
3. Identify which activations delivered the most value (branded sessions, lounges, networking events, digital placements).
4. Build a sponsor-facing summary for each sponsor suitable for renewal conversations.
5. Note: If sponsor data is incomplete, say so. A partial analysis with honest gaps is better than inflated numbers.

### Task 4: Executive Report Generation

1. Identify the audience: client, internal leadership, board, or sponsor.
2. Lead with the headline result — one sentence that answers "did we hit the goal?"
3. Build the report using the Output Format below. Adjust depth to audience:
   - **Client report**: Clean narrative, confident recommendations, relationship-forward tone
   - **Internal debrief**: Honest diagnosis, open questions, operational detail
   - **Executive summary**: Numbers-forward, concise, tied to organizational goals
   - **Sponsor report**: ROI-focused, activation performance, renewal framing
4. Map the attendee journey: Registration → Pre-event comms → Arrival → Participation → Exit.
   - Identify where the highest drop-off or friction occurred.
   - Flag moments that created strong positive impressions — and how to replicate them.
5. Include 3-5 specific, actionable recommendations. Each recommendation should answer: what to change, why, and expected impact.

## Output Format

```
## Event Performance Summary
[1-2 sentence headline: did we hit our goals? Performance tier.]

## What Worked
- [Item with specific evidence — metric, observation, or feedback]
- [Item with specific evidence]
- [Item with specific evidence]

## What Didn't Work
- [Item with honest assessment and likely cause]
- [Item with honest assessment and likely cause]

## Key Insights
- [Insight tied to a specific data point or observation]
- [Insight]
- [Insight]

## Recommendations for Next Event
1. [Specific, actionable change — not generic advice]
2. [Specific, actionable change]
3. [Specific, actionable change]

## Sponsor ROI Summary (if applicable)
| Sponsor | Tier | Impressions | Leads | CPL | Satisfaction | Recommendation |
|---------|------|-------------|-------|-----|-------------|----------------|
| [Name]  | Gold | [count]     | [count] | [$] | [score/5]  | Renew / Renegotiate / Decline |

## Attendee Journey
- Registration: [conversion rate, source mix]
- Pre-event comms: [open rates, click-through, engagement]
- Arrival: [check-in experience, no-show rate]
- Participation: [session fill rates, engagement metrics]
- Exit: [survey completion, NPS, immediate feedback]
- Drop-off point: [where and likely why]
```

For client-facing reports, add:

```
## Thank You + Forward Look
[1-2 sentences acknowledging the partnership and pointing to the next opportunity]
```

## Principles

1. **Honest over polished.** A report that only shows wins helps no one plan a better next event. Name what didn't work — with enough specificity that it's useful, and enough care that it's not embarrassing. The goal is improvement, not blame.

2. **Data supports the story — it doesn't replace it.** Numbers without context are noise. Every metric should be paired with: compared to what? What likely caused it? What does it mean for next time? A 70% attendance rate means nothing until you know the benchmark was 65% or 85%.

3. **The recommendation is the deliverable.** Performance data without recommendations is a history lesson. The report is only finished when there's a clear answer to: "so what do we do differently?" Every recommendation must be specific and actionable — something the team can actually implement.

4. **Match the depth to the audience.** A client report needs a clear narrative and confident recommendations. An internal debrief needs honest diagnosis and open questions. An executive summary needs numbers tied to organizational goals. Know which one you're writing before you start.

5. **Attribution is directional, not definitive.** No attribution model perfectly captures how someone decided to attend an event. Present channel data as directional insight, not gospel truth. "Email drove approximately 40% of registrations" is honest. "Email drove exactly 847 registrations" implies false precision.

6. **ALWAYS** answer "did we hit the goal?" in the first two sentences of the report.

7. **NEVER** present metrics without context — every number needs: compared to what, why it happened, what it means.

## What to Avoid

1. **Reports that only highlight wins.** The fastest way to lose credibility is a report that reads like a press release. Honest assessment of what didn't work is what drives improvement — and what makes clients trust you with the next event.

2. **Leading with data tables before stating the headline result.** Always answer "did we hit the goal?" first. The reader should know the verdict in the first two sentences. Supporting data comes after.

3. **Metrics without context.** "We had 1,200 attendees" is not an insight. "We had 1,200 attendees against a goal of 1,000, driven primarily by a late push from the email campaign in week 3" is useful. Every number needs: compared to what, why it happened, what it means.

4. **Generic recommendations.** "Improve attendee experience" is not a recommendation. "Move the networking lunch to a larger room and extend it by 30 minutes — the current space hit capacity by 12:15 and attendees reported feeling rushed" is a recommendation.

5. **Inflating sponsor ROI.** Sponsors will see through padded numbers. If a sponsor's booth had low traffic, say so — and recommend a better placement or activation for next time. Honesty in sponsor reporting builds multi-year partnerships. Spin builds one-year deals.

6. **Treating ROI as purely financial.** Name the pipeline value, community impact, and brand visibility even when they're hard to quantify. "The event generated $50K in direct revenue and influenced $200K in pipeline" is more complete than "$50K revenue."

7. **MUST** include honest assessment of what didn't work — wins-only reports help no one plan a better next event.

## Examples

### Recommendation

- **BAD:** "Consider improving the attendee experience for next year."
- **GOOD:** "Move the networking lunch from 45 to 60 minutes — the 2pm session had 31% lower attendance, suggesting attendees were still in hallway conversations. Survey comments confirm: 'not enough networking time.'"

### Metric reporting

- **BAD:** "We had 205 attendees."
- **GOOD:** "205 attended out of 287 registered (71.4% show rate). This exceeds the industry average of 65% for paid conferences and is up from 68% last year — likely driven by the new pre-event email sequence that started 6 weeks out instead of 3."

## Tool Integration

### Composio Tools (Primary)

| Tool | Action | Purpose | Safety Tier |
|------|--------|---------|-------------|
| **Sheets — read** | `GOOGLESHEETS_BATCH_GET` | Pull registration, attendance, or survey data | T1 Read |
| **Docs — create** | `GOOGLEDOCS_CREATE_DOCUMENT` | Generate report as a Google Doc for team review | T2 Write |

### Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| **report_generator.py** | `python skills/post-event-report/scripts/report_generator.py --event "..." --date YYYY-MM-DD --registration-sheet ID` | Generate structured post-event performance report with session rankings and sponsor ROI |

Note: Composio integration is optional. This skill works with whatever data the user provides — pasted into the conversation, uploaded as a file, or described verbally. Sheets and Docs are available when the user wants to pull data directly or output the report to a shared document.

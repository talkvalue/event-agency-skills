---
name: budget-tracker
version: 1.0.0
description: "Event budget tracking — variance analysis, invoice aging, and payment follow-up for live event production. Use when reviewing event budgets, tracking spend vs. estimates, monitoring vendor invoices, or drafting payment follow-up messages. Triggers: 'budget', 'variance', 'invoice aging', 'overdue invoice', 'budget tracker', 'event budget', 'spend vs estimate', 'payment follow-up'."
---

# Budget Tracker

## Purpose

Turn event budget data into cash flow clarity and action. Events hemorrhage money in the gap between "we estimated $X" and "we actually spent $Y" — and most teams don't discover the gap until it's too late to adjust.

This skill takes your budget spreadsheet, invoice data, or verbal summary and produces an honest picture of where the money is, where it's going, and what needs attention right now. It covers both sides: spend tracking (are we on budget?) and receivables (have vendors and sponsors actually paid?).

## When to Use

- Building or reviewing an event budget before production begins
- Comparing estimated vs. actual spend during or after an event
- Reviewing outstanding vendor invoices and payment timelines
- Identifying budget lines trending over and deciding where to cut
- Drafting payment follow-up messages to clients or sponsors
- Preparing a financial summary for a post-event debrief

## When NOT to Use

- **Not for contract negotiation or procurement.** This skill analyzes budget data and flags variances — it does not negotiate vendor pricing or select vendors.
- **Not for payroll or HR expense management.** Event budgets cover production costs, not team compensation.
- **Not for tax preparation or compliance.** This produces operational budget reports, not financial statements for accounting or audit purposes.
- **Not for real-time expense approval.** This is a periodic analysis tool, not a purchase order approval workflow.

## Inputs

| Input | Required | Default | Notes |
|-------|----------|---------|-------|
| Budget data | Yes | — | Spreadsheet, Sheets link, or verbal summary of estimated vs. actual spend |
| Event context | Yes | — | Event name, dates, scale (attendee count), venue type |
| Invoice data | No | — | Outstanding invoices with amounts, ages, and vendor/client names |
| Payment history | No | — | Past payment behavior for key accounts — helps set follow-up tone |
| Event timeline position | No | — | Pre-event / during / post-event — affects which thresholds apply |

## Quick Reference

### Event Budget Categories

| Category | Typical Line Items |
|----------|--------------------|
| Venue | Rental, F&B minimum, AV in-house surcharge |
| Production | AV vendor, staging, lighting, signage |
| Catering | Per-head cost, bar package, service charge, gratuity |
| Marketing | Print collateral, digital ads, social media, PR |
| Travel | Speaker travel, team travel, ground transport |
| Speakers | Honoraria, green room, speaker gifts |
| Staffing | Registration desk, security, ushers |
| Decor | Florals, linens, furniture rental |
| Contingency | Standard 10-15% of total budget |

### Variance Alert Thresholds

| Category | Alert At | Why |
|----------|----------|-----|
| Venue | 5% over | Largest single line item — small % = big dollars |
| Catering | 10% over | Per-head counts fluctuate; some variance is normal |
| Marketing | 15% over | Most flexible category; note but don't panic |
| Contingency | 0% drawn | Should not be touched before T-14 days to event |
| All others | 10% over | Default threshold for flagging |

### Invoice Aging Buckets

| Age | Status | Action |
|-----|--------|--------|
| Current | Within terms | No action needed |
| 1-30 days overdue | Nudge | Friendly reminder — assume oversight |
| 31-60 days overdue | Firm request | Direct ask with specific date and amount |
| 60+ days overdue | Escalation | Escalate to account lead; consider late fee or hold |

### Payment Risk Signals

| Signal | Level | Meaning |
|--------|-------|---------|
| First late payment | Incident | Note it, send a nudge, don't overreact |
| Second late payment | Pattern | Flag the account, shorten terms on next invoice |
| Third late payment | Risk | Requires proactive management — deposit requirements, payment plans |

## Workflow by Task

### Task 1: Budget Overview

1. Receive budget data — spreadsheet, Sheets link, or verbal summary.
2. Organize into the standard event budget categories (see Quick Reference).
3. For each category, list: estimated amount, actual spend to date, remaining balance.
4. Calculate total budget, total spent, total remaining, and overall % consumed.
5. Flag any category where actual spend exceeds the estimate.
6. If pre-event: project final spend based on current run rate and known upcoming costs.
7. Present the budget summary dashboard (see Output Format).

### Task 2: Variance Analysis

1. For each budget category, calculate: variance amount (actual - estimated) and variance % ((actual - estimated) / estimated).
2. Apply the category-specific alert thresholds (see Quick Reference).
3. For every variance that triggers an alert:
   - Name the category and the dollar amount over/under.
   - Diagnose the likely cause: scope change, vendor price increase, underestimate, late addition, weather/force majeure.
   - Recommend a specific corrective action: renegotiate, cut from another line, draw contingency (only if T-14 or closer).
4. Rank variances by dollar impact, not percentage — a 20% variance on a $500 line matters less than a 6% variance on a $50,000 line.
5. If contingency has been drawn: flag it prominently and state what triggered the draw.

### Task 3: Invoice Aging Review

1. Receive invoice data — outstanding invoices with amounts, ages, and account names.
2. Sort into aging buckets: Current, 1-30 days, 31-60 days, 60+ days.
3. For each overdue invoice, assess payment risk level based on:
   - How many times this account has been late (incident / pattern / risk).
   - Relationship length — a long-term partner gets more grace than a new vendor.
   - Invoice amount relative to total receivables — prioritize large outstanding amounts.
4. Calculate total outstanding by aging bucket.
5. Identify which invoices, if collected, would most improve near-term cash position.
6. Flag any cash flow gaps: periods where outgoing expenses are due before expected incoming payments.
7. Remember: revenue on paper is not cash in the door. Prioritize actual payments over booked revenue.

### Task 4: Follow-Up Draft Generation

1. For each overdue invoice requiring follow-up, determine the appropriate tone:
   - **1-30 days, first occurrence**: Warm nudge. "Just a quick note — invoice #X for $Y was due on [date]. Wanted to make sure it didn't slip through the cracks."
   - **1-30 days, repeat occurrence**: Polite but direct. "Following up on invoice #X. This is the second time payment has extended past terms — can we get this resolved this week?"
   - **31-60 days**: Firm request. State the amount, the original due date, and request a specific payment date. No apology for asking.
   - **60+ days**: Escalation. Reference prior attempts, state the total outstanding, and name the next step if unresolved (late fee, hold on future work, account review).
2. Match tone to relationship length:
   - 3+ year client with first late payment: warm, assume good faith.
   - New client with a pattern: firm, protect your position.
3. Each follow-up message should include: invoice number, amount, original due date, and a clear ask (specific payment date or next step).
4. Set a follow-up cadence: when to send each message and what changes if there is no response.

## Output Format

### Budget Summary Dashboard

```
**Event:** [Event Name]
**Date:** [Event Date]
**Total Budget:** $[amount]  |  **Spent:** $[amount] ([%])  |  **Remaining:** $[amount]

⚠ [Number] categories flagged for variance alerts
```

**Budget by Category**

| Category | Estimated | Actual | Variance | Var % | Status |
|----------|-----------|--------|----------|-------|--------|
| Venue | $X | $X | +/- $X | X% | OK / Alert / Over |
| Production | $X | $X | +/- $X | X% | OK / Alert / Over |
| Catering | $X | $X | +/- $X | X% | OK / Alert / Over |
| Marketing | $X | $X | +/- $X | X% | OK / Alert / Over |
| Travel | $X | $X | +/- $X | X% | OK / Alert / Over |
| Speakers | $X | $X | +/- $X | X% | OK / Alert / Over |
| Staffing | $X | $X | +/- $X | X% | OK / Alert / Over |
| Decor | $X | $X | +/- $X | X% | OK / Alert / Over |
| Contingency | $X | $X | +/- $X | X% | OK / Drawn |

**Invoice Aging**

| Account | Invoice # | Amount | Age | Risk | Recommended Action |
|---------|-----------|--------|-----|------|--------------------|
| [Name] | [#] | $[X] | [days] | Low/Med/High | [Action] |

**Action Items**
1. [Specific action — what, who, by when]
2. [Specific action]
3. [Specific action]

## Principles

1. **Revenue on paper is not cash in the door.** Every recommendation should prioritize actual cash received, not booked revenue or signed contracts. A $50K sponsorship means nothing if the invoice is 60 days overdue.

2. **Rank by dollars, not percentages.** A 6% overage on Venue ($3,000 on a $50K line) matters more than a 25% overage on speaker gifts ($250 on a $1,000 line). Always sort variances by dollar impact first.

3. **Tone matches the relationship.** A first late invoice from a 3-year client gets a warm nudge. A third late invoice from a new client gets a firm request. The relationship context changes everything — never apply the same follow-up template to every account.

4. **Flag patterns early.** One late payment is an incident. Two is a pattern. Three is a risk. Don't wait until 60+ days overdue to escalate — flag at two late payments, not three.

5. **Contingency is not a slush fund.** The 10-15% contingency exists for genuine surprises, not for scope creep or poor estimates. **NEVER** draw contingency budget before T-14 without explicit approval.

6. **Don't bury the lead.** **ALWAYS** lead with the cash flow headline — if there's a gap in 14 days, say it first. Not buried in a table on page three.

## What to Avoid

1. **Presenting data tables without a headline.** If there is a budget problem, name it before showing the numbers. "Catering is $12K over due to a 15% jump in per-head cost" — then show the table.

2. **Applying the same follow-up tone to every overdue account.** A warm nudge to a chronically late new client is weak. A stern warning to a loyal long-term partner is damaging. Match tone to context.

3. **Treating booked revenue as available cash.** Sponsorship commitments, pending invoices, and verbal confirmations are not money you can spend. Base cash flow recommendations on what has actually been received.

4. **Ignoring small variances that compound.** Five categories each 8% over budget adds up to a significant total overage. Review cumulative impact, not just individual lines.

5. **Drawing contingency for predictable costs.** If catering always runs 10% over the estimate, that is not a contingency draw — that is a bad estimate. Fix the estimate for next time.

6. **Producing a variance report without diagnosing causes.** **MUST** diagnose the likely cause of every variance, not just report the number. "Venue is 7% over" is an observation. "Venue is 7% over because the client added a second breakout room at T-21" is useful. Always explain why.

## Examples

### Variance Diagnosis

**BAD:** "Venue is 7% over budget."

**GOOD:** "Venue is 7% over budget ($4,200 overage) — driven by the client adding a second breakout room after contract signing. This was a scope change, not a cost overrun."

### Follow-Up Tone

**BAD:** "Your invoice is overdue. Please remit payment immediately."

**GOOD:** "Quick note — Invoice #4821 ($8,500, due March 15) is now 12 days past terms. Can your AP team confirm it's in queue? Happy to resend if needed."

## Tool Integration

| Tool | Command Pattern | Purpose |
|------|----------------|---------|
| **Sheets — read** | `gws sheets +read --spreadsheet {ID}` | Load budget tracker or invoice data from Google Sheets |
| **Sheets — append** | `gws sheets +append --spreadsheet {ID} --range {range} --values {data}` | Log new actuals or invoice status updates (T2) |
| **Drive — list** | `gws drive +list --query "name contains 'budget'" --supportsAllDrives` | Find budget files across personal and shared drives |
| **Gmail — draft** | `gws gmail +send --to {email} --subject {subj} --body {body} --draft` | Save payment follow-up as draft for review (T2) |
| **Gmail — send** | `gws gmail +send --to {email} --subject {subj} --body {body}` | Send follow-up after user approval (T3 — requires --dry-run first) |

## GWS Gotchas

### Sheets Append-Only Pattern
When updating budget actuals in Sheets, prefer `+append` to add new rows rather than overwriting existing data. This preserves the audit trail — you can always see what changed and when. If you must update a cell in place, confirm with the user first (T2 operation).

### Shared Drive Access
Budget files are often stored on Shared Drives. Always include `--supportsAllDrives` in Drive commands, or files on shared drives will silently not appear in results.

### Follow-Up Email Safety
Payment follow-ups are T3 operations — always `--dry-run` first:
```bash
gws gmail +send --to vendor@company.com --subject "Invoice #1234 — Payment Follow-Up" --body "..." --dry-run
# Review preview, confirm recipient and tone with user, then:
gws gmail +send --to vendor@company.com --subject "Invoice #1234 — Payment Follow-Up" --body "..."
```

### Currency and Number Formatting
When reading budget data from Sheets, amounts may come through as raw numbers without currency formatting. Always confirm the currency (USD, KRW, EUR) with the user before presenting financial summaries. Do not assume USD.

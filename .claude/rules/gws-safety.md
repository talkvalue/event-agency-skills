# GWS Safety Rules (Always Active)

All GWS CLI operations are classified into 3 tiers. These rules are non-negotiable.

## Tier 1 — READ (Auto-allowed)

Execute freely. No confirmation needed.

**Commands:** `list`, `get`, `+read`, `+triage`, `+agenda`, `schema`, `auth status`

These only retrieve data. They never modify anything in the user's Google Workspace.

## Tier 2 — WRITE (Confirm before executing)

Always confirm with the user before executing. Show what will be written.

**Commands:** `+create`, `+write`, `+append`, `+upload`, `+insert`, `+update`

**Workflow:**
1. Show the user exactly what will be created/written/uploaded
2. Ask: "Proceed with this action?"
3. Execute only after explicit "yes"

## Tier 3 — DANGEROUS (Dry-run mandatory)

MUST run `--dry-run` first, show full preview, get explicit confirmation.

**Commands:** `+send`, `+reply`, `+reply-all`, `+forward`, `+delete`, `+share`, `+permission`

**Workflow:**
1. Run the command with `--dry-run` appended
2. Show the dry-run output to the user in full
3. Ask: "This will [send an email / delete a file / change permissions]. Execute?"
4. Only execute the real command after explicit user confirmation
5. If user says no, do NOT retry or ask again — move on

## Never Do

- Never send email without showing --dry-run preview first
- Never delete files/emails without listing what will be deleted
- Never change sharing permissions without confirming exact scope
- Never bulk-operate (more than 3 items) without itemized preview
- Never bypass these tiers even if the user says "just do it" — always show the preview for Tier 3
- Never run Tier 3 commands in background agents or automated loops

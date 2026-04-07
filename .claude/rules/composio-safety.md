# Composio Safety Rules (Always Active)

All Composio tool operations are classified into 3 tiers. These rules are non-negotiable.

## Tier 1 — READ (Auto-allowed)

Execute freely. No confirmation needed.

**Actions:**
- `GMAIL_FETCH_EMAILS`, `GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID`, `GMAIL_FETCH_MESSAGE_BY_THREAD_ID`, `GMAIL_LIST_LABELS`, `GMAIL_LIST_THREADS`
- `GOOGLECALENDAR_EVENTS_LIST`, `GOOGLECALENDAR_GET_CALENDAR`
- `GOOGLESHEETS_BATCH_GET`, `GOOGLESHEETS_GET_SPREADSHEET_DATA`
- `GOOGLEDRIVE_LIST_FILES`, `GOOGLEDRIVE_FIND_FILE`
- `GOOGLEDOCS_GET_DOCUMENT`
- `HUBSPOT_SEARCH_CONTACTS_BY_CRITERIA`, `HUBSPOT_GET_CONTACT`, `HUBSPOT_GET_DEAL`
- `MAILCHIMP_LIST_AUDIENCES`, `MAILCHIMP_GET_CAMPAIGN`
- Any Python script with `--dry-run` flag

These only retrieve data. They never modify anything.

## Tier 2 — WRITE (Confirm before executing)

Always confirm with the user before executing. Show what will be written.

**Actions:**
- `GMAIL_CREATE_EMAIL_DRAFT`
- `GOOGLECALENDAR_CREATE_EVENT`, `GOOGLECALENDAR_UPDATE_EVENT`
- `GOOGLESHEETS_BATCH_UPDATE`, row append operations
- `GOOGLEDRIVE_UPLOAD_FILE`, `GOOGLEDRIVE_CREATE_FOLDER`
- `GOOGLEDOCS_CREATE_DOCUMENT`, `GOOGLEDOCS_UPDATE_DOCUMENT`
- `HUBSPOT_CREATE_CONTACT`, `HUBSPOT_CREATE_DEAL`, `HUBSPOT_UPDATE_*`
- `MAILCHIMP_ADD_CONTACT_TO_AUDIENCE`
- Any Python script that creates/modifies data

**Workflow:**
1. Show the user exactly what will be created/written/uploaded
2. Ask: "Proceed with this action?"
3. Execute only after explicit "yes"

## Tier 3 — DANGEROUS (Dry-run mandatory)

MUST preview first, show full output, get explicit confirmation.

**Actions:**
- `GMAIL_SEND_DRAFT`, `GMAIL_SEND_EMAIL`, `GMAIL_REPLY_TO_THREAD`
- `GMAIL_DELETE_MESSAGE`, `GMAIL_BATCH_MODIFY_MESSAGES`
- `GOOGLECALENDAR_DELETE_EVENT`
- `GOOGLEDRIVE_DELETE_FILE`
- `HUBSPOT_DELETE_CONTACT`, `HUBSPOT_DELETE_DEAL`
- `MAILCHIMP_SEND_CAMPAIGN`, `MAILCHIMP_DELETE_*`
- Any Python script with `--send` or `--execute` flags

**Workflow:**
1. For Python scripts, run with `--dry-run` first
2. For Composio actions, show the exact parameters that will be sent
3. Ask: "This will [send an email / delete a record / send a campaign]. Execute?"
4. Only execute after explicit user confirmation
5. If user says no, do NOT retry — move on

## Never Do

- Never send email without showing a preview first
- Never delete records without listing what will be deleted
- Never send Mailchimp campaigns without draft review
- Never bulk-operate (more than 3 items) without itemized preview
- Never bypass these tiers even if the user says "just do it"
- Never run Tier 3 actions in background agents or automated loops

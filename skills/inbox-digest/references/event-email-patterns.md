# Event Email Classification Patterns

Use these patterns to classify incoming emails by stakeholder type. Apply domain, title, and keyword signals together — a single match is suggestive; two or more is a confident classification.

---

## Vendor Patterns

Vendors are external service providers contracted to deliver specific goods or services.

### Known AV / Technical Production Vendors

| Company | Domain signals |
|---------|---------------|
| PRG | `@prg.com` |
| PSAV (now Encore) | `@psav.com`, `@encoreglobal.com` |
| Encore | `@encoreglobal.com`, `@encore.com` |

### Vendor Category Keywords

| Category | Keyword signals |
|----------|----------------|
| AV / Technical | "rigging", "lighting plot", "audio rack", "video wall", "gear list", "tech advance", "AV quote" |
| Catering / F&B | "BEO", "banquet event order", "menu proposal", "F&B minimum", "catering captain", "staffing ratio", "dietary", "bar package" |
| Security | "security detail", "badge check", "credentialing", "wristband order", "access control", "guard schedule" |
| Decor / Floral | "floral proposal", "linen order", "centerpiece", "decor install", "breakdown crew", "rental inventory" |
| Transport / Logistics | "shuttle manifest", "vehicle count", "load schedule", "freight quote", "customs clearance", "ground transport" |
| Signage / Print | "print-ready files", "bleed", "banner specs", "wayfinding", "proof approval", "production timeline" |
| Staffing Agencies | "temp staff", "event staff", "brand ambassador", "registration staff", "floor staff", "staffing confirmation" |

### Vendor Sender Title / Role Signals

- "Account Manager", "Account Executive" at vendor domain
- "Project Coordinator", "Event Coordinator" at vendor domain
- "Site Operations", "Site Ops", "Operations Manager"
- "Delivery Confirmation", "Shipping Notification"
- "Invoice", "Statement", "Payment Due", "Net 30", "PO Required"

---

## Client / Stakeholder Patterns

Clients are the paying sponsor or host organization. Stakeholders include internal approvers on the client side.

### Domain Signals

- Corporate domain (not a personal Gmail/Yahoo address)
- Domain matches the event's organizer or contracting company
- Fortune 500 / known enterprise domain

### Title / Role Signals

- C-Suite: "CEO", "CFO", "COO", "CTO", "CMO", "President"
- VP / Director tier: "VP of", "Vice President", "Director of"
- Event owner titles: "Head of Events", "Event Director", "Corporate Events Manager", "Brand Experience Lead"

### Subject Line Signals

| Pattern | Meaning |
|---------|---------|
| "RE: Proposal" | Active proposal review |
| "RE: Contract" | Contract negotiation or signature |
| "Budget Approval" | Finance stakeholder in loop |
| "FW: Invoice" | Client forwarding financials internally |
| "Event Brief" | Kick-off or scope document attached |
| "Debrief" | Post-event feedback incoming |

---

## Sponsor Patterns

Sponsors provide funding or value-in-kind in exchange for brand presence at the event.

### Keyword Signals

| Signal | Context |
|--------|---------|
| "sponsorship" | General sponsor inquiry or agreement |
| "activation" | Brand activation or experiential element |
| "booth" | Expo/trade show floor presence |
| "branding opportunity" | Seeking logo or naming rights placement |
| "logo placement" | Artwork and brand guideline exchange |
| "sponsor deck" | Prospectus or tiered package document |
| "sponsor invoice" | Payment for sponsorship tier |
| "naming rights" | High-value sponsorship tier |
| "co-marketing" | Joint promotional arrangement |

### Sender Title Signals

- "Sponsorship Manager", "Partnership Manager"
- "Brand Manager", "Marketing Manager", "Marketing Director"
- "Community Relations", "Corporate Affairs"
- Agency acting on behalf of sponsor brand

---

## Speaker / Talent Patterns

Speakers, performers, emcees, and entertainers — often routed through bureaus or agents.

### Domain Signals

| Bureau / Agency | Domain signal |
|----------------|--------------|
| Keppler Speakers | `@kepplerspeakers.com` |
| Washington Speakers Bureau | `@washingtonspeakers.com` |
| CAA Speakers | `@caa.com` |
| Harry Walker Agency | `@harrywalker.com` |
| Premiere Speakers Bureau | `@premierespeakers.com` |
| WME | `@wmeagency.com` |
| Generic talent agency | "agency", "bureau", "representation", "booking" in domain or signature |

### Keyword Signals

| Signal | Context |
|--------|---------|
| "rider" | Technical or hospitality rider attached |
| "AV requirements" | Speaker's technical spec sheet |
| "session" | Session title/abstract/timing |
| "keynote" | Keynote slot confirmation or prep |
| "panel" | Panel logistics or moderator brief |
| "green room" | Backstage / speaker hospitality |
| "honorarium" | Speaker fee or payment |
| "bio and headshot" | Speaker collateral for marketing |
| "run of show" | Talent needs ROS for rehearsal |
| "travel itinerary" | Speaker travel being coordinated |

---

## Venue Patterns

Venue emails come from the property's event services, catering, operations, or sales teams.

### Domain Signals

- Convention center domains (e.g., `@javitscenter.com`, `@mccormickplace.com`)
- Hotel chains: `@marriott.com`, `@hilton.com`, `@hyatt.com`, `@mgmresorts.com`, `@caesars.com`
- Venue name appearing in sender's email or signature
- "@venue" present in sender domain or display name

### Keyword Signals

| Signal | Context |
|--------|---------|
| "dock" / "loading dock" | Load-in coordination |
| "load-in" / "load-out" | Move-in/move-out schedule |
| "curfew" | Hard-out or noise ordinance |
| "COI" / "Certificate of Insurance" | Vendor insurance requirement |
| "floor plan" / "CAD" | Space layout and capacity |
| "rigging" | Ceiling attachment approval |
| "catering minimum" | F&B spend commitment |
| "in-house AV" | Venue's preferred AV vendor |
| "exclusive vendor" | Required contractor list |
| "venue coordinator" | Primary venue contact |
| "event order" | Final venue BEO or EO document |
| "fire marshal" | Capacity or safety review |
| "egress" | Emergency exit compliance |

---

## Internal Patterns

Emails from within the agency or client organization that are operational, not action-requiring.

### Domain Signals

- Own agency domain
- Client's internal domain (already captured as Client type above; flag as internal if forwarded internally)
- Team aliases: `events@`, `production@`, `ops@`, `allhands@`

### Sender / Subject Signals

| Signal | Context |
|--------|---------|
| "internal" in subject | Flagged as non-external |
| Project management tool notifications | Asana, Monday.com, Basecamp, Notion automated sends |
| "Do Not Reply" sender | Automated platform notification |
| "Digest" / "Weekly Update" | Internal newsletter or status roll-up |
| Slack email notification | `@slack.com` sender |
| Google Calendar invite | `@calendar.google.com` sender |

---

## Classification Confidence Scoring

When multiple signals match, increase classification confidence:

| Matches | Confidence |
|---------|-----------|
| 1 signal | Low — flag for review |
| 2 signals | Medium — classify, mark as inferred |
| 3+ signals | High — classify with confidence |

When signals conflict (e.g., vendor domain + VP title), defer to the **sender's domain** as the primary classifier, and note the anomaly in the digest for human review.

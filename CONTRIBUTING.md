# Contributing Event Skills

Welcome to event-agency-skills. Event industry expertise is valued here — your skills, workflows, and domain knowledge directly improve the toolkit for production teams.

## Overview

This repository hosts reusable Claude skills for event professionals. Each skill encodes domain knowledge for a specific event workflow — inbox triage, vendor tracking, budget reconciliation, speaker management, outreach, and analytics. Skills may integrate with Google Workspace tools (Gmail, Calendar, Docs, Sheets, Drive) but GWS integration is optional — domain knowledge is the core value.

---

## Adding a Skill

### Structure

```
skills/{skill-name}/
├── SKILL.md              # Skill definition (required)
├── references/           # Optional reference files
│   ├── decision-tree.md
│   └── patterns.md
└── examples/             # Optional example outputs
```

### SKILL.md Template

Create `skills/{skill-name}/SKILL.md`:

```yaml
---
name: your-skill-name
version: 1.0.0
description: "What it does. Use when [context]. Triggers: 'keyword1', 'keyword2'."
---

# Your Skill Name

## Purpose
Concise statement of the problem this skill solves. Why does this workflow matter in event production?

## When to Use
Bulleted scenarios where this skill saves time or prevents mistakes. "Use when..." — be specific to event context.

## Inputs
Table listing required and optional inputs with defaults and validation notes.

## Workflow by Task
Numbered tasks with step-by-step instructions including actual `gws` CLI commands (if applicable).
Example:
```
gws gmail +triage --query "{event_name}" --max 50
```

## Output Format
Show the exact structure of the skill's output (markdown table, structured text, etc.).

## Principles
3–5 statements of what makes output high-quality and why. These are the rules that prevent common mistakes.

## What to Avoid
3–5 specific anti-patterns. Describe the mistake and what goes wrong if you don't catch it.

## GWS Gotchas
(Include this section if the skill uses GWS commands.)
Document any GWS CLI quirks, auth edge cases, or command-specific pitfalls.

## Tool Integration
(Optional — include if the skill uses GWS tools.)
Table of GWS tools used, commands, and purpose.

## Resources
Links to reference files and external resources.
```

---

## Naming Conventions

- **Skill directory**: `skills/{skill-name}/` — lowercase with hyphens, no prefix
- Examples: `skills/inbox-digest/`, `skills/vendor-tracker/`, `skills/budget-tracker/`

---

## Testing Your Skill

Before submitting a pull request:

1. **Copy your skill to Claude Code's skill directory**:
   ```bash
   cp -r skills/{skill-name} ~/.claude/skills/
   ```

2. **Invoke the skill in Claude Code**:
   ```
   /skill-name
   ```

3. **Test the workflow** — run through each task in the Workflow by Task section. Verify that:
   - All steps execute and return expected results
   - Output format matches the defined Output Format section
   - Principles section correctly describes quality
   - What to Avoid section actually reflects mistakes the workflow prevents

4. **Test with real event data** if possible. Dummy data won't catch contextual errors.

5. **(Optional) If the skill uses GWS commands**, install and authenticate:
   ```bash
   brew install gws && gws auth login
   ```
   Then verify all `gws` CLI commands execute and return expected data.

---

## Quality Bar

- **Workflow by Task must have actionable steps** — each step should be executable. Include actual `gws CLI` commands where applicable, not pseudocode.
- **Principles section required** — what makes output good in this context? What decisions does a human need to make?
- **What to Avoid section required** — name 3–5 specific mistakes that break the skill's output. "Don't forget to..." is not enough; "If you skip X, this happens" is the right level of specificity.
- **Event industry terminology** — use "vendor", "load-in", "run-of-show", "advance", "production week", not generic "partner", "delivery", "timeline".
- **GWS integration is optional** — domain knowledge is the core value. A skill that encodes expert event logic without any GWS commands is still valuable.
- **Include a GWS Gotchas section** if the skill uses GWS commands — document auth quirks, command pitfalls, and edge cases.

---

## Pull Request Process

1. **Fork this repository** (or branch if you have direct access).

2. **Create a feature branch**:
   ```bash
   git checkout -b feat/{skill-name}
   ```

3. **Write your skill** in `skills/{skill-name}/SKILL.md`.

4. **Add any reference files** in a `references/` subdirectory (decision trees, pattern lists, etc.). Keep reference files tight — under 100 lines each.

5. **Test locally** (see Testing section above).

6. **Commit with a clear message**:
   ```bash
   git add skills/{skill-name}/
   git commit -m "create(skill): skill-name — one-line description"
   ```

7. **Push and open a PR** with:
   - Skill name in the title: `Add skill: {skill-name}`
   - Description of what the skill does and when to use it
   - Note any GWS CLI dependencies (if applicable)
   - Link to any reference files or examples

---

## Questions?

Check the existing skills in `skills/` for patterns and examples. The `inbox-digest` and `cold-outreach` skills demonstrate the full structure and quality bar.

Thank you for contributing to event-agency-skills.

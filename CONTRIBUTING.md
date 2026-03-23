# Contributing Event Skills

Welcome to event-agency-skills. Event industry expertise is valued here — your skills, workflows, and domain knowledge directly improve the toolkit for production teams.

## Overview

This repository hosts reusable Claude skills for event professionals: recipe skills that encode repeatable workflows, and persona skills that embody production roles. All skills integrate with Google Workspace tools (Gmail, Calendar, Docs, Sheets, Drive) for seamless execution within event management platforms.

---

## Adding a Recipe Skill

Recipe skills encode repeatable workflows for specific event tasks (inbox triage, vendor tracking, budget reconciliation, etc.).

### Structure

```
skills/recipe-event-{name}/
├── SKILL.md              # Skill definition (required)
├── references/           # Optional reference files
│   ├── decision-tree.md
│   └── patterns.md
└── examples/             # Optional example outputs
```

### SKILL.md Template

Create `skills/recipe-event-{name}/SKILL.md` following the Anca structure:

```yaml
---
name: recipe-event-your-skill
version: 1.0.0
description: "What this skill does. When to use it."
metadata:
  category: "recipe"
  requires:
    skills:
      - gws-gmail
      - gws-docs
---

# Your Skill Name

## Purpose
Concise statement of the problem this skill solves. Why does this workflow matter in event production?

## When to Use
Bulleted scenarios where this skill saves time or prevents mistakes. "Use when..." — be specific to event context.

## Inputs
Table listing required and optional inputs with defaults and validation notes.

## Workflow by Task
Numbered tasks with step-by-step instructions including actual `gws` CLI commands.
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

## Tool Integration
Table of GWS tools used, commands, and purpose.

## Resources
Links to reference files and external resources.
```

### Quality Bar

- **Workflow by Task must have actionable steps** — each step should be executable. Include actual `gws CLI` commands, not pseudocode.
- **Principles section required** — what makes output good in this context? What decisions does a human need to make?
- **What to Avoid section required** — name 3–5 specific mistakes that break the skill's output. "Don't forget to..." is not enough; "If you skip X, this happens" is the right level of specificity.
- **Event industry terminology** — use "vendor", "load-in", "run-of-show", "advance", "production week", not generic "partner", "delivery", "timeline".
- **Cross-reference Google Workspace tools** — show which tools the skill requires in metadata.requires and in the Tool Integration table.

---

## Adding a Persona Skill

Persona skills embody event production roles (coordinator, production manager, sponsor manager, etc.). They orchestrate multiple recipe skills and workflows into a coherent operating model.

### Structure

```
skills/persona-event-{name}/
├── SKILL.md              # Skill definition (required)
└── workflows/            # Optional workflow templates
    └── daily-routine.md
```

### SKILL.md Template

Create `skills/persona-event-{name}/SKILL.md` with the same Anca structure as recipe skills:

```yaml
---
name: persona-event-your-role
version: 1.0.0
description: "Event [Role] persona — [what this role owns]. Use when [primary context]."
metadata:
  category: "persona"
  requires:
    skills:
      - recipe-event-inbox-digest
      - gws-gmail
      - gws-calendar
---
```

Key sections (same Anca structure as recipes):
- **Purpose** — the operating model this persona enables
- **When to Use** — phases of the event (kickoff, daily ops, advance, post-event)
- **Inputs** — event name, production phase, stakeholder list
- **Workflow by Task** — the repeatable routines this role executes
- **Output Format** — status updates, daily summaries, stakeholder briefs
- **Principles** — values, SLAs, accountability standards
- **What to Avoid** — common coordination mistakes
- **Tool Integration** — how this role uses Drive, Sheets, Docs, Gmail, Calendar together
- **Resources** — reference files and dependent recipe skills

Persona skills declare their gws skill dependencies in `metadata.requires.skills`.

---

## Naming Conventions

- **Recipe skills**: `recipe-event-{action-noun}` (e.g., `recipe-event-inbox-digest`, `recipe-event-vendor-tracker`)
- **Persona skills**: `persona-event-{role}` (e.g., `persona-event-coordinator`, `persona-event-production-manager`)
- Skill names are lowercase with hyphens. Spaces → hyphens.

---

## Testing Your Skill

Before submitting a pull request:

1. **Install the GWS CLI** (if not already installed):
   ```bash
   bash .system/scripts/setup-gws.sh
   ```

2. **Generate skills from your local directory**:
   ```bash
   gws generate-skills
   ```

3. **Copy your skill to Claude Code's skill directory**:
   ```bash
   cp -r skills/recipe-event-{name} ~/.claude/skills/
   ```

4. **Invoke the skill in Claude Code**:
   ```
   /recipe-event-{name}
   ```
   or
   ```
   /persona-event-{name}
   ```

5. **Test the workflow** — run through each task in the Workflow by Task section. Verify that:
   - All `gws` CLI commands execute and return expected data
   - Output format matches the defined Output Format section
   - Principles section correctly describes quality
   - What to Avoid section actually reflects mistakes the workflow prevents

6. **Test with real event data** if possible. Dummy data won't catch contextual errors.

---

## Pull Request Process

1. **Fork this repository** (or branch if you have direct access).

2. **Create a feature branch**:
   ```bash
   git checkout -b feat/recipe-event-{name}
   ```

3. **Write your skill** in `skills/recipe-event-{name}/SKILL.md` or `skills/persona-event-{name}/SKILL.md`.

4. **Add any reference files** in a `references/` subdirectory (decision trees, pattern lists, etc.). Keep reference files tight — under 100 lines each.

5. **Test locally** (see Testing section above).

6. **Commit with a clear message**:
   ```bash
   git add skills/recipe-event-{name}/
   git commit -m "create(recipe): recipe-event-{name} — one-line description"
   ```

7. **Push and open a PR** with:
   - Skill name and category in the title: `Add recipe: recipe-event-{name}`
   - Description of what the skill does and when to use it
   - Note any gws CLI dependencies you added or assumed
   - Link to any reference files or examples

---

## Questions?

Check the existing skills in `skills/` for patterns and examples. The `recipe-event-inbox-digest` and `persona-event-coordinator` skills demonstrate the full structure and quality bar.

Thank you for contributing to event-agency-skills.

# Contributing Event Skills

Welcome to event-agency-skills. Event industry expertise is valued here — your skills, workflows, and domain knowledge directly improve the toolkit for production teams.

## Overview

This repository hosts reusable event production skills powered by [Composio](https://composio.dev) for tool integration. Each skill combines domain knowledge (SKILL.md) with executable Python scripts for Gmail, Calendar, Sheets, HubSpot, and more.

---

## Adding a Skill

### Structure

```
skills/{skill-name}/
├── SKILL.md              # Skill definition (required)
├── scripts/              # Executable Python scripts (required for v2+ skills)
│   ├── main_workflow.py  # Primary script for the skill's core operation
│   └── helper_script.py  # Optional additional scripts
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
version: 2.0.0
description: "What it does. Use when [context]. Triggers: 'keyword1', 'keyword2'."
tools: ["composio:GMAIL_FETCH_EMAILS", "composio:GOOGLESHEETS_BATCH_GET"]
scripts: ["scripts/main_workflow.py"]
---

# Your Skill Name

## Purpose
Concise statement of the problem this skill solves. Why does this workflow matter in event production?

## When to Use
Bulleted scenarios where this skill saves time or prevents mistakes.

## When NOT to Use
Explicit boundaries — what this skill does NOT do.

## Inputs
Table listing required and optional inputs with defaults and validation notes.

## Quick Reference
Domain-specific thresholds, classifications, or formulas used by the skill.

## Workflow by Task
Numbered tasks with:
- **Script mode**: CLI command examples using the Python scripts
- **Interactive mode**: Composio tool actions for Claude-guided workflows

## Output Format
Show the exact structure of the skill's output.

## Principles
3-5 statements of what makes output high-quality and why.

## What to Avoid
3-5 specific anti-patterns with consequences.

## Tool Integration
### Composio Tools (Primary)
Table of Composio actions used, with safety tier annotations.

### Scripts
Table of Python scripts with CLI commands and purpose.

## Composio Notes
Document any Composio-specific quirks or patterns.

## Resources
Links to reference files and external resources.
```

### Script Template

Each script should follow this pattern:

```python
#!/usr/bin/env python3
"""One-line description of what this script does."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from lib.composio_client import EventComposioClient
from lib.event_context import EventContext  # and other imports as needed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--event", required=True, help="Event name")
    parser.add_argument("--date", required=True, help="Event date (YYYY-MM-DD)")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # ... implementation
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Requirements:**
- Import shared libraries from `lib/` (composio_client, event_context)
- Use `argparse` with clear help strings
- Support `--dry-run` that works without a Composio API key
- Support `--json` for machine-readable output
- Support `--output` for file output (default: stdout)
- Include `main()` function returning an exit code

---

## Naming Conventions

- **Skill directory**: `skills/{skill-name}/` — lowercase with hyphens
- **Script files**: `skills/{skill-name}/scripts/{script_name}.py` — lowercase with underscores
- **Shared libraries**: `lib/{module_name}.py` — lowercase with underscores

---

## Composio Integration

### Safety Tiers

All Composio tool operations must follow the 3-tier safety model in `.claude/rules/composio-safety.md`:

| Tier | Actions | Rule |
|------|---------|------|
| **T1 Read** | `GMAIL_FETCH_EMAILS`, `GOOGLESHEETS_BATCH_GET`, etc. | Auto-allowed |
| **T2 Write** | `GMAIL_CREATE_EMAIL_DRAFT`, `GOOGLESHEETS_BATCH_UPDATE`, etc. | Confirm with user |
| **T3 Dangerous** | `GMAIL_SEND_DRAFT`, `GMAIL_DELETE_MESSAGE`, etc. | Preview + explicit approval |

### Adding New Integrations

If your skill needs a Composio tool not yet in `lib/composio_client.py`:

1. Add the method to `EventComposioClient` in `lib/composio_client.py`
2. Document the safety tier in `.claude/rules/composio-safety.md`
3. Add the action to the `tools:` list in your SKILL.md frontmatter
4. Update `.claude/settings.json` if it's a T1 (auto-allowed) action

---

## Testing Your Skill

Before submitting a pull request:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # Optional: for standalone script usage with Composio SDK
   pip install composio
   ```

2. **Verify scripts compile**:
   ```bash
   python -m py_compile skills/{skill-name}/scripts/{script}.py
   ```

3. **Test dry-run mode** (no API key needed):
   ```bash
   python skills/{skill-name}/scripts/{script}.py --event "Test Event" --date 2026-06-01 --dry-run
   ```

4. **Test with real data** if you have a Composio API key:
   ```bash
   export COMPOSIO_API_KEY="your-key"
   python skills/{skill-name}/scripts/{script}.py --event "Test Event" --date 2026-06-01
   ```

5. **Test as a Claude Code skill** (optional):
   ```bash
   cp -r skills/{skill-name} ~/.claude/skills/
   # Then invoke in Claude Code: /skill-name
   ```

---

## Quality Bar

- **Scripts must be executable** — every script must run with `--help` and `--dry-run` without errors
- **Domain knowledge in SKILL.md** — the skill must encode real event production logic, not generic workflows
- **Principles section required** — what makes output good in this event production context?
- **What to Avoid section required** — 3-5 specific mistakes with consequences
- **Event industry terminology** — use "vendor", "load-in", "run-of-show", "advance", not generic terms
- **Safety tiers documented** — every Composio tool used must have a safety tier annotation
- **Shared library usage** — import from `lib/` for Composio client and event context, don't duplicate

---

## Pull Request Process

1. **Fork this repository** (or branch if you have direct access).

2. **Create a feature branch**:
   ```bash
   git checkout -b feat/{skill-name}
   ```

3. **Write your skill** in `skills/{skill-name}/` with SKILL.md and scripts.

4. **Verify scripts compile and run** (see Testing section above).

5. **Commit with a clear message**:
   ```bash
   git add skills/{skill-name}/
   git commit -m "create(skill): skill-name — one-line description"
   ```

6. **Push and open a PR** with:
   - Skill name in the title: `Add skill: {skill-name}`
   - Description of what the skill does and when to use it
   - Note any new Composio integrations required
   - Link to any reference files

---

## Questions?

Check the existing skills in `skills/` for patterns and examples. The `inbox-digest` and `vendor-tracker` skills demonstrate the full structure and quality bar.

Thank you for contributing to event-agency-skills.

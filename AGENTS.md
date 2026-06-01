# Agent Instructions

This repository follows the WG Technology Labs Clean Commit convention for all commit messages.

## Commit Format

Use one of these formats:

```text
<emoji> <type>: <description>
<emoji> <type> (<scope>): <description>
<emoji> <type>!: <description>
<emoji> <type>! (<scope>): <description>
```

## Types

| Emoji | Type | What it covers |
|:-----:|------|----------------|
| 📦 | `new` | Adding new features, files, or capabilities |
| 🔧 | `update` | Changing existing code, refactoring, improvements |
| 🗑️ | `remove` | Removing code, files, features, or dependencies |
| 🔒 | `security` | Security fixes, patches, vulnerability resolutions |
| ⚙️ | `setup` | Project configs, CI/CD, tooling, build systems |
| ☕ | `chore` | Maintenance tasks, dependency updates, housekeeping |
| 🧪 | `test` | Adding, updating, or fixing tests |
| 📖 | `docs` | Documentation changes and updates |
| 🚀 | `release` | Version releases and release preparation |

## Rules

- Use lowercase type names.
- Use present tense.
- Do not end the description with a period.
- Keep descriptions concise and under 72 characters when possible.
- Use a scope only when it improves clarity.

## Project Priorities

- Keep this repo reusable-workflow-first.
- Preserve build and validation before release sequencing.
- Update docs and examples when workflow behavior changes.
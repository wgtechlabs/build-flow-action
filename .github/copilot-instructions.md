# Build Flow Action Copilot Instructions

## Project Overview

Build Flow Action is the reusable-workflow-first orchestration layer for CI, packaging, containerization, and release automation.

## Commit Convention

All commits must follow the WG Technology Labs Clean Commit convention.

```text
<emoji> <type>: <description>
<emoji> <type> (<scope>): <description>
<emoji> <type>!: <description>
<emoji> <type>! (<scope>): <description>
```

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

## Workflow Rules

- Keep build and validation steps before release steps.
- Preserve the reusable-workflow-first orchestration model.
- Update docs and examples when workflow behavior changes.
- Prefer small, focused changes that keep app, package, container, and release flows coherent.
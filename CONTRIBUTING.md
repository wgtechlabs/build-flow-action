# Contributing

Thanks for contributing to Build Flow Action.

## Contribution Standards

- Follow the WG Technology Labs Clean Commit convention.
- Keep pull requests focused and coherent.
- Update docs and examples when behavior changes.
- Prefer safe-by-default orchestration decisions.
- Do not manually edit `CHANGELOG.md`; changelog updates are owned by the release-build-flow primitive.

## Local Validation

This repository is currently documentation-and-workflow scaffold oriented. As implementation evolves, validation commands will be expanded.

Current minimum checks before opening a PR:

- Review workflow YAML for valid structure.
- Validate docs/examples reflect the reusable-workflow-first model.
- Ensure release remains the final orchestration step in workflow logic.

## Pull Request Guidance

- Describe intent and user impact clearly.
- Reference changed workflow(s) and example(s).
- Include migration notes when changing workflow contracts.

# Contributing

Thanks for contributing to Build Flow Action.

## Contribution Standards

- Follow the WG Technology Labs Clean Commit convention.
- Keep pull requests focused and coherent.
- Update docs and examples when behavior changes.
- Prefer safe-by-default orchestration decisions.
- Do not manually edit `CHANGELOG.md`; changelog updates are owned by the release-build-flow primitive.

## Local Validation

Run the workflow contracts from the repository root:

```sh
pwsh -NoProfile -File tests/workflow-contract.ps1
python3 tests/container-images.py
```

Current minimum checks before opening a PR:

- Review workflow YAML for valid structure.
- Validate docs/examples reflect the reusable-workflow-first model.
- Ensure release remains the final orchestration step in workflow logic.
- For multi-image changes, cover input validation and a partially published batch; one image's success must never allow a release when another image failed or did not publish.

## Pull Request Guidance

- Describe intent and user impact clearly.
- Reference changed workflow(s) and example(s).
- Include migration notes when changing workflow contracts.

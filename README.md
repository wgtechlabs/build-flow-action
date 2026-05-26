# Build Flow Action

Build Flow Action is the flagship WG Technology Labs orchestration layer for CI, packaging, containerization, and release automation.

## Vision

Provide one safe-by-default entrypoint so teams can adopt a complete build and release flow without manually wiring separate `ci.yml`, `release.yml`, and `container.yml` files.

## Status

> MVP orchestration scaffold with primitive wiring in place.

This repository is intentionally reusable-workflow-first. The reusable workflows now invoke WG Technology Labs package/container/release primitives with policy gates and release-last sequencing. CI and CodeQL implementation details continue to evolve incrementally.

## Ecosystem Relationship

Build Flow Action orchestrates these WG Technology Labs primitives:

- [`wgtechlabs/release-build-flow-action`](https://github.com/wgtechlabs/release-build-flow-action)
- [`wgtechlabs/package-build-flow-action`](https://github.com/wgtechlabs/package-build-flow-action)
- [`wgtechlabs/container-build-flow-action`](https://github.com/wgtechlabs/container-build-flow-action)

## Core Philosophy

- Build and validate first
- Publish package/container artifacts after successful build gates
- Finalize GitHub release last
- Avoid release-first orchestration patterns

## Quick Start

Use one reusable workflow from your project:

```yaml
name: Build Flow

on:
  pull_request:
    branches: [dev, main]
  push:
    branches: [dev, main]
  workflow_dispatch:

jobs:
  flow:
    uses: wgtechlabs/build-flow-action/.github/workflows/app.yml@main
    secrets: inherit
    with:
      enable-package: true
      enable-container: true
      enable-release: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
      main-branch: main
      dev-branch: dev
      publish-dev-artifacts: false
      publish-pr-artifacts: false
      publish-manual-artifacts: false
      package-registry: both
      package-dry-run: false
      container-registry: both
      container-image-name: ''
      container-tag-prefix: ''
      container-tag-suffix: ''
      release-changelog-path: ./CHANGELOG.md
      release-draft: false
      release-prerelease: false
      release-dry-run: false
      release-version-prefix: v
      release-create: true
```

## Available Reusable Workflows

- `.github/workflows/app.yml` — full application orchestration flow
- `.github/workflows/package.yml` — package-only flow
- `.github/workflows/container.yml` — container-only flow

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`examples/`](examples)

## License

MIT

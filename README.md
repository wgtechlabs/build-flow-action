# Build Flow Action

Build Flow Action is the flagship WG Technology Labs orchestration layer for CI, packaging, containerization, and release automation.

## Vision

Provide one safe-by-default entrypoint so teams can adopt a complete build and release flow without manually wiring separate `ci.yml`, `release.yml`, and `container.yml` files.

## Status

> MVP scaffold in progress.

This repository is intentionally reusable-workflow-first. The initial workflows define orchestration shape and safe sequencing while implementation details are wired in incrementally.

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

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
      enable-gitleaks: true
      enable-codeql: true
      codeql-languages: auto
      codeql-build-mode: autobuild
      ci-profile: auto
      ci-runs-on: ubuntu-latest
      ci-runtime-version: '22'
      ci-matrix-versions: '["20","22"]'
      ci-install-command: npm ci
      ci-lint-command: npm run lint --if-present
      ci-typecheck-command: npm run typecheck --if-present
      ci-test-command: npm test --if-present
      ci-build-command: npm run build --if-present
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

- `.github/workflows/ci.yml` — unified CI/security gate reusable workflow
- `.github/workflows/app.yml` — full application orchestration flow
- `.github/workflows/package.yml` — package-only flow
- `.github/workflows/container.yml` — container-only flow

## CI Profiles and Custom Commands

`ci.yml` supports `explicit profile -> auto detect -> custom` and can be used directly or through `app.yml`, `package.yml`, and `container.yml`.

Profiles auto-detect from lockfiles/manifests (`auto`) or can be set explicitly. Each profile includes sensible default commands and dependency caching.

```yaml
# Node/Bun (auto-detects .nvmrc/.node-version for version pinning)
ci-profile: node-bun
ci-install-command: bun install --frozen-lockfile
ci-test-command: bun test

# Python (defaults: pip install, pytest)
ci-profile: python
ci-runtime-version: '3.13'
ci-matrix-versions: '["3.11","3.12"]'
ci-install-command: pip install -r requirements.txt
ci-test-command: pytest -q

# Go (defaults: go build, go test)
ci-profile: go
ci-runtime-version: '1.23'
ci-test-command: go test ./...

# Rust (defaults: cargo build, cargo test, cargo clippy)
ci-profile: rust
ci-build-command: cargo build
ci-test-command: cargo test

# Java (defaults: gradlew/mvn build and test)
ci-profile: java
ci-matrix-versions: '["17","21"]'
ci-build-command: ./gradlew build

# C/C++ (defaults: cmake build and ctest)
ci-profile: c-cpp
ci-build-command: cmake -S . -B build && cmake --build build
ci-test-command: ctest --test-dir build --output-on-failure

# Custom (no defaults — bring your own commands)
ci-profile: custom
ci-setup-command: ./scripts/ci/setup.sh
ci-install-command: ./scripts/ci/install.sh
ci-lint-command: ./scripts/ci/lint.sh
ci-test-command: ./scripts/ci/test.sh
```

## Runner and Version Configuration

All CI jobs default to `ubuntu-latest`. Override with `ci-runs-on` for macOS, Windows, or self-hosted runners:

```yaml
ci-runs-on: macos-latest        # or windows-latest, self-hosted, etc.
ci-runtime-version: '22'        # pin runtime version without using matrix
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`examples/`](examples)

## License

MIT

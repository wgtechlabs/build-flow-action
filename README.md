# Build Flow Action

One workflow. Full CI, security, packaging, containers, and releases — safe by default.

Build Flow Action is the orchestration layer by [WG Technology Labs](https://github.com/wgtechlabs) that coordinates your entire build and release lifecycle through a single reusable workflow call.

## Why Build Flow?

Without Build Flow, teams must manually wire separate workflows for CI, security scanning, package publishing, container builds, and releases. This leads to:

- Unsafe release ordering (publishing a release before artifacts are built)
- Duplicated workflow boilerplate across repositories
- Inconsistent CI checks and security gates
- Visible GitHub Releases with missing production artifacts

Build Flow eliminates these problems with one rule: **build and validate first, release last.**

## Getting Started

Add one workflow file to your repository. That's it.

### Zero-Config (auto-detects your ecosystem)

```yaml
# .github/workflows/build-flow.yml
name: Build Flow

on:
  pull_request:
    branches: [dev, main]
  push:
    branches: [dev, main]

jobs:
  build-flow:
    uses: wgtechlabs/build-flow-action/.github/workflows/app.yml@main
    secrets: inherit
```

Build Flow auto-detects your project from lockfiles and manifests — no configuration needed for most projects.

### With Common Options

```yaml
jobs:
  build-flow:
    uses: wgtechlabs/build-flow-action/.github/workflows/app.yml@main
    secrets: inherit
    with:
      ci-profile: auto
      enable-gitleaks: true
      enable-codeql: true
      enable-package: true
      enable-container: true
      enable-release: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
```

### CI-Only (no packaging or releases)

```yaml
jobs:
  ci:
    uses: wgtechlabs/build-flow-action/.github/workflows/ci.yml@main
    secrets: inherit
    with:
      ci-profile: auto
```

## Supported Ecosystems

| Ecosystem | Profile | Auto-Detected From | Default Commands |
|-----------|---------|-------------------|-----------------|
| Node.js + Bun | `node-bun` | `bun.lockb`, `bun.lock` | install, lint, typecheck, test, build |
| Node.js | `node` | `package.json` | npm ci, lint, typecheck, test, build |
| Python | `python` | `pyproject.toml`, `requirements.txt` | pip install, pytest |
| Go | `go` | `go.mod` | go build, go test |
| Rust | `rust` | `Cargo.toml` | cargo build, cargo test, cargo clippy |
| Java | `java` | `pom.xml`, `build.gradle`, `build.gradle.kts` | gradlew/mvn build and test |
| C/C++ | `c-cpp` | `CMakeLists.txt` | cmake build, ctest |
| Custom | `custom` | — | Bring your own commands |

All profiles support overriding individual commands via `ci-*-command` inputs.

## What You Get

When you call `app.yml`, Build Flow runs this dependency graph:

```
1. Context Detection     → determines branch, event, and policy
2. CI Gate               → install, lint, typecheck, test, build + Gitleaks (matrix support)
   ├── 3a. Package Publishing  → delegates to package-build-flow-action
   ├── 3b. Container Publishing → delegates to container-build-flow-action
   └── 4. Release Finalization  → creates GitHub Release LAST (after package + container)
   CodeQL (parallel)     → independent security scan (does not gate publishing or release)
```

Key behaviors:
- **Release is always last** — no public release until all artifacts succeed
- **Smart check visibility** — only relevant checks appear on your PRs (no skipped noise)
- **Matrix validation** — test across multiple runtime versions automatically
- **Ecosystem caching** — dependency caching for npm, pip, Go modules

## Available Workflows

| Workflow | Use Case |
|----------|----------|
| `app.yml` | Full orchestration: CI + security + package + container + release |
| `ci.yml` | CI and security validation only (no publishing) |
| `package.yml` | CI + package publishing + release |
| `container.yml` | CI + container publishing + release |
| `codeql.yml` | Standalone CodeQL security scanning (called internally) |

**Usage pattern** — these are [reusable workflows](https://docs.github.com/en/actions/sharing-automations/reusing-workflows). Reference them with:

```yaml
uses: wgtechlabs/build-flow-action/.github/workflows/<workflow>@main
```

## CI Profiles and Custom Commands

Profiles auto-detect from lockfiles (`auto`) or can be set explicitly. Each profile includes sensible defaults and dependency caching.

```yaml
# Node/Bun — auto-detects .nvmrc/.node-version for version pinning
ci-profile: node-bun
ci-install-command: bun install --frozen-lockfile
ci-test-command: bun test

# Python
ci-profile: python
ci-runtime-version: '3.13'
ci-matrix-versions: '["3.11","3.12","3.13"]'
ci-install-command: pip install -r requirements.txt
ci-test-command: pytest -q

# Go
ci-profile: go
ci-runtime-version: '1.23'
ci-test-command: go test ./...

# Rust
ci-profile: rust
ci-build-command: cargo build
ci-test-command: cargo test

# Java
ci-profile: java
ci-matrix-versions: '["17","21"]'
ci-build-command: ./gradlew build

# C/C++
ci-profile: c-cpp
ci-build-command: cmake -S . -B build && cmake --build build
ci-test-command: ctest --test-dir build --output-on-failure

# Custom — bring your own commands
ci-profile: custom
ci-setup-command: ./scripts/ci/setup.sh
ci-install-command: ./scripts/ci/install.sh
ci-lint-command: ./scripts/ci/lint.sh
ci-test-command: ./scripts/ci/test.sh
```

## Runner and Version Configuration

All CI jobs default to `ubuntu-latest`. Override with `ci-runs-on` for macOS, Windows, or self-hosted runners:

```yaml
ci-runs-on: macos-latest
ci-runtime-version: '22'
ci-matrix-versions: '["20","22"]'
```

## Ecosystem Relationship

Build Flow orchestrates these WG Technology Labs primitives:

- [`wgtechlabs/release-build-flow-action`](https://github.com/wgtechlabs/release-build-flow-action) — release automation
- [`wgtechlabs/package-build-flow-action`](https://github.com/wgtechlabs/package-build-flow-action) — package publishing (npm, GitHub Packages)
- [`wgtechlabs/container-build-flow-action`](https://github.com/wgtechlabs/container-build-flow-action) — container publishing (Docker Hub, GHCR)

You don't need to install or configure these separately — Build Flow calls them internally with the correct sequencing and policy gates.

## Security

Build Flow includes security scanning out of the box:

- **Gitleaks** — detects secrets committed to your repository (enabled by default)
- **CodeQL** — static analysis for vulnerabilities (enabled by default, language auto-detected)

Both are enabled by default. Gitleaks runs as part of the CI gate and blocks releases if secrets are detected. CodeQL runs as an independent security scan alongside the CI gate.

## Branch Strategy

Build Flow is designed for the [Clean Flow](https://github.com/wgtechlabs/clean-flow) workflow:

| Event | Behavior |
|-------|----------|
| PR to `dev` or `main` | CI + security gates |
| Push to `dev` | CI + optional dev artifact publishing |
| Push to `main` | CI + publish artifacts + finalize release |
| Manual dispatch | Configurable operational/recovery scenarios |

## Examples

See the [`examples/`](examples/) directory for complete workflow files:

- [`examples/app.yml`](examples/app.yml) — full orchestration (Node/Bun project)
- [`examples/minimal.yml`](examples/minimal.yml) — zero-config auto-detect
- [`examples/ci-only.yml`](examples/ci-only.yml) — CI validation only
- [`examples/package-only.yml`](examples/package-only.yml) — package flow (Python project)
- [`examples/container-only.yml`](examples/container-only.yml) — container flow (C/C++ project)

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — design philosophy and orchestration model
- [`docs/roadmap.md`](docs/roadmap.md) — planned features and improvements

## License

MIT

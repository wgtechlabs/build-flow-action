# Build Flow Action

[![Build Flow Action - GitHub Repo Banner](https://ghrb.waren.build/banner?header=Build+Flow+Action+%F0%9F%9A%82&subheader=Reusable-workflow-first+CI%2C+package%2C+container%2C+and+release+orchestration&bg=013B84-016EEA&color=FFFFFF)](https://github.com/wgtechlabs/build-flow-action)
<!-- Created with GitHub Repo Banner by Waren Gonzaga: https://ghrb.waren.build -->

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

Build Flow auto-detects your project from lockfiles and manifests. Zero-config gives you CI validation, security scanning, and release finalization. Package and container flows in `app.yml` stay opt-in via `enable-package` and `enable-container`.

For production repositories, pin reusable workflow references to a release tag or commit SHA instead of `@main`.

### With Package and Container Publishing

```yaml
permissions:
  contents: write          # release commits, tags, and changelog
  packages: write          # npm / GitHub Packages / GHCR
  pull-requests: write     # default PR comments from primitives
  security-events: write   # CodeQL + container SARIF upload
  actions: read            # CodeQL

jobs:
  build-flow:
    uses: wgtechlabs/build-flow-action/.github/workflows/app.yml@main
    secrets: inherit
    with:
      ci-profile: auto
      enable-package: true        # opt-in: publish to npm/GitHub Packages
      enable-container: true      # opt-in: publish to Docker Hub/GHCR
      container-registry: docker-hub
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
3. Version Plan (main)   → release primitive dry run produces immutable version metadata
  ├── 4a. Package Publishing  → consumes the planned version
  ├── 4b. Container Publishing → consumes the planned tag
   └── 5. Release Finalization  → creates GitHub Release LAST after an artifact publishes
   CodeQL (parallel)     → independent security scan (does not gate publishing or release)
```

Default behavior (zero-config): CI + security on main. Enable a package or container flow to publish artifacts and finalize a release. When enabled (or when using `package.yml` / `container.yml` directly), artifact publishing defaults to allowed on main, dev, PR, manual, and published release events unless you set a `publish-*-artifacts` input to `false`.

Key behaviors:
- **Immutable main releases** — a dry-run release plan supplies one version to every planned artifact and finalization
- **Release is always last** — no public release until at least one enabled artifact reports publication
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

For production safety, prefer:

```yaml
uses: wgtechlabs/build-flow-action/.github/workflows/<workflow>@v0
# or pin to a full commit SHA
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

## Inputs Reference

Source of truth: `.github/workflows/app.yml` (`on.workflow_call.inputs`).

### Orchestration toggles

| Input | Default | Description |
|-------|---------|-------------|
| `enable-package` | `false` | Enable package flow orchestration |
| `enable-container` | `false` | Enable container flow orchestration |
| `enable-release` | `true` | Enable release finalization orchestration |
| `enable-gitleaks` | `true` | Enable Gitleaks gate |
| `enable-codeql` | `true` | Enable CodeQL gate |

### CI configuration

| Input | Default | Description |
|-------|---------|-------------|
| `ci-profile` | `auto` | CI profile (auto\|node-bun\|node\|python\|go\|rust\|java\|c-cpp\|custom) |
| `ci-runs-on` | `ubuntu-latest` | Runner label for CI jobs (e.g., ubuntu-latest, macos-latest, self-hosted) |
| `ci-runtime-version` | `""` | Runtime version for non-matrix validation (e.g., 22 for Node, 3.13 for Python) |
| `ci-matrix-versions` | `""` | JSON array of runtime versions (example: `["20","22"]`) |
| `ci-setup-command` | `""` | Optional setup command |
| `ci-install-command` | `""` | Optional install command |
| `ci-lint-command` | `""` | Optional lint command |
| `ci-typecheck-command` | `""` | Optional typecheck command |
| `ci-test-command` | `""` | Optional test command |
| `ci-coverage-command` | `""` | Optional coverage command |
| `ci-build-command` | `""` | Optional build command |
| `ci-docker-smoke-command` | `""` | Optional docker smoke command |
| `codeql-languages` | `auto` | CodeQL languages (auto or comma-separated list) |
| `codeql-build-mode` | `autobuild` | CodeQL build mode (autobuild or manual) |

### Branch/publish policy

| Input | Default | Description |
|-------|---------|-------------|
| `main-branch` | `main` | Main branch name |
| `dev-branch` | `dev` | Development branch name |
| `publish-dev-artifacts` | `true` | Allow artifact publishing on dev branch pushes |
| `publish-pr-artifacts` | `true` | Allow artifact publishing for pull requests |
| `publish-manual-artifacts` | `true` | Allow artifact publishing for workflow_dispatch runs |

### Container inputs

| Input | Default | Description |
|-------|---------|-------------|
| `container-registry` | `both` | Container registry target (docker-hub, ghcr, or both) |
| `container-image-name` | `""` | Optional image name override |
| `container-tag-prefix` | `""` | Optional tag prefix |
| `container-tag-suffix` | `""` | Optional tag suffix |
| `container-ghcr-username` | `""` | GHCR username override (defaults to repository owner) |
| `container-dockerfile` | `./Dockerfile` | Dockerfile path |
| `container-context` | `.` | Build context path |
| `container-platforms` | `linux/amd64` | Target platforms (comma-separated) |
| `container-release-platforms` | `linux/amd64,linux/arm64` | Release-build platforms (empty uses `container-platforms`) |
| `container-build-args` | `""` | Build arguments (newline-separated) |
| `container-labels` | `""` | Image labels (newline-separated) |
| `container-cache-enabled` | `true` | Enable build cache |
| `container-pr-comment-enabled` | `true` | Enable PR comments with pull instructions |
| `container-pr-comment-template` | `""` | Custom PR comment template |
| `container-push-enabled` | `true` | Enable pushing to registry |
| `container-load-enabled` | `false` | Load image to Docker daemon |
| `container-provenance` | `true` | Enable provenance attestation |
| `container-sbom` | `true` | Enable SBOM attestation |
| `container-pre-build-scan-enabled` | `true` | Enable pre-build security scanning |
| `container-scan-source-code` | `true` | Scan source code and dependencies before build |
| `container-scan-dockerfile` | `true` | Scan Dockerfile for misconfigurations |
| `container-image-scan-enabled` | `true` | Enable post-build image scan |
| `container-trivy-severity` | `HIGH,CRITICAL` | Trivy severity levels to scan |
| `container-trivy-ignore-unfixed` | `false` | Ignore vulnerabilities without available fixes |
| `container-trivy-timeout` | `10m0s` | Trivy scan timeout duration |
| `container-trivy-skip-dirs` | `""` | Directories to skip during Trivy scan |
| `container-trivy-skip-files` | `""` | Files to skip during Trivy scan |
| `container-upload-sarif` | `true` | Upload vulnerability results to GitHub Security tab |
| `container-sarif-category-source` | `trivy-source-scan` | SARIF category for source code scan |
| `container-sarif-category-dockerfile` | `trivy-dockerfile-scan` | SARIF category for Dockerfile scan |
| `container-sarif-category-image` | `trivy-container-scan` | SARIF category for image scan |
| `container-vulnerability-comment-enabled` | `true` | Add vulnerability results to PR comments |
| `container-enable-image-comparison` | `false` | Compare vulnerabilities with a baseline image |
| `container-comparison-baseline-image` | `""` | Baseline image tag for comparison |
| `container-fail-on-vulnerability` | `false` | Fail build when vulnerabilities are found at severity threshold |
| `container-commit-convention-enabled` | `false` | Enable convention-based build filtering |
| `container-commit-convention` | `clean-commit` | Commit convention for build filtering |
| `container-build-trigger-types` | `""` | Commit types that trigger container build |
| `container-build-skip-types` | `""` | Commit types that skip container build |
| `container-release-tag-pattern` | `^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$` | Regex pattern for release tags that trigger container build |
| `container-bot-detection` | `true` | Auto-detect bot actors and skip build |
| `container-bot-detection-mode` | `smart` | Identity source for bot detection (smart, actor, or pr-author) |
| `container-floating-tags` | `false` | Push a mutable floating tag for non-release builds |

### Package inputs

| Input | Default | Description |
|-------|---------|-------------|
| `package-registry` | `both` | Package registry target (npm, github, or both) |
| `package-dry-run` | `false` | Run package primitive in dry-run mode |
| `package-npm-registry-url` | `https://registry.npmjs.org` | npm registry URL |
| `package-github-registry-url` | `https://npm.pkg.github.com` | GitHub Packages registry URL |
| `package-scope` | `""` | Package scope for GitHub Packages |
| `package-path` | `./package.json` | Path to package manifest |
| `package-build-script` | `build` | Build script to run before publishing |
| `package-manager` | `auto` | Package manager to use (npm, yarn, pnpm, bun, auto). Bun is installed in the package job when selected, or when `auto` may resolve to it |
| `package-version-prefix` | `""` | Prefix for package version tags |
| `package-audit-enabled` | `true` | Enable package-manager-aware security scanning |
| `package-audit-level` | `high` | Minimum severity level for package security scanning |
| `package-fail-on-audit` | `false` | Fail package build when vulnerabilities are found |
| `package-pr-comment-enabled` | `true` | Enable PR comments with package install instructions |
| `package-pr-comment-template` | `""` | Custom PR comment template |
| `package-publish-enabled` | `true` | Enable publishing to package registry |
| `package-access` | `public` | Access level for scoped packages |
| `package-monorepo` | `false` | Enable monorepo mode |
| `package-paths` | `""` | Comma-separated package manifest paths (monorepo mode) |
| `package-workspace-detection` | `true` | Auto-detect workspaces from root package.json |
| `package-changed-only` | `true` | Only build/publish changed packages (monorepo mode) |
| `package-dependency-order` | `true` | Build packages in dependency order |
| `package-commit-convention-enabled` | `false` | Enable convention-based package build filtering |
| `package-commit-convention` | `clean-commit` | Commit convention for package build filtering |
| `package-build-trigger-types` | `""` | Commit types that trigger package build |
| `package-build-skip-types` | `""` | Commit types that skip package build |
| `package-bot-detection` | `true` | Auto-detect bots and fall back to validation-only mode |

### Release inputs

| Input | Default | Description |
|-------|---------|-------------|
| `release-changelog-path` | `./CHANGELOG.md` | Changelog path |
| `release-draft` | `false` | Create GitHub release as draft |
| `release-prerelease` | `false` | Mark GitHub release as prerelease |
| `release-dry-run` | `false` | Run release primitive in dry-run mode |
| `release-version-prefix` | `v` | Tag version prefix |
| `release-create` | `true` | Enable GitHub Release creation |
| `release-update-major-tag` | `false` | Move major version tag (`vN`) to new release |
| `release-initial-version` | `0.1.0` | Initial version when no tags exist |
| `release-prerelease-prefix` | `""` | Prefix for prerelease versions |
| `release-changelog-enabled` | `true` | Enable automatic changelog generation |
| `release-commit-type-mapping` | `""` | JSON mapping of commit types to changelog sections |
| `release-exclude-types` | `""` | Commit types to exclude from changelog |
| `release-exclude-scopes` | `""` | Commit scopes to exclude from changelog |
| `release-major-keywords` | `BREAKING CHANGE,BREAKING-CHANGE,breaking` | Keywords that trigger major bump |
| `release-minor-keywords` | `""` | Keywords that trigger minor bump |
| `release-patch-keywords` | `""` | Keywords that trigger patch bump |
| `release-release-name-template` | `{tag}` | Release name template |
| `release-git-user-name` | `WG Tech Labs` | Git user name for release commits |
| `release-git-user-email` | `262751631+wgtechlabs-automation@users.noreply.github.com` | Git user email for release commits |
| `release-commit-changelog` | `true` | Commit and push changelog changes |
| `release-sync-version-files` | `true` | Sync resolved version into manifest files |
| `release-version-file-paths` | `""` | Manifest file paths to update |
| `release-commit-convention` | `clean-commit` | Commit convention for generated commits |
| `release-tag-only` | `false` | Create tag only (skip GitHub Release) |
| `release-fetch-depth` | `0` | Number of commits to fetch for changelog (0 = full history) |
| `release-include-all-commits` | `false` | Include all commits in changelog |
| `release-monorepo` | `false` | Enable monorepo mode |
| `release-workspace-detection` | `true` | Auto-detect workspace packages |
| `release-change-detection` | `both` | Package change detection mode (scope, path, or both) |
| `release-scope-package-mapping` | `""` | JSON mapping of commit scopes to package paths |
| `release-per-package-changelog` | `true` | Generate `CHANGELOG.md` in each package directory |
| `release-root-changelog` | `true` | Generate aggregated root changelog |
| `release-cascade-bumps` | `false` | Automatically bump dependent packages (reserved) |
| `release-unified-version` | `false` | Use a single version for all packages |
| `release-monorepo-root-release` | `true` | Create a unified root release in monorepo mode |
| `release-package-manager` | `""` | Package manager for workspace detection |

## Required Secrets

When using `secrets: inherit`, Build Flow automatically picks up the following secrets from your repository or organization:

| Secret | Required when | Purpose |
|--------|--------------|---------|
| `DOCKER_HUB_USERNAME` | `enable-container: true` + `container-registry: docker-hub` or `both` | Docker Hub login username |
| `DOCKER_HUB_ACCESS_TOKEN` | `enable-container: true` + `container-registry: docker-hub` or `both` | Docker Hub access token |
| `GITLEAKS_LICENSE` | `enable-gitleaks: true` (default) | Gitleaks license key |
| `NPM_TOKEN` | `enable-package: true` + `package-registry: npm` or `both` | npm publish token |
| `CODECOV_TOKEN` | Coverage reporting enabled | Codecov upload token |
| `GHCR_TOKEN` | Optional override when `enable-container: true` + `container-registry: ghcr` or `both` | GHCR token override — uses built-in `GITHUB_TOKEN` when not set |

GHCR (GitHub Container Registry) authentication uses the built-in `GITHUB_TOKEN` automatically — no extra secret is needed unless you set `GHCR_TOKEN` to override it.

## Full Primitive Configuration

This example keeps Build Flow orchestration while tuning package, container, and release primitives directly through `app.yml` passthrough inputs.

```yaml
name: Build Flow

on:
  push:
    branches: [dev, main]
  pull_request:
    branches: [dev, main]

permissions:
  contents: write
  packages: write
  pull-requests: write
  security-events: write
  actions: read

jobs:
  build-flow:
    uses: wgtechlabs/build-flow-action/.github/workflows/app.yml@main
    secrets: inherit
    with:
      enable-package: true
      enable-container: true
      enable-release: true

      package-registry: both
      package-monorepo: true
      package-paths: "packages/core/package.json,packages/cli/package.json"

      container-registry: both
      container-dockerfile: ./ops/docker/Dockerfile
      container-context: ./apps/api
      container-floating-tags: true
      container-tag-prefix: api-

      release-monorepo: true
      release-unified-version: false
      release-per-package-changelog: true
      release-root-changelog: true
      release-sync-version-files: true
```

## Required Permissions

Build Flow's reusable workflows request the permissions their primitives need, but **a called workflow can never exceed the permissions of the caller**. If your caller workflow grants fewer scopes, the primitives' default features (PR comments, SARIF upload, npm/registry publish, release commits) are silently capped and fail. Declare the scopes you need in the caller:

| Permission | Required for |
|------------|--------------|
| `contents: write` | Release commits, tags, changelog (release flow) |
| `packages: write` | npm, GitHub Packages, and GHCR publishing |
| `pull-requests: write` | Default PR comments from the package/container primitives |
| `security-events: write` | CodeQL results and container Trivy SARIF upload |
| `actions: read` | CodeQL |

A CI-only caller (no publishing, no release) needs only the defaults. For a full app flow, use the block shown in [With Package and Container Publishing](#with-package-and-container-publishing).

## Ecosystem Relationship

Build Flow orchestrates these WG Technology Labs primitives:

- [`wgtechlabs/release-build-flow-action`](https://github.com/wgtechlabs/release-build-flow-action) — release automation
- [`wgtechlabs/package-build-flow-action`](https://github.com/wgtechlabs/package-build-flow-action) — package publishing (npm, GitHub Packages)
- [`wgtechlabs/container-build-flow-action`](https://github.com/wgtechlabs/container-build-flow-action) — container publishing (Docker Hub, GHCR)

You don't need to install these separately — Build Flow calls them internally with safe sequencing and policy gates, and now exposes their full configurable input surface through orchestration passthroughs.

## Security

Build Flow includes security scanning out of the box:

- **Gitleaks** — detects secrets committed to your repository (enabled by default)
- **CodeQL** — static analysis for vulnerabilities (enabled by default, language auto-detected)

Both are enabled by default. Gitleaks runs as part of the CI gate and blocks releases if secrets are detected. CodeQL runs as an independent security scan alongside the CI gate.

## Branch Strategy

Build Flow is designed for the [Clean Flow](https://github.com/wgtechlabs/clean-flow) workflow:

| Event | Behavior |
|-------|----------|
| PR to `dev` or `main` | CI + security gates + artifact publishing (enabled by default) |
| Push to `dev` | CI + artifact publishing (enabled by default) |
| Push to `main` | CI + version plan + publish enabled artifacts + finalize release when one publishes |
| Release published | CI + artifact publishing (release mode in container primitive) |
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

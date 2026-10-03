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
  packages: write          # GitHub Packages / GHCR
  id-token: write          # npm trusted publishing
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
      package-npm-auth-method: oidc
      enable-container: true      # opt-in: publish to Docker Hub/GHCR
      container-registry: docker-hub
      publish-dev-artifacts: false
      publish-pr-artifacts: false
      publish-manual-artifacts: false
```

Configure [npm trusted publishing](#npm-trusted-publishing) before the first publish. This example validates development changes and publishes artifacts only from eligible `main` pushes.

### CI-Only (no packaging or releases)

```yaml
jobs:
  ci:
    uses: wgtechlabs/build-flow-action/.github/workflows/ci.yml@main
    secrets: inherit
    with:
      ci-profile: auto
```

### Multiple Images, One Release

Set `container-images` to build distinct images with the same planned version and finalized source commit. Build Flow publishes one GitHub release only after every configured image publishes successfully. This does not require monorepo mode.

```yaml
with:
  enable-container: true
  container-registry: ghcr
  container-release-platforms: linux/amd64
  container-images: |
    [
      {"image-name": "my-app", "build-args": "SERVICE=app"},
      {"image-name": "my-browser", "build-args": "SERVICE=browser"}
    ]
```

Both images use the shared Dockerfile and build context; the Dockerfile must use the `SERVICE` build argument to select its app or browser stage. See the complete [multi-image example](examples/multi-image.yml) and [image definition schema](#image-definitions).

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
4. Source Finalization  → waits for CI + CodeQL, updates versions, and creates the release tag
  ├── 5a. Package Publishing   → consumes the planned version and finalized source
  ├── 5b. Container Publishing → all images consume the planned tag and finalized source
   └── 6. Release Publication  → creates GitHub Release LAST after every enabled artifact publishes
   CodeQL (after CI)     → required before source finalization or artifact publication
```

Default behavior (zero-config): CI + security on main. Enable a package or container flow to publish artifacts and finalize a release. When enabled (or when using `package.yml` / `container.yml` directly), artifact publishing defaults to allowed on main, dev, PR, manual, and published release events unless you set a `publish-*-artifacts` input to `false`.

An enabled CodeQL scan must succeed before source finalization or any artifact publishing. A deliberately disabled scan, or one with no detected languages, may be skipped. Failed or cancelled scans block publication.

Key behaviors:
- **Immutable main releases** — a dry-run release plan supplies one version to every planned artifact and finalization
- **Release is always last** — no public release until every enabled artifact job succeeds; packages must publish to every selected registry
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

`container.yml` delegates to `app.yml` with container publishing enabled. Its existing inputs and `artifact-published` output remain available; it also accepts `container-images` and shared Dockerfile, context, build argument, platform, and push settings. Use `app.yml` for the full primitive configuration, including custom container security options.

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
| `container-images` | `""` | Optional JSON array of image definitions; empty preserves the existing single-image inputs |
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

#### Image Definitions

`container-images` accepts a JSON array of 1–256 objects. Unknown keys and non-string values are rejected before release planning.

The resolved JSON, including shared defaults copied into each image, is limited to 900 KiB measured as UTF-16. This leaves room for policy outputs within [GitHub's job output limit](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idoutputs). Oversized configurations fail before builds start; use fewer images or smaller shared defaults.

| Field | Required | Behavior |
|-------|----------|----------|
| `image-name` | Yes | Unique lowercase image name, without a registry or tag; `app.backend` and `namespace/app` are valid, but `ghcr.io/org/app` and `localhost/app` are rejected |
| `dockerfile` | No | Inherits `container-dockerfile`; an explicit value must not be empty |
| `context` | No | Inherits `container-context`; an explicit value must not be empty |
| `build-args` | No | Inherits `container-build-args`; `""` clears shared arguments, `\n` separates arguments |
| `platforms` | No | Inherits `container-platforms`; an explicit value must not be empty |
| `release-platforms` | No | Inherits `container-release-platforms`; `""` uses this image's `platforms` |

Registry, tag, security, and publishing settings are shared across images. Leaving `container-images` empty retains single-image behavior; a one-item array also retains the existing skip and comment behavior.

With more than one image and pushing enabled, every image must report publication to at least one selected registry. A failed, cancelled, skipped, or unpublished image prevents the shared GitHub release. Bot detection or commit filtering that skips an image fails the requested publishing batch. Already-published images are not rolled back if another image fails.

For builds without publication, set `container-push-enabled: false`; this disables the batch publication requirement and prevents the GitHub release. On main, also set `release-dry-run: true` to run the build without finalizing the source and tag.

Multi-image builds disable the primitive's PR and vulnerability comments because concurrent images would update the same comment. Results remain in each job's logs and summary. SARIF categories receive per-image suffixes so scans remain separate. Single-image comments and categories are unchanged.

Container checks use the static base name `Container flow` so disabled or policy-skipped jobs remain readable before matrix expansion. GitHub appends matrix details to executed checks. The `Run container primitive (<image-name>)` step identifies each image; image details also remain in the logs and summary.

### Package inputs

Package GitHub Releases require a successful package job and publication to every registry selected by `package-registry`. For monorepos, every result must succeed in every selected registry; planned releases must also cover the exact planned package names and versions. The primitive's `artifact-published` output retains its meaning of publication to at least one registry. Partial publication blocks the GitHub Release but does not roll back packages already published.

| Input | Default | Description |
|-------|---------|-------------|
| `package-registry` | `both` | Package registry target (npm, github, or both) |
| `package-npm-auth-method` | `oidc` | npm authentication: `oidc` for trusted publishing or `token` for an `NPM_TOKEN`; ignored for GitHub-only publication |
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

### npm trusted publishing

`app.yml` and `package.yml` support automatic npm releases through GitHub Actions OIDC. The package job uses [Package Build Flow v2.3.0](https://github.com/wgtechlabs/package-build-flow-action/releases/tag/v2.3.0), pinned to `fac4cc6f61889fbc33849df87f20aa81a2a41bf2`. Use a Build Flow release or immutable commit containing `package-npm-auth-method`; upgrading the primitive alone does not upgrade an older Build Flow pin.

Before publishing:

1. Ensure the npm package exists. A new package needs the [one-time first publication](#first-publication-for-a-new-package) below.
2. In the package's npm settings, configure a GitHub Actions trusted publisher for the **calling repository and workflow filename**, such as `build.yml`. Use only the filename, not `.github/workflows/build.yml` or this repository's `app.yml`. Match the publishing job's environment if one is configured. Each package in a monorepo needs its own trust configuration.
3. Explicitly allow **`npm publish`** for that trusted publisher. Stage-only permission requires a maintainer's approval for each version; it does not permit unattended direct releases.
4. Grant `id-token: write` in the caller and select `package-npm-auth-method: oidc`. Keep `packages: write` when also publishing to GitHub Packages.

The package job installs Node **24.21.0** and npm **11.21.0** when OIDC is selected for npm or both registries. These exceed npm's minimum requirements of Node 22.14.0 and npm 11.5.1. This publication runtime is separate from the CI compatibility matrix. Bun remains available for installation, tests, builds, and packing; the npm CLI supplies the OIDC publication transport. Use GitHub-hosted runners. [npm setup requirements](https://docs.npmjs.com/trusted-publishers/)

The caller and reusable publishing job both need OIDC permission. The package job inherits the caller grant, including any additional scopes granted for other features; other jobs keep their own explicit permissions. Keep the caller permission map minimal and never use `write-all`. See the [permission tradeoff](docs/architecture.md#required-permissions-per-primitive). The package's `repository.url` must identify the calling GitHub repository. Configuring trust does not prove publication: verify the registry version and workflow results after the first run.

OIDC publication does not need `NPM_TOKEN`. GitHub Packages uses the built-in `GITHUB_TOKEN` and is separate from GHCR container publication. Installing private dependencies may require separate read credentials; npm publishing trust does not authorize installation. This input does not configure dependency credentials. Keep any required read credentials separate from publishing authentication.

#### Migrate existing workflows

When upgrading to a Build Flow revision that supports this input, set `package-npm-auth-method` explicitly in the same change. Older revisions reject the new input:

- **OIDC:** configure trust, add the caller permission, and set `package-npm-auth-method: oidc`. No npm publishing secret is required. Remove obsolete publishing credentials only after verifying the new path and checking whether other workflows still use them.
- **Token:** set `package-npm-auth-method: token` and provide `NPM_TOKEN` through repository/organization secrets or an explicit reusable-workflow secret mapping. npm still supports granular tokens subject to their permissions and package policy. A stage-only token cannot authorize this action's direct publish command.

For automatic production releases, set `publish-dev-artifacts`, `publish-pr-artifacts`, and `publish-manual-artifacts` to `false`, as in the examples. CI and security checks still validate those events. OIDC changes authentication; it does not change the requirement for every selected registry and the complete package job to succeed before the GitHub Release.

#### First publication for a new package

npm requires an existing package before [configuring its trusted publisher](https://docs.npmjs.com/cli/v11/commands/npm-trust/). Build and review the initial tarball, then have a maintainer publish it once using interactive npm login and 2FA:

```sh
npm login --registry=https://registry.npmjs.org
npm publish ./path/to/reviewed-package.tgz --access public --registry=https://registry.npmjs.org
```

Verify the published version, configure trust, and use OIDC for subsequent versions. Do not retry the already published version. If a version was published to only one selected registry, recover the missing registry separately before creating its GitHub Release; publication is not atomic.

A staged first publication followed by maintainer approval is also possible. Build Flow uses direct publication and does not implement staging or approval polling. Keep account 2FA enabled; npm's setting to disallow traditional publishing tokens is compatible with a trusted publisher allowed to run `npm publish`.

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
| `NPM_TOKEN` | Package publishing to npm or both registries with `package-npm-auth-method: token` | npm granular token with direct publishing permission; not required for OIDC |
| `CODECOV_TOKEN` | Coverage reporting enabled | Codecov upload token |
| `GHCR_TOKEN` | Optional override when `enable-container: true` + `container-registry: ghcr` or `both` | GHCR token override — uses built-in `GITHUB_TOKEN` when not set |

GHCR (GitHub Container Registry) authentication uses the built-in `GITHUB_TOKEN` automatically — no extra secret is needed unless you set `GHCR_TOKEN` to override it.

GitHub Packages also uses the built-in `GITHUB_TOKEN`. `GHCR_TOKEN` is a container credential override, not an npm or GitHub Packages credential.

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
  id-token: write
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
      package-npm-auth-method: oidc
      package-monorepo: true
      package-paths: "packages/core/package.json,packages/cli/package.json"
      publish-dev-artifacts: false
      publish-pr-artifacts: false
      publish-manual-artifacts: false

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

Build Flow's reusable workflows request the permissions their primitives need, but **a called workflow can never exceed the permissions of the caller**. Missing caller permissions can prevent the called workflow from starting or cause an operation to fail. Declare the scopes needed by your enabled features:

| Permission | Required for |
|------------|--------------|
| `contents: write` | Release commits, tags, changelog (release flow) |
| `packages: write` | GitHub Packages and GHCR publishing; does not authorize npm |
| `id-token: write` | npm trusted publishing when `package-npm-auth-method: oidc` and npm is selected |
| `pull-requests: write` | Default PR comments from the package/container primitives |
| `security-events: write` | CodeQL results and container Trivy SARIF upload |
| `actions: read` | CodeQL |

A CI-only or container-only caller does not need OIDC permission for this feature. For a full app flow, use the block shown in [With Package and Container Publishing](#with-package-and-container-publishing).

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

Both are enabled by default. Gitleaks runs as part of the CI gate and blocks releases if secrets are detected. CodeQL runs after the CI gate and must succeed before source finalization or artifact publication. A disabled scan or one with no detected languages may be skipped; a failed or cancelled scan blocks publication.

## Branch Strategy

Build Flow is designed for the [Clean Flow](https://github.com/wgtechlabs/clean-flow) workflow:

| Event | Behavior |
|-------|----------|
| PR to `dev` or `main` | CI + security gates + artifact publishing (enabled by default) |
| Push to `dev` | CI + artifact publishing (enabled by default) |
| Push to `main` | CI + CodeQL gates + version plan + finalize source + publish enabled artifacts + GitHub Release after every selected package registry and enabled artifact job succeeds |
| Release published by a user | CI + artifact publishing (release mode in container primitive) |
| Bot-authored release publication | Skipped to prevent a duplicate artifact build |
| Manual dispatch | Configurable operational/recovery scenarios |

## Examples

See the [`examples/`](examples/) directory for complete workflow files:

- [`examples/app.yml`](examples/app.yml) — full orchestration (Node/Bun project)
- [`examples/minimal.yml`](examples/minimal.yml) — zero-config auto-detect
- [`examples/ci-only.yml`](examples/ci-only.yml) — CI validation only
- [`examples/package-only.yml`](examples/package-only.yml) — package flow (Node.js project)
- [`examples/container-only.yml`](examples/container-only.yml) — container flow (C/C++ project)

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — design philosophy and orchestration model
- [`docs/roadmap.md`](docs/roadmap.md) — planned features and improvements

## License

MIT

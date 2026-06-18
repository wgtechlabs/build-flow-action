# Build Flow Action Architecture

This document is the single source of truth for how `build-flow-action` works and the rules it must follow. It is written for both human contributors and AI agents working on this repository. Read it before changing any workflow under `.github/workflows/`.

## Purpose

`build-flow-action` is the flagship **orchestration layer** for WG Technology Labs build and release automation.

It gives end users a **single entrypoint** so they no longer have to hand-wire separate workflows for CI, packaging, containerization, and release creation. Instead of asking each repository to compose multiple workflow files and reason about job ordering, this project owns the safe sequencing of the full build-and-release lifecycle.

It does **not** reimplement build, publish, or release logic. That logic lives in three lower-level "primitive" actions. This project only **coordinates** them.

## The primitives

`build-flow-action` orchestrates three independent, separately versioned primitive actions. Each one is a complete product on the GitHub Marketplace and owns its own defaults and behavior.

| Primitive | Role | Pinned version (SHA) | Tag |
|-----------|------|----------------------|-----|
| [`wgtechlabs/release-build-flow-action`](https://github.com/wgtechlabs/release-build-flow-action) | Version bump, changelog, tag, GitHub Release | `caae411` | v1.7.0 |
| [`wgtechlabs/package-build-flow-action`](https://github.com/wgtechlabs/package-build-flow-action) | Publish packages (npm, GitHub Packages) | `999bc41` | v2.1.2 |
| [`wgtechlabs/container-build-flow-action`](https://github.com/wgtechlabs/container-build-flow-action) | Build and publish containers (Docker Hub, GHCR) | `7df0af8` | v1.8.1 |

All three are pinned by exact commit SHA (with a trailing version comment) in the reusable workflows. Bumping a primitive means updating the SHA **and** re-running the parity audit described below.

## Core principles

Two rules govern every design decision in this repository.

### Principle 1 — Build first, release last

A public release must be the **final** step, never the first. The orchestration always follows:

1. Prepare build context.
2. Run CI and required quality/security gates.
3. Build and publish the required artifacts (package, container).
4. Verify everything succeeded.
5. Only then create the tag and the GitHub Release.

This eliminates the original production failure mode: a release being published first, the public release becoming visible, and the artifact build then failing — leaving a release with no artifacts behind it. The orchestration never relies on the `release` event as the trigger that produces artifacts.

### Principle 2 — Never override primitive defaults

Each primitive's author deliberately chose its defaults and must-have behavior. **This orchestration must preserve those defaults, never silently suppress or re-assert them.**

Concretely:

- If a primitive default is correct as-is, the orchestration **does not forward a value for it at all** — the primitive's own default governs. Forwarding a value that merely repeats the default is still a form of pinning: if the primitive later changes its default, the orchestration would silently freeze the old one. So we leave it alone.
- The orchestration only forwards a value when that value is part of **its own configurable surface** (an input a consumer is expected to set) **and** its default exactly matches the primitive's default.
- A value-level divergence from a primitive default is a bug. Historically these crept in one at a time and had to be patched repeatedly; this document and the parity reference exist to stop that.

Example: `release-build-flow-action` defaults `sync-version-files` to `true` (it syncs the resolved version into `package.json`, `Cargo.toml`, etc.). The orchestration **does not pass `sync-version-files`** — the primitive's `true` default governs untouched. We do not expose or re-assert it.

## The override surface

There are exactly **three** mechanisms through which the orchestration can break a primitive default. Audit all three whenever a primitive is bumped or a workflow is edited.

1. **Policy gate + event triggers.** The `context`/policy job decides whether a flow runs. A missing event trigger (for example `release: published`) or a too-strict gate can suppress a flow the primitive would otherwise run.
2. **Job permissions.** Reusable-workflow job permissions are **capped by the caller**. A missing scope makes a primitive's default feature (PR comments, SARIF upload, registry publish, release commit) fail or silently no-op.
3. **Forwarded input values.** Every value forwarded to a primitive must equal that primitive's default unless the consumer deliberately overrode it. The cleanest way to honor a default is to not forward it at all (see Principle 2).

## Integration model

The primary model is **reusable-workflow-first**. Consumers call the reusable workflows under `.github/workflows/`:

- `app.yml` — full orchestration (CI gate, CodeQL, package, container, release).
- `package.yml` — package-focused flow (CI gate, CodeQL, package, release).
- `container.yml` — container-focused flow (CI gate, CodeQL, container, release).
- `ci.yml` — CI/validation only (lint, typecheck, test, build, Gitleaks).
- `codeql.yml` — CodeQL security scan, called by the flows above.

A thin wrapper action exists at the repo root, but reusable workflows are preferred because they support multi-job orchestration, `needs` dependency graphs, per-job permission boundaries, and isolated release stages.

## Execution flow

Each flow runs the same staged model:

1. **Detect context.** A policy job classifies the event — pull request, push to `dev`, push to `main`, manual dispatch, or release — and decides which flows are allowed to publish and whether the release may finalize.
2. **Run gates.** The CI gate (lint/typecheck/test/build, profile-driven) plus Gitleaks; CodeQL runs as an independent scan.
3. **Build and publish artifacts.** Package and/or container flows run when enabled and allowed by policy.
4. **Finalize release (last).** The release job runs only after the gates and required artifact jobs succeed.

## Branch and event model

- **Pull request** → run CI and preview checks; do not publish a production release.
- **Push to `dev`** → run CI; optionally publish development artifacts; no production release.
- **Push to `main`** → run CI and gates; prepare version/release metadata; publish required artifacts; finalize the release only after success.
- **Release (`published`)** → allow artifact publishing on release events (so a manually published release can still produce artifacts). The orchestration does not depend on this event as the sole production trigger.
- **Manual dispatch / unknown events** → resolve to the primitives' own `wip` flow.

## Primitive parity reference

This is the canonical record of what each primitive requires so the orchestration does not drift.

### Required permissions per primitive

Because reusable-workflow permissions are bounded by the caller, **example/consumer caller workflows must declare these scopes too** — otherwise the primitive defaults are silently capped.

| Primitive | contents | packages | pull-requests | security-events | actions |
|-----------|----------|----------|---------------|-----------------|---------|
| package   | write    | write    | write (PR comments default on) | – | – |
| container | write    | write    | write (PR comments default on) | write (SARIF) | – |
| release   | write    | –        | – | – | – |
| codeql gate | read   | –        | – | write | read |

### Required secrets / checkout per primitive

- **package** — `npm-token` (`secrets.NPM_TOKEN`) is mandatory when `registry` includes npm (default `both`); the primitive hard-fails without it. The package primitive checks out its own repo internally (`fetch-depth: 0`) when no manifest is present, so the package job needs no external checkout.
- **container** — `dockerhub-username` / `dockerhub-token` for Docker Hub (default registry `both`). The container job **must** check out the repo and **must** run `docker/setup-qemu-action` before the primitive, because the default `release-platforms` is multi-arch (`linux/amd64,linux/arm64`) and the primitive sets up buildx without QEMU.
- **release** — requires `actions/checkout` with `fetch-depth: 0` before it runs (it reads full git history via `git log tag..HEAD`). Every workflow that finalizes a release must include this checkout.

### Must-have defaults preserved (do not override)

- **package** — dual-registry publish, `pr-comment-enabled`, branch-aware flow detection.
- **container** — dual-registry, Trivy source/dockerfile/image scans, SARIF upload, SBOM, provenance, bot-detection, PR comments.
- **release** — `sync-version-files: true` (auto-syncs manifest versions — left to the primitive, not forwarded), `commit-changelog: true`, `create-release: true`, `commit-convention: clean-commit`; the first release patch-bumps from `initial-version`.

### Consumer-facing passthroughs

These are the only release-primitive toggles the orchestration deliberately exposes, and each default matches the primitive default so nothing is overridden:

- `release-update-major-tag` → `update-major-tag` (default `false` = primitive default). Lets action-repo consumers opt into moving the floating `vN` tag, which they cannot otherwise reach through the orchestration.

## Intentional design choices (by design — not bugs)

These behaviors look like divergences but are deliberate. Do not "fix" them back.

- **The policy gate is stricter than a primitive run in isolation.** The orchestration adds its own convention/branch gate and "build first, release last" sequencing on top of the primitives' own branch-aware detection. This safe-sequencing layer is the orchestration's reason to exist.
- **`workflow_dispatch` and unknown events resolve to the `wip` flow.** This is the primitives' own behavior, preserved here.
- **`sync-version-files` is left entirely to the release primitive.** It is `true` by default at the primitive level and the orchestration never forwards it (see Principle 2).
- **GitHub releases created with `GITHUB_TOKEN` do not trigger downstream `release:`-triggered workflows.** This is a GitHub platform behavior. The orchestration handles it by publishing artifacts before finalizing the release rather than relying on the `release` event.

## What this project must avoid

- Publishing a GitHub Release before its artifacts exist.
- Depending on the `release` event as the sole production-artifact trigger.
- Forwarding a value that diverges from a primitive default (silent override).
- Capping primitive permissions by omitting required scopes from caller workflows.

If a release is visible publicly, the required production artifacts must already have been built and published successfully.

## Repository structure

### Root documentation
- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `LICENSE`

### Architecture and planning docs
- `docs/architecture.md` (this file)
- `docs/roadmap.md`

### Reusable workflow entrypoints
- `.github/workflows/ci.yml`
- `.github/workflows/app.yml`
- `.github/workflows/package.yml`
- `.github/workflows/container.yml`
- `.github/workflows/codeql.yml`

### Usage examples
- `examples/minimal.yml`
- `examples/app.yml`
- `examples/ci-only.yml`
- `examples/package-only.yml`
- `examples/container-only.yml`

## Design goals

This project is:

- **opinionated** enough to be safe by default,
- **simple** enough for end users to adopt quickly,
- **modular internally** so it keeps using the WG Technology Labs primitives rather than reimplementing them,
- **faithful** to every primitive default (Principle 2),
- **extensible** for future improvements such as monorepo support and advanced release modes,
- **clear in contract** so each workflow stage has a well-defined responsibility.

## Decision summary

`build-flow-action` exists to convert a set of separate build/release/package/container primitives into a single safe orchestration product, while preserving each primitive's own defaults.

Its two defining rules are:

> **Build and validate first. Release last.**
>
> **Never override a primitive's own defaults.**

Everything in this repository should reinforce both.

# Build Flow Action Architecture

## Purpose

`build-flow-action` is the flagship orchestration layer for WG Technology Labs build and release automation.

Its purpose is to provide a **single entrypoint** for end users so they no longer need to manually compose separate workflows for CI, release creation, package publishing, and container publishing.

Instead of asking repository maintainers to wire multiple workflow files together, this project owns the orchestration and safe sequencing of the full build and release lifecycle.

## Problem Statement

The current ecosystem provides strong low-level building blocks:

- `wgtechlabs/release-build-flow-action`
- `wgtechlabs/package-build-flow-action`
- `wgtechlabs/container-build-flow-action`

However, users still need to manually configure these actions across multiple workflow files such as:

- `ci.yml`
- `release.yml`
- `container.yml`
- package-related workflows

This creates several problems:

1. **Too much manual workflow composition**  
   End users must understand job dependencies, triggers, and release timing.

2. **Unsafe orchestration**  
   A release can be published before required artifacts are built and successfully published.

3. **Contract mismatch risk**  
   Independent low-level actions can drift in behavior or assumptions, causing broken release chains.

4. **Poor default experience**  
   Users can easily assemble a technically valid but operationally unsafe release flow.

## Concrete Failure Mode We Are Solving

A key failure already observed in production-like repositories was this sequence:

1. A push to `main` triggered a release workflow.
2. The release workflow published a GitHub Release first.
3. The published release triggered a container workflow via the `release` event.
4. The downstream container action failed because the release event path was unsupported.
5. The public GitHub Release remained visible even though the production artifact was missing.

This is the core anti-pattern this project is designed to eliminate.

## Core Architectural Principle

### Build first, release last.

`build-flow-action` must ensure that public release publication is the **final** step of the process, not the first.

The orchestration model should always prefer:

1. prepare build context
2. run CI and quality gates
3. build and publish required artifacts
4. validate success
5. create tag and GitHub Release last

This protects repositories from false releases, partial releases, and broken production artifact states.

## Product Role

`build-flow-action` is the **umbrella orchestrator** over the existing WG Technology Labs primitives.

### Existing primitives

- `release-build-flow-action` → release automation primitive
- `package-build-flow-action` → package publishing primitive
- `container-build-flow-action` → container publishing primitive

### New role of this repository

This repository provides the orchestration layer that coordinates those primitives into a single safe workflow system.

The goal is to make this the default recommended product for most users, while preserving the lower-level actions for advanced or highly customized use cases.

## Intended User Experience

The end user should not need to manually stitch together separate release, package, and container workflows.

The intended experience is:

1. install one workflow
2. configure a small number of inputs
3. push and merge changes normally
4. let `build-flow-action` coordinate the lifecycle automatically

This project should reduce setup burden while increasing operational safety.

## Integration Model

The primary integration model should be **reusable-workflow-first**.

That means users should consume this project mainly through reusable workflows under `.github/workflows/`, for example:

- `app.yml`
- `package.yml`
- `container.yml`

A thin wrapper action may exist if useful, but reusable workflows are the preferred model because they better support:

- multi-job orchestration
- dependency graphs with `needs`
- permission boundaries
- isolated release stages
- flexible branch/event handling

## Orchestration Responsibilities

`build-flow-action` should own the sequencing and policy of the following concerns:

- CI gates
- optional security gates such as CodeQL
- version preparation
- changelog preparation
- package publishing
- container publishing
- tag creation
- GitHub Release finalization
- workflow summaries and outputs

Users should specify intent and capabilities, not rebuild orchestration logic themselves.

## High-Level Flow Model

The preferred orchestration sequence is:

1. **Detect context**
   - pull request
   - push to `dev`
   - push to `main`
   - manual dispatch

2. **Prepare release/build metadata**
   - version candidate
   - changelog context
   - release naming
   - artifact tagging context

3. **Run CI and required gates**
   - secrets scan (Gitleaks)
   - CodeQL scan
   - profile-driven validate commands (lint/typecheck/test/build)

4. **Build and publish artifacts**
   - package artifacts if enabled
   - container artifacts if enabled

5. **Finalize release**
   - only after all required gates and artifacts succeed
   - create tag
   - create GitHub Release

## Branch and Event Philosophy

This repository should support an opinionated but configurable branch model.

Typical expected behavior:

### Pull requests
- run CI
- run preview checks
- do not publish a production release

### Push to `dev`
- run CI
- optionally publish development artifacts
- do not create a production release

### Push to `main`
- run CI and required gates
- prepare version and release metadata
- publish required production artifacts
- finalize release only after success

### Manual dispatch
- support controlled operational or recovery scenarios

## What This Project Must Avoid

The architecture should explicitly avoid the previous broken pattern:

- publishing a GitHub Release first
- depending on the `release` event as the sole production artifact trigger
- separating artifact publication from release finalization in a way that creates false public releases

If a release is visible publicly, the system should have already produced the required production artifacts successfully.

## Project Structure Direction

The repository should be scaffolded around the following types of assets:

### Root documentation
- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `LICENSE`

### Architecture and planning docs
- `docs/architecture.md`
- `docs/roadmap.md`

### Reusable workflow entrypoints
- `.github/workflows/ci.yml`
- `.github/workflows/app.yml`
- `.github/workflows/package.yml`
- `.github/workflows/container.yml`

### Usage examples
- `examples/app.yml`
- `examples/package-only.yml`
- `examples/container-only.yml`

## Design Goals

This project should be:

- **opinionated** enough to be safe by default
- **simple** enough for end users to adopt quickly
- **modular internally** so it can continue using WGTechLabs primitives
- **extensible** for future improvements such as monorepo support and advanced release modes
- **clear in contract** so each workflow stage has a well-defined responsibility

## Non-Goals for the Initial Scaffold

The initial scaffold does **not** need to fully implement the entire orchestration engine.

It only needs to establish:

- the correct product direction
- the correct architectural philosophy
- the correct workflow sequencing model
- the correct repository structure for future implementation

## Decision Summary

`build-flow-action` exists to convert a set of separate build/release/package/container primitives into a single safe orchestration product.

Its defining rule is simple:

> **Build and validate first. Release last.**

Everything in this repository should reinforce that rule.

## Primitive Parity Reference

This project orchestrates three primitives. Each primitive ships its own **default / must-have behavior**, and the orchestration must preserve those defaults rather than silently suppress them. This section is the canonical record of what each primitive expects so the orchestration does not drift again.

Pinned versions (by exact commit SHA in the workflows):

| Primitive | Version | Tag |
|-----------|---------|-----|
| `wgtechlabs/container-build-flow-action` | `7df0af8` | v1.8.1 |
| `wgtechlabs/package-build-flow-action` | `999bc41` | v2.1.2 |
| `wgtechlabs/release-build-flow-action` | `caae411` | v1.7.0 |

### The override surface

Whenever the orchestration can break a primitive default, it happens through exactly one of three mechanisms. Audit these three whenever a primitive is bumped:

1. **Policy gate + event triggers** — the `context`/policy job decides whether a flow runs. A missing event (e.g. `release: published`) or a too-strict gate suppresses a default flow.
2. **Job permissions** — reusable-workflow job permissions are capped by the caller. Missing scopes make the primitive's default features (PR comments, SARIF upload, publish, release commit) fail or silently no-op.
3. **Forwarded input values** — every value forwarded to a primitive must equal that primitive's own default unless a deliberate override is intended. Today no input value diverges from primitive defaults.

### Required permissions per primitive

| Primitive | contents | packages | pull-requests | security-events | actions |
|-----------|----------|----------|---------------|-----------------|---------|
| package   | write    | write    | write (PR comments default on) | – | – |
| container | write    | write    | write (PR comments default on) | write (SARIF) | – |
| release   | write    | –        | – | – | – |
| codeql gate | read   | –        | – | write | read |

Because reusable-workflow permissions are bounded by the caller, **example caller workflows must declare these scopes too** — otherwise the primitive defaults are silently capped.

### Required secrets / inputs per primitive

- **package**: `npm-token` (`secrets.NPM_TOKEN`) is mandatory when `registry` includes npm (default `both`); the primitive hard-fails without it. The package primitive checks out its own repo internally (`fetch-depth: 0`) when no manifest is present, so the package job needs no external checkout.
- **container**: `dockerhub-username` / `dockerhub-token` for Docker Hub (default registry `both`). The container job **must** check out the repo and **must** run `docker/setup-qemu-action` before the primitive, because the default `release-platforms` is multi-arch (`linux/amd64,linux/arm64`) and the primitive sets up buildx without QEMU.
- **release**: requires `actions/checkout` with `fetch-depth: 0` before it runs (it reads full git history via `git log tag..HEAD`). Every workflow that finalizes a release must include this checkout.

### Must-have defaults preserved (do not override)

- Package: dual-registry publish, `pr-comment-enabled`, branch-aware flow detection.
- Container: dual-registry, Trivy source/dockerfile/image scans, SARIF upload, SBOM, provenance, bot-detection, PR comments.
- Release: `sync-version-files: true` (auto-syncs manifest versions), `commit-changelog: true`, `create-release: true`, `commit-convention: clean-commit`, first release patch-bumps from `initial-version`.

### Intentional divergences (by design — documented, not bugs)

- **`update-major-tag` defaults to `false`** in the release primitive. The orchestration exposes a passthrough input `release-update-major-tag` (default `false` to match the primitive). Action-repo consumers that want the floating `vN` tag to move should set it to `true`.
- **WIP-flow gate**: the orchestration applies its own convention/branch gate before primitives, which is stricter than a primitive run in isolation.
- **`workflow_dispatch` and unknown events** resolve to the primitives' `wip` flow.
- **GitHub releases created with `GITHUB_TOKEN`** do not trigger downstream `release:`-triggered workflows; the orchestration sequences artifact publishing before release finalize so it does not rely on the `release` event as the sole production trigger.

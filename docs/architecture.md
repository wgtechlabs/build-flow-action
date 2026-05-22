# Architecture

## Product Role

`build-flow-action` is the umbrella orchestration layer for WG Technology Labs build-flow primitives.

It is designed to expose one public integration surface (reusable workflows) while coordinating internal release, package, and container actions in a safe sequence.

## Orchestration Model

Primary integration: reusable workflows under `.github/workflows/`.

High-level sequence:

1. Prepare context and validate inputs.
2. Build and test first.
3. Publish package and/or container artifacts only after successful build gates.
4. Finalize GitHub release last.

## Safety Rules

- Never make release publication the first production event.
- Treat package/container publication as dependent steps, not standalone release triggers.
- Keep release finalization blocked on upstream job success.

## Reusable Workflow Entrypoints

- `app.yml` — full app orchestration (CI + optional package/container + release)
- `package.yml` — package-focused orchestration
- `container.yml` — container-focused orchestration

## Internal Relationship to Existing WGTechLabs Actions

- `release-build-flow-action` handles release metadata and final release publication.
- `package-build-flow-action` handles package build/publish concerns.
- `container-build-flow-action` handles container build/publish concerns.

This repository orchestrates those primitives with opinionated defaults and a safer execution order.

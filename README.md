# Build Flow Action

An opinionated all-in-one build and release automation framework for GitHub repositories.

## Overview

`build-flow-action` is the umbrella orchestration layer for WG Technology Labs build automation.
It is designed to coordinate CI, package publishing, container publishing, versioning, changelog generation, and final release creation using safe sequencing.

## Goals

- provide one entrypoint for end users
- reduce manual workflow composition
- make release publication the final step, not the first
- unify package, container, and release flows
- expose safe defaults with optional advanced overrides

## Current Status

This repository is currently being scaffolded.

## Planned Structure

- reusable workflows under `.github/workflows/`
- optional wrapper action entrypoint
- examples for app, package-only, and container-only repositories
- architecture and migration docs

## Ecosystem

This project is intended to orchestrate:

- `wgtechlabs/release-build-flow-action`
- `wgtechlabs/package-build-flow-action`
- `wgtechlabs/container-build-flow-action`

## License

MIT

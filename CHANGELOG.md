# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial scaffold for Build Flow Action repository.
- Reusable workflow entrypoints for app, package-only, and container-only modes.
- Architecture and roadmap documentation.
- Example consumer workflows.
- Unified reusable CI gate workflow with profile resolution, Gitleaks, CodeQL, and customizable validation commands.
- Self-test workflow to validate own reusable workflows and release flow.
- `ci-runs-on` input for custom runner labels (macOS, Windows, self-hosted).
- `ci-runtime-version` input for pinning runtime version without matrix.
- Rust profile with `Cargo.toml` auto-detection, `cargo build/test/clippy` defaults.
- Default commands for Python (`pip install`, `pytest`), Go (`go build/test`), Java (`gradlew/mvn`), and C/C++ (`cmake/ctest`) profiles.
- Dependency caching for Node (npm), Python (pip), and Go.
- `.nvmrc` and `.node-version` file support for Node.js version pinning.

### Fixed

- Release job condition in `app.yml` referencing wrong job name and non-existent `codeql` dependency.
- Self-test release trigger now finalizes release on merged pull requests targeting `main`.
- `custom` profile incorrectly defaulting CodeQL language to `javascript-typescript`.
- CodeQL gate now correctly skipped when resolved language is empty.
- Gitleaks action pinned to commit SHA for supply chain consistency.

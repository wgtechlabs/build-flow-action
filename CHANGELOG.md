# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.1.5] - 2026-06-17

### Changed

- default publish-artifact gates to true (#24)

## [0.1.4] - 2026-06-17

### Changed

- correct default values for enable-package, enable-container, and enable-release (#22)

## [0.1.3] - 2026-06-17

### Changed

- pass docker hub credentials and add checkout to container flow (#20)

## [0.1.2] - 2026-06-16

### Changed

- use full clone for gitleaks scan (#19)
- update CHANGELOG.md for v0.1.1
- promote dev to main (#15)

## [0.1.1] - 2026-06-06

### Changed

- add branding icon and color

## [0.1.0] - 2026-06-06

### Added

- add landing page and github pages deployment (#9)

### Changed

- use v1 release action and remove CI gate
- replace build flow with release workflow (#13)
- detect merged PRs in CI workflows for correct branch detection (#12)
- add testing skill for Build Flow Action landing page (#10)
- remove error suppression from test and lint commands
- rename workflow to Build Flow Dogfood and update permissions
- enhance README with production safety guidelines for workflows
- clarify changelog editing guidelines in contributing guide
- update README with GitHub Repo Banner
- improve adoption guide with clear getting started and examples (#8)
- extract CodeQL into separate reusable workflow
- rename workflow and fix validate job naming
- consolidate CI jobs to reduce skipped noise
- fix gitleaks license passthrough and disable in dogfood
- add missing permissions for CodeQL in caller workflows
- make ci.yml generic for any project and ecosystem (#6)
- unify reusable CI gate and enforce security-first orchestration (#3)
- add copilot and clean commit instructions
- update examples and documentation for workflows
- update GitHub actions workflows with new inputs
- scaffold reusable-workflow-first foundation for build-flow-action (#1)
- add architecture guide for build-flow-action
- add contributing guide scaffold
- add changelog scaffold
- add MIT license
- add initial README scaffold

### Security

- harden workflows against injection, pin actions, tighten permissions (#4)


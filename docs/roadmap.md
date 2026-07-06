# Roadmap

## Completed

- Reusable workflow-first entrypoints (`app`, `ci`, `package`, `container`, `codeql`)
- Example integration workflows for end users
- Baseline architecture and contribution docs
- Safe sequencing contract (release last)
- Wired reusable workflows to WG Technology Labs primitive actions
- CI gate with profile-based ecosystem detection (node, node-bun, python, go, rust, java, c-cpp, custom)
- CodeQL security scanning (extracted into standalone reusable workflow)
- Gitleaks secret detection integrated into CI gate
- Matrix version validation support
- Dependency caching (npm, pip, Go)
- Custom runner support (`ci-runs-on`)
- `.nvmrc` / `.node-version` file support for Node.js version pinning
- PR check noise reduction (consolidated from 10 checks to 2-3 visible entries)
- Full primitive input passthrough for `container-build-flow-action`, `release-build-flow-action`, and `package-build-flow-action` via orchestration workflows
- Monorepo package publishing and monorepo release mode exposed via `package-monorepo` and `release-monorepo`
- Floating container tags (`@dev`, `@pr`, `@wip`) exposed via `container-floating-tags`

## Current Iteration

- Production-grade input validation and summaries
- Branch strategy defaults (`dev` + `main`) fully implemented
- Clear migration guidance from manually composed workflows
- Comprehensive usage documentation and examples

## Future

- Input validation and guard-rail summaries for misconfigured primitive input combinations
- First-class examples for monorepo and floating-tag configurations
- Additional registry and deployment integration options
- Version pinning and tagged releases for stable consumer adoption

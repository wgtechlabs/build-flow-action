$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$mainBranch = 'main'
$isMainPush = 'push' -eq 'push' -and 'refs/heads/main' -eq "refs/heads/$mainBranch"
$isMergedPullRequest = 'pull_request' -eq 'push' -and 'refs/pull/41/merge' -eq "refs/heads/$mainBranch"

if (-not $isMainPush -or $isMergedPullRequest) {
  throw 'Only a push to main can select artifact-first release orchestration'
}

$contracts = @{
  'app.yml' = @(
    'wgtechlabs/release-build-flow-action@5e43e8a06d9ea39d2dac5c0246a018f29fe0b635',
    'wgtechlabs/container-build-flow-action@7779e7cc816a1eaa3f5c34ce6c7e584455ca3572',
    'wgtechlabs/package-build-flow-action@3632392ecc4651713babb4ebc430596724f1a231',
    'version-plan:', 'planned-version-tag:', 'planned-version-bump-type:', 'artifact-published:'
  )
  'package.yml' = @(
    'wgtechlabs/release-build-flow-action@5e43e8a06d9ea39d2dac5c0246a018f29fe0b635',
    'wgtechlabs/package-build-flow-action@3632392ecc4651713babb4ebc430596724f1a231',
    'version-plan:', 'planned-version:', 'planned-npm-tag:', 'artifact-published:'
  )
  'container.yml' = @(
    'wgtechlabs/release-build-flow-action@5e43e8a06d9ea39d2dac5c0246a018f29fe0b635',
    'wgtechlabs/container-build-flow-action@7779e7cc816a1eaa3f5c34ce6c7e584455ca3572',
    'version-plan:', 'planned-version-tag:', 'artifact-published:'
  )
}

foreach ($flow in $contracts.Keys) {
  $path = Join-Path $root ".github\workflows\$flow"
  $content = Get-Content -Raw $path

  foreach ($required in $contracts[$flow]) {
    if ($content -notmatch [regex]::Escape($required)) {
      throw "$flow must contain $required"
    }
  }

  foreach ($required in @(
    'concurrency:',
    'group: build-flow-release-${{ github.repository }}-${{ inputs.main-branch }}',
    "needs.context.outputs.is-main == 'true'",
    'if [[ "$GH_EVENT_NAME" == "push" && "$GH_REF" == "refs/heads/$INPUT_MAIN_BRANCH" ]]; then'
  )) {
    if ($content -notmatch [regex]::Escape($required)) {
      throw "$flow must contain $required"
    }

    if ($content -match '\$GH_BASE_REF" == "\$INPUT_MAIN_BRANCH') {
      throw "$flow must not classify merged pull requests as main release candidates"
    }
  }

  if ($flow -eq 'app.yml') {
    $prereleasePrefix = 'prerelease-prefix: ${{ inputs.release-prerelease-prefix }}'
    if (([regex]::Matches($content, [regex]::Escape($prereleasePrefix))).Count -ne 1) {
      throw 'app.yml must only pass prerelease-prefix to the version plan'
    }
    if ($content -notmatch [regex]::Escape('planned-package-versions: ${{ inputs.release-monorepo && needs.version-plan.outputs.planned-packages-updated || '''' }}')) {
      throw 'app.yml must pass monorepo package versions from the release plan'
    }
  }

  if ($flow -eq 'package.yml') {
    foreach ($required in @(
      'release-monorepo:',
      'release-unified-version:',
      'planned-packages-updated: ${{ steps.release.outputs.packages-updated }}',
      'planned-package-versions: ${{ inputs.package-monorepo && inputs.release-monorepo && needs.version-plan.outputs.planned-packages-updated || '''' }}'
    )) {
      if ($content -notmatch [regex]::Escape($required)) {
        throw "package.yml must contain $required"
      }
    }
  }
}

Write-Output 'Workflow contracts passed'

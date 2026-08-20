$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$mainBranch = 'main'

function Test-MainReleaseCandidate {
  param(
    [string]$EventName,
    [string]$Ref,
    [string]$BaseRef,
    [string]$MainBranch
  )

  $isMainPush = $EventName -eq 'push' -and $Ref -eq "refs/heads/$MainBranch"
  $isMergedPullRequest = $EventName -ne 'push' -and $BaseRef -eq $MainBranch

  return $isMainPush -and -not $isMergedPullRequest
}

foreach ($scenario in @(
  @{ Name = 'push to main'; EventName = 'push'; Ref = "refs/heads/$mainBranch"; BaseRef = ''; Expected = $true },
  @{ Name = 'push to dev'; EventName = 'push'; Ref = 'refs/heads/dev'; BaseRef = ''; Expected = $false },
  @{ Name = 'merged pull request into main'; EventName = 'pull_request'; Ref = 'refs/pull/41/merge'; BaseRef = $mainBranch; Expected = $false }
)) {
  $actual = Test-MainReleaseCandidate -EventName $scenario.EventName -Ref $scenario.Ref -BaseRef $scenario.BaseRef -MainBranch $mainBranch
  if ($actual -ne $scenario.Expected) {
    throw "Release orchestration gating for '$($scenario.Name)' returned $actual but expected $($scenario.Expected)"
  }
}

if ($env:GITHUB_EVENT_NAME) {
  $isReleaseContext = Test-MainReleaseCandidate -EventName $env:GITHUB_EVENT_NAME -Ref $env:GITHUB_REF -BaseRef $env:GITHUB_BASE_REF -MainBranch $mainBranch
  Write-Output "Current context ($env:GITHUB_EVENT_NAME $env:GITHUB_REF) selects artifact-first release orchestration: $isReleaseContext"
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
  $path = Join-Path $root ".github/workflows/$flow"
  $content = Get-Content -Raw $path

  foreach ($required in $contracts[$flow]) {
    if ($content -notmatch [regex]::Escape($required)) {
      throw "$flow must contain $required"
    }
  }

  foreach ($required in @(
    'concurrency:',
    'group: build-flow-release-${{ github.repository }}-${{ inputs.main-branch }}-${{ github.ref }}',
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

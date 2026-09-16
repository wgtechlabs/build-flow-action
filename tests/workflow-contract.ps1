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
  $isMergedPullRequest = $EventName -eq 'pull_request' -and $Ref -like 'refs/pull/*/merge' -and $BaseRef -eq $MainBranch

  return $isMainPush -and -not $isMergedPullRequest
}

function Test-PublishedReleaseArtifactCandidate {
  param(
    [string]$EventName,
    [string]$EventAction,
    [string]$SenderType
  )

  return $EventName -eq 'release' -and $EventAction -eq 'published' -and $SenderType -ne 'Bot'
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

foreach ($scenario in @(
  @{ Name = 'manually published release'; EventName = 'release'; EventAction = 'published'; SenderType = 'User'; Expected = $true },
  @{ Name = 'automation-published release'; EventName = 'release'; EventAction = 'published'; SenderType = 'Bot'; Expected = $false },
  @{ Name = 'release edited'; EventName = 'release'; EventAction = 'edited'; SenderType = 'User'; Expected = $false }
)) {
  $actual = Test-PublishedReleaseArtifactCandidate -EventName $scenario.EventName -EventAction $scenario.EventAction -SenderType $scenario.SenderType
  if ($actual -ne $scenario.Expected) {
    throw "Published release gating for '$($scenario.Name)' returned $actual but expected $($scenario.Expected)"
  }
}

if ($env:GITHUB_EVENT_NAME) {
  $isReleaseContext = Test-MainReleaseCandidate -EventName $env:GITHUB_EVENT_NAME -Ref $env:GITHUB_REF -BaseRef $env:GITHUB_BASE_REF -MainBranch $mainBranch
  Write-Output "Current context ($env:GITHUB_EVENT_NAME $env:GITHUB_REF) selects artifact-first release orchestration: $isReleaseContext"
}

$contracts = @{
  'app.yml' = @(
    'wgtechlabs/release-build-flow-action@6df9cb42c24c296d902150d051a0b6be4422cccc # v1.8.0',
    'wgtechlabs/container-build-flow-action@fb5c0662b33f7702bc1ccf85350689436989f606 # v1.9.0',
    'wgtechlabs/package-build-flow-action@9be4582316267a397955254e0f80cfe0b9454ab2 # v2.2.0',
    'version-plan:', 'source-finalize:', 'finalized-sha:', 'planned-version-tag:', 'planned-version-bump-type:', 'artifact-published:',
    'ref: ${{ needs.source-finalize.outputs.finalized-sha || github.sha }}',
    'needs.source-finalize.result == ''success''',
    'Release publish (last)',
    'Finalization skipped: package did not publish.',
    'Finalization skipped: container did not publish.'
  )
  'package.yml' = @(
    'wgtechlabs/release-build-flow-action@6df9cb42c24c296d902150d051a0b6be4422cccc # v1.8.0',
    'wgtechlabs/package-build-flow-action@9be4582316267a397955254e0f80cfe0b9454ab2 # v2.2.0',
    'version-plan:', 'source-finalize:', 'finalized-sha:', 'planned-version:', 'planned-npm-tag:', 'artifact-published:',
    'ref: ${{ needs.source-finalize.outputs.finalized-sha || github.sha }}',
    'needs.source-finalize.result == ''success''',
    'Release publish (last)'
  )
  'container.yml' = @(
    'wgtechlabs/release-build-flow-action@6df9cb42c24c296d902150d051a0b6be4422cccc # v1.8.0',
    'wgtechlabs/container-build-flow-action@fb5c0662b33f7702bc1ccf85350689436989f606 # v1.9.0',
    'version-plan:', 'source-finalize:', 'finalized-sha:', 'planned-version-tag:', 'artifact-published:',
    'ref: ${{ needs.source-finalize.outputs.finalized-sha || github.sha }}',
    'needs.source-finalize.result == ''success''',
    'Release publish (last)'
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
    'if [[ "$GH_EVENT_NAME" == "push" && "$GH_REF" == "refs/heads/$INPUT_MAIN_BRANCH" ]]; then',
    'GH_SENDER_TYPE: ${{ github.event.sender.type }}',
    'if [[ "$GH_EVENT_NAME" == "release" && "$GH_EVENT_ACTION" == "published" && "$GH_SENDER_TYPE" != "Bot" ]]; then',
    'create-release: false',
    'tag-only: true',
    "if: `${{ !inputs.release-dry-run && needs.context.outputs.allow-release-finalize == 'true'",
    'run: echo "finalized-sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"',
    'gh release create "${args[@]}"'
  )) {
    if ($content -notmatch [regex]::Escape($required)) {
      throw "$flow must contain $required"
    }

    $releasePrimitive = 'wgtechlabs/release-build-flow-action@6df9cb42c24c296d902150d051a0b6be4422cccc # v1.8.0'
    if (([regex]::Matches($content, [regex]::Escape($releasePrimitive))).Count -ne 2) {
      throw "$flow must invoke the release primitive exactly twice: plan and source finalization"
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
    if ($content -notmatch [regex]::Escape("(!inputs.enable-package || needs.package.outputs.artifact-published == 'true')")) {
      throw 'app.yml must require every enabled package artifact to publish before the release'
    }
    if ($content -notmatch [regex]::Escape("(!inputs.enable-container || needs.container.outputs.artifact-published == 'true')")) {
      throw 'app.yml must require every enabled container artifact to publish before the release'
    }
    if ($content -notmatch [regex]::Escape('org.opencontainers.image.revision=${{ needs.source-finalize.outputs.finalized-sha || github.sha }}')) {
      throw 'app.yml must override container OCI revision metadata with the finalized source SHA'
    }
    $callerLabels = '${{ inputs.container-labels }}'
    $revisionLabel = 'org.opencontainers.image.revision=${{ needs.source-finalize.outputs.finalized-sha || github.sha }}'
    if ($content.IndexOf($revisionLabel) -lt $content.IndexOf($callerLabels)) {
      throw 'app.yml must apply the finalized OCI revision after caller-provided labels'
    }
  }

  if ($flow -eq 'container.yml' -and $content -notmatch [regex]::Escape('org.opencontainers.image.revision=${{ needs.source-finalize.outputs.finalized-sha || github.sha }}')) {
    throw 'container.yml must override container OCI revision metadata with the finalized source SHA'
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

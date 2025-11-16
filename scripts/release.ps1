<#
.SYNOPSIS
  Helper script to create/publish a PDFForge release with GitHub CLI.

.DESCRIPTION
  Interactive (or parameterized) PowerShell script to:
    - Optionally create and push an annotated git tag
    - Trigger the GitHub Actions release workflow (release.yml)
    - Optionally publish a Draft release to a Published release

.PARAMETER Tag
  The SemVer tag to release, e.g., v2.2.4

.PARAMETER CreateTag
  Create an annotated git tag locally if it does not exist.

.PARAMETER PushTag
  Push the tag to origin.

.PARAMETER RunWorkflow
  Trigger the GitHub Actions workflow release.yml with inputs tag and confirm.

.PARAMETER ConfirmInput
  The confirm input for the workflow (default: YES).

.PARAMETER Publish
  If a Draft Release exists for the tag, publish it (turn off --draft).

.PARAMETER Wait
  After triggering the workflow, wait and stream logs of the latest run of release.yml.

.EXAMPLE
  ./scripts/release.ps1 -Tag v2.2.4 -CreateTag -PushTag -RunWorkflow -Publish -Wait

.NOTES
  - Requires GitHub CLI (gh) to be installed and authenticated (gh auth login)
  - Works best when a default repo is set: gh repo set-default oscar2song/pdfforge
  - You can override repo detection by setting $env:GH_REPO to "owner/name"
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)] [string]$Tag,
  [switch]$CreateTag,
  [switch]$PushTag,
  [switch]$RunWorkflow,
  [Alias('Confirm')] [string]$ConfirmInput = 'YES',
  [switch]$Publish,
  [switch]$Wait
)

function Require-Command {
  param([string]$Name, [string]$InstallHint)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    Write-Error "Required command not found: $Name. $InstallHint"
    exit 1
  }
}

function Get-RepoSlug {
  # Priority: env GH_REPO > gh repo view > git remote origin
  if ($env:GH_REPO) { return $env:GH_REPO }
  try {
    $json = gh repo view --json nameWithOwner --jq .nameWithOwner 2>$null
    if ($LASTEXITCODE -eq 0 -and $json) { return $json }
  } catch {}
  try {
    $url = git remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0 -and $url) {
      if ($url -match 'github.com[/:]([^/]+/[^/.]+)') { return $matches[1] }
    }
  } catch {}
  return $null
}

function Confirm-YesNo {
  param([string]$Message)
  while ($true) {
    $resp = Read-Host "$Message [y/N]"
    if ($resp -match '^(?i:y|yes)$') { return $true }
    if ($resp -match '^(?i:n|no)$' -or [string]::IsNullOrWhiteSpace($resp)) { return $false }
  }
}

# --- Preconditions ---
Require-Command git "Install Git for Windows: https://git-scm.com/download/win"

# Make gh available even if PATH hasn’t refreshed in this session
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  $ghPath = 'C:\\Program Files\\GitHub CLI\\gh.exe'
  if (Test-Path $ghPath) { Set-Alias gh $ghPath }
}
Require-Command gh "Install with: winget install --id GitHub.cli -e --source winget"

# Check auth
$auth = (& gh auth status 2>$null)
if ($LASTEXITCODE -ne 0) {
  Write-Host "You are not logged into GitHub CLI. Running 'gh auth login'..." -ForegroundColor Yellow
  gh auth login
  if ($LASTEXITCODE -ne 0) { Write-Error "GitHub auth failed."; exit 1 }
}

# Determine repo
$repo = Get-RepoSlug
if (-not $repo) {
  Write-Host "Could not detect repo. Set default with: gh repo set-default owner/name or set GH_REPO env var." -ForegroundColor Yellow
  $repo = Read-Host "Enter repo (owner/name)"
}
Write-Host "Using repository: $repo" -ForegroundColor Cyan

# Ask for Tag if missing
if (-not $Tag) { $Tag = Read-Host "Enter SemVer tag (e.g., v2.2.4)" }
if ([string]::IsNullOrWhiteSpace($Tag)) { Write-Error "Tag is required."; exit 1 }

# Display summary of actions
Write-Host "Actions:" -ForegroundColor Green
Write-Host "  CreateTag:  $CreateTag"
Write-Host "  PushTag:    $PushTag"
Write-Host "  RunWorkflow:$RunWorkflow"
Write-Host "  Publish:    $Publish"
Write-Host "  Wait:       $Wait"
Write-Host "  Tag:        $Tag"
Write-Host "  Repo:       $repo"

# Confirm before proceeding in interactive mode
if (-not $PSBoundParameters.ContainsKey('CreateTag') -and 
    -not $PSBoundParameters.ContainsKey('PushTag') -and 
    -not $PSBoundParameters.ContainsKey('RunWorkflow') -and 
    -not $PSBoundParameters.ContainsKey('Publish') ) {
  if (-not (Confirm-YesNo "Proceed to run default flow: CreateTag+PushTag+RunWorkflow?")) { exit 0 }
  $CreateTag = $true; $PushTag = $true; $RunWorkflow = $true
}

# Step 1: Create tag
if ($CreateTag) {
  $exists = (git tag --list $Tag)
  if ($exists) {
    Write-Host "Tag $Tag already exists locally." -ForegroundColor Yellow
  } else {
    $msg = "PDFForge $Tag – Release"
    git tag -a $Tag -m $msg
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create tag $Tag."; exit 1 }
    Write-Host "Created tag $Tag" -ForegroundColor Green
  }
}

# Step 2: Push tag
if ($PushTag) {
  git push origin $Tag
  if ($LASTEXITCODE -ne 0) { Write-Error "Failed to push tag $Tag to origin."; exit 1 }
  Write-Host "Pushed tag $Tag to origin" -ForegroundColor Green
}

# Step 3: Trigger workflow
if ($RunWorkflow) {
  Write-Host "Triggering workflow release.yml for $Tag ..." -ForegroundColor Cyan
  gh workflow run release.yml -R $repo -f tag=$Tag -f confirm=$ConfirmInput
  if ($LASTEXITCODE -ne 0) { Write-Error "Failed to trigger workflow."; exit 1 }
  Write-Host "Workflow dispatched." -ForegroundColor Green
  if ($Wait) {
    Write-Host "Waiting for the latest run logs..." -ForegroundColor Cyan
    gh run watch --workflow release.yml -R $repo --exit-status
    gh run view --workflow release.yml -R $repo --log --latest
  }
}

# Step 4: Publish release
if ($Publish) {
  Write-Host "Publishing release $Tag (turning off draft)..." -ForegroundColor Cyan
  gh release edit $Tag -R $repo --draft=false
  if ($LASTEXITCODE -ne 0) { Write-Error "Failed to publish release $Tag."; exit 1 }
  Write-Host "Published release $Tag" -ForegroundColor Green
}

Write-Host "Done." -ForegroundColor Green

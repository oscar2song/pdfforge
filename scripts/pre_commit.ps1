Param(
    [string]$Root = $(Resolve-Path "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)")
)

Write-Host "Running pre-commit checks (PowerShell)..."
$ErrorActionPreference = 'Stop'

# Helper to run a command if available
function Try-Run($name, $cmd) {
    if (Get-Command $name -ErrorAction SilentlyContinue) {
        Write-Host "-> Running $name"
        try {
            & $cmd
            if ($LASTEXITCODE -ne 0) {
                Write-Error "$name failed with exit code $LASTEXITCODE"
                return $false
            }
            return $true
        } catch {
            Write-Error "$name failed: $_"
            return $false
        }
    } else {
        Write-Host "-> Skipping $name (not installed)"
        return $true
    }
}

$rootPath = (Resolve-Path "$PSScriptRoot/..").ProviderPath
Set-Location $rootPath

$ok = $true

# Python checks: ruff (fix), isort, black
$ok = $ok -and (Try-Run 'ruff' { ruff check --fix . } )
$ok = $ok -and (Try-Run 'isort' { isort . } )
$ok = $ok -and (Try-Run 'black' { black . } )

# JavaScript/Frontend checks: prefer npm lint if package.json present
if (Test-Path "$rootPath/package.json") {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "-> Running npm lint (if present)"
        try {
            npm run lint --silent --if-present
            if ($LASTEXITCODE -ne 0) { Write-Error "npm lint failed"; $ok = $false }
        } catch { Write-Error "npm lint failed: $_"; $ok = $false }
    } else {
        Write-Host "-> Skipping npm lint (npm not installed)"
    }
} else {
    Write-Host "-> No package.json at repo root; skipping npm lint"
}

if (-not $ok) {
    Write-Error "Pre-commit checks failed. Fix issues and try again."
    exit 1
}

Write-Host "Pre-commit checks passed."
exit 0

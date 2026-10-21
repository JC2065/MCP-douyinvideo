<#
.SYNOPSIS
  Release the video/admin service to the Guangzhou server.

.DESCRIPTION
  Default (delta): uploads only the committed code (git archive of scripts/ + utils/platform-boundaries.json,
  a few hundred KB) and builds the new image ON THE SERVER on top of the live image. No local Docker needed.
  Full (-Full, or automatically when Dockerfile FROM/RUN lines changed or the live image is not a platform-<commit>
  release): builds locally with Docker and uploads the whole image (~270 MB).

  Both modes then run scripts/remote-release.sh on the server: back up .env/compose/admin data to
  /opt/youai/releases/<tag>/, switch VIDEO_TAG, restart only the video service, health-check, and
  automatically restore the previous release on failure. SSH keeps BatchMode/StrictHostKeyChecking.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\deploy-platform.ps1          # delta when possible
  powershell -ExecutionPolicy Bypass -File scripts\deploy-platform.ps1 -Full    # force full image upload
  powershell -ExecutionPolicy Bypass -File scripts\deploy-platform.ps1 -DryRun
#>
param(
  [string]$Server = "root@182.61.14.185",
  [string]$Key = "$env:USERPROFILE\.ssh\youai_deploy",
  [string]$PublicUrl = "https://youai888.top/youai",
  [switch]$Full,
  [switch]$DryRun,
  [switch]$SkipTests
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$Rel = "/opt/youai/releases"

function Step($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Run($exe, [string[]]$arguments) {
  Write-Host "    $exe $($arguments -join ' ')" -ForegroundColor DarkGray
  if ($DryRun) { return }
  & $exe @arguments
  if ($LASTEXITCODE -ne 0) { throw "$exe failed with exit code $LASTEXITCODE" }
}
$sshOpts = @("-i", $Key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes")
function Release([string]$command) {
  # remote-release.sh lives on the server; arguments are plain words (no quotes needed).
  Write-Host "    ssh $Server bash $Rel/remote-release.sh $command" -ForegroundColor DarkGray
  if ($DryRun) { return }
  & ssh @sshOpts $Server "bash $Rel/remote-release.sh $command"
  if ($LASTEXITCODE -ne 0) { throw "remote step '$command' failed with exit code $LASTEXITCODE" }
}

$Tag = "platform-" + (git rev-parse --short HEAD).Trim()
$dirty = git status --porcelain -- scripts utils/platform-boundaries.json
if ($dirty) { throw "Uncommitted changes; commit first so the release matches a Git revision:`n$dirty" }
if (-not (Test-Path $Key)) { throw "SSH key not found: $Key" }

Step "1/5 Run backend tests"
$py = $null
foreach ($candidate in @("py -3", "python", "python3")) {
  $parts = $candidate -split " "
  try {
    $rest = @($parts | Select-Object -Skip 1)
    & $parts[0] @rest -c "import sys; assert sys.version_info >= (3, 8)" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $py = $parts; break }
  } catch { }
}
if ($SkipTests) { Write-Host "    skipped (-SkipTests)" -ForegroundColor Yellow }
elseif (-not $py) { Write-Host "    Python not found on this computer; skipping local tests (they passed in the development check)." -ForegroundColor Yellow }
else { foreach ($test in @("test-platform-config.py", "test-inspiration-ai.py", "test-text-works.py")) { Run $py[0] (@($py | Select-Object -Skip 1) + @("scripts/$test")) } }

Step "2/5 Check the live release"
Run "scp" ($sshOpts + @("scripts/remote-release.sh", "${Server}:$Rel/remote-release.sh"))
$live = ""
if (-not $DryRun) { $live = (& ssh @sshOpts $Server "bash $Rel/remote-release.sh live").Trim() }
Write-Host "    live: $live   new: $Tag"
if ($live -eq $Tag) { Write-Host "`n$Tag is already live." -ForegroundColor Green; return }
$mode = "delta"
if ($Full) { $mode = "full" }
elseif ($live -notmatch '^platform-[0-9a-f]+$') { $mode = "full"; Write-Host "    live image is not a platform-<commit> release: full upload" -ForegroundColor Yellow }
else {
  $base = $live.Substring(9)
  $known = $true
  try { git cat-file -e "$base^{commit}" 2>$null; if ($LASTEXITCODE -ne 0) { $known = $false } } catch { $known = $false }
  if (-not $known) { $mode = "full"; Write-Host "    live commit $base not in this repository: full upload" -ForegroundColor Yellow }
  elseif (git diff $base HEAD -- scripts/Dockerfile.video | Select-String -Pattern '^[+-](FROM|RUN)') { $mode = "full"; Write-Host "    dependencies changed: full upload" -ForegroundColor Yellow }
  else { git diff --stat $base HEAD -- scripts utils/platform-boundaries.json | Select-Object -Last 1 }
}

if ($mode -eq "delta") {
  Step "3/5 Upload changed code only and build on the server"
  $archive = Join-Path ([System.IO.Path]::GetTempPath()) "app-$Tag.tgz"
  Run "git" @("archive", "--format=tar.gz", "-o", $archive, "HEAD", "scripts", "utils/platform-boundaries.json")
  if (-not $DryRun) { Write-Host ("    archive: {0:N0} KB" -f ((Get-Item $archive).Length / 1KB)) }
  Run "ssh" ($sshOpts + @($Server, "mkdir -p $Rel/$Tag"))
  Run "scp" ($sshOpts + @($archive, "${Server}:$Rel/$Tag/app.tgz"))
  if (-not $DryRun) { Remove-Item $archive -Force }
  Release "build-delta $Tag"
} else {
  Step "3/5 Build locally and upload the whole image"
  Run "docker" @("build", "-f", "scripts/Dockerfile.video", "-t", "codexyouai-video:$Tag", ".")
  Write-Host "    check-image-modules.py | docker run -i codexyouai-video:$Tag" -ForegroundColor DarkGray
  if (-not $DryRun) {
    Get-Content -Raw scripts/check-image-modules.py | docker run -i --rm --entrypoint python "codexyouai-video:$Tag" -
    if ($LASTEXITCODE -ne 0) { throw "image failed the server import check" }
  }
  $archive = Join-Path ([System.IO.Path]::GetTempPath()) "codexyouai-video-$Tag.tar"
  Run "docker" @("save", "-o", $archive, "codexyouai-video:$Tag")
  Run "ssh" ($sshOpts + @($Server, "mkdir -p $Rel/$Tag"))
  Run "scp" ($sshOpts + @($archive, "${Server}:$Rel/$Tag/image.tar"))
  Run "ssh" ($sshOpts + @($Server, "docker load -i $Rel/$Tag/image.tar && rm -f $Rel/$Tag/image.tar"))
  if (-not $DryRun) { Remove-Item $archive -Force }
}

Step "4/5 Back up, switch and health-check (auto-rollback on failure)"
Release "switch $Tag"

Step "5/5 Public checks"
if ($DryRun) { Write-Host "`nDry run only: nothing was built, uploaded or changed. Mode would be: $mode." -ForegroundColor Yellow; return }
$health = Invoke-WebRequest -UseBasicParsing "$PublicUrl/health" -TimeoutSec 10
Write-Host "    public health: $($health.StatusCode)"
try { Invoke-WebRequest -UseBasicParsing "$PublicUrl/admin-api/platform" -TimeoutSec 10 | Out-Null; throw "admin API answered without a session" }
catch { if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw }; Write-Host "    admin API requires login: 401" }
Write-Host "`nDone ($mode). Release $Tag is live. Rollback: restore $Rel/$Tag/env.previous to /opt/youai/internal-api/.env and run 'docker compose -f compose.video-cloud.yml up -d --no-build --wait video'." -ForegroundColor Green

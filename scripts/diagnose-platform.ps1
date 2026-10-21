<#
  Read-only diagnosis for a release that failed its health check.
  Does NOT switch VIDEO_TAG or restart the live service. Output is saved to deploy-diagnose.log.
#>
param(
  [string]$Tag = "",
  [string]$Server = "root@182.61.14.185",
  [string]$Key = "$env:USERPROFILE\.ssh\youai_deploy",
  [string]$RemoteDir = "/opt/youai/internal-api"
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not $Tag) { $Tag = "platform-" + (git rev-parse --short HEAD).Trim() }
$sshOpts = @("-i", $Key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes")
$script = @'
cd __DIR__
LIVE=$(grep '^VIDEO_TAG=' .env | cut -d= -f2)
echo "== live tag: $LIVE   candidate: __TAG__"
echo "== candidate image present:"; docker image ls codexyouai-video --format '{{.Tag}} {{.CreatedSince}}' | head -8
echo "== files only in live image:"
diff <(docker run --rm --entrypoint sh codexyouai-video:$LIVE -c 'ls scripts' | sort) <(docker run --rm --entrypoint sh codexyouai-video:__TAG__ -c 'ls scripts' | sort)
echo "== python packages diff (live < > candidate):"
diff <(docker run --rm --entrypoint pip codexyouai-video:$LIVE freeze | sort) <(docker run --rm --entrypoint pip codexyouai-video:__TAG__ freeze | sort)
echo "== live image entrypoint/cmd:"; docker image inspect codexyouai-video:$LIVE --format '{{json .Config.Cmd}} {{json .Config.Entrypoint}} {{json .Config.WorkingDir}}'
echo "== candidate import test with live compose environment and volumes:"
VIDEO_TAG=__TAG__ timeout 120 docker compose -f compose.video-cloud.yml run --rm --no-deps -T --entrypoint python video -c "import importlib.util,traceback
try:
    spec=importlib.util.spec_from_file_location('vs','scripts/video-server.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);print('IMPORT OK')
    print('platform video:',m.PLATFORM.config()['video']);print('ai scenes:',sorted(m.INSPIRATION_AI.config()['scenes']))
except Exception:
    traceback.print_exc()" 2>&1 | tail -40
echo "== last logs of the live container (tail 15):"; docker logs --tail 15 youai-video-video-1 2>&1
'@
$script = $script.Replace("__DIR__", $RemoteDir).Replace("__TAG__", $Tag) -replace "`r", ""
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script + "`n"))
$log = Join-Path (Get-Location) "deploy-diagnose.log"
& ssh @sshOpts $Server "echo $encoded | base64 -d | bash" 2>&1 | Tee-Object -FilePath $log
Write-Host "`nSaved to $log" -ForegroundColor Green

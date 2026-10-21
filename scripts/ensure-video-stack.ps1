param(
  [int]$DockerTimeoutSeconds = 150,
  [int]$ServiceTimeoutSeconds = 150
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$parserRoot = 'E:\data\codexYOUAI-services\Douyin_TikTok_Download_API-5.1.3'
$composeFile = Join-Path $parserRoot 'docker\compose.yml'
$dockerDesktop = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
$python = 'C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe'
$logRoot = 'E:\data\codexYOUAI-data\logs'
$mutex = [Threading.Mutex]::new($false, 'Local\YOUAI.VideoStackWatchdog')

function Test-Endpoint([string]$Uri) {
  try {
    $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 4
    return $response.StatusCode -eq 200
  } catch { return $false }
}

function Test-DockerEngine {
  $previous = $ErrorActionPreference
  try {
    $ErrorActionPreference = 'Continue'
    & docker info *> $null
    return $LASTEXITCODE -eq 0
  } finally { $ErrorActionPreference = $previous }
}

function Wait-Until([scriptblock]$Condition, [int]$TimeoutSeconds, [string]$Failure) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    if (& $Condition) { return }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)
  throw $Failure
}

if (-not $mutex.WaitOne(0)) {
  [pscustomobject]@{ status = 'already_running' } | ConvertTo-Json -Compress
  exit 0
}

try {
  New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

  if (-not (Test-Endpoint 'http://127.0.0.1:8000/readyz')) {
    if (-not (Test-Path -LiteralPath $composeFile)) { throw "解析器编排文件不存在：$composeFile" }
    if (-not (Test-DockerEngine)) {
      if (-not (Test-Path -LiteralPath $dockerDesktop)) { throw 'Docker Desktop 未安装' }
      Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
      Wait-Until { Test-DockerEngine } $DockerTimeoutSeconds 'Docker Desktop 启动超时'
    }
    & docker compose -p dtk -f $composeFile up -d --no-build --wait --wait-timeout $ServiceTimeoutSeconds
    if ($LASTEXITCODE -ne 0) { throw 'DTK 解析服务启动失败' }
    Wait-Until { Test-Endpoint 'http://127.0.0.1:8000/readyz' } $ServiceTimeoutSeconds 'DTK 解析服务未就绪'
  }

  if (-not (Test-Endpoint 'http://127.0.0.1:8765/health')) {
    if (-not (Test-Path -LiteralPath $python)) { throw 'YOUAI 视频服务 Python 环境不存在' }
    $launcher = Join-Path $PSScriptRoot 'start-video-server.ps1'
    Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$launcher) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'video-server.out.log') -RedirectStandardError (Join-Path $logRoot 'video-server.err.log')
    Wait-Until { Test-Endpoint 'http://127.0.0.1:8765/health' } 30 'YOUAI 视频服务启动失败'
  }

  & (Join-Path $PSScriptRoot 'ensure-reference-relay.ps1') | Out-Null

  [pscustomobject]@{
    status = 'ready'
    video = 'http://127.0.0.1:8765/health'
    parser = 'http://127.0.0.1:8000/readyz'
    checkedAt = (Get-Date).ToString('o')
  } | ConvertTo-Json -Compress
} finally {
  $mutex.ReleaseMutex()
  $mutex.Dispose()
}

$ErrorActionPreference = 'Stop'
$cloudflared = 'C:\Users\one\AppData\Local\Programs\Cloudflare\cloudflared.exe'
$python = 'C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe'
$dataRoot = 'E:\data\codexYOUAI-data'
$stateFile = Join-Path $dataRoot 'reference-relay.json'
$credentialFile = Join-Path $dataRoot '.youai-reference-relay.env'
$logRoot = Join-Path $dataRoot 'logs'
function Test-Endpoint([string]$Uri) { try { return (Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 8).StatusCode -eq 200 } catch { return $false } }
function Wait-Endpoint([string]$Uri,[int]$Seconds) { $deadline=(Get-Date).AddSeconds($Seconds);do { if(Test-Endpoint $Uri){return};Start-Sleep -Seconds 1 } while((Get-Date)-lt $deadline);throw "Endpoint did not become ready: $Uri" }
function Read-State { if(-not (Test-Path -LiteralPath $stateFile)){return $null};try{return Get-Content -LiteralPath $stateFile -Raw|ConvertFrom-Json}catch{return $null} }
New-Item -ItemType Directory -Path $logRoot -Force|Out-Null
if(-not (Test-Path -LiteralPath $credentialFile)){
  $bytes=New-Object byte[] 32;$rng=[Security.Cryptography.RandomNumberGenerator]::Create();$rng.GetBytes($bytes);$rng.Dispose()
  $secret=($bytes|ForEach-Object{$_.ToString('x2')}) -join ''
  [IO.File]::WriteAllText($credentialFile,"YOUAI_REFERENCE_MEDIA_SECRET=$secret"+[Environment]::NewLine,(New-Object Text.UTF8Encoding($true)))
}
$state=Read-State
if($state -and $state.publicBaseUrl -and (Test-Endpoint ($state.publicBaseUrl.TrimEnd('/')+'/health'))){[pscustomobject]@{status='ready';publicBaseUrl=$state.publicBaseUrl;reused=$true}|ConvertTo-Json -Compress;exit 0}
if(-not (Test-Endpoint 'http://127.0.0.1:8766/health')){
  $relay=Start-Process -FilePath $python -ArgumentList (Join-Path $PSScriptRoot 'reference-relay.py') -WorkingDirectory (Split-Path -Parent $PSScriptRoot) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'reference-relay.out.log') -RedirectStandardError (Join-Path $logRoot 'reference-relay.err.log')
  Wait-Endpoint 'http://127.0.0.1:8766/health' 20
} else {$relay=$null}
if(-not (Test-Path -LiteralPath $cloudflared)){throw 'cloudflared is not installed'}
$stamp=[DateTimeOffset]::Now.ToUnixTimeMilliseconds();$tunnelLog=Join-Path $logRoot "reference-tunnel-$stamp.err.log";$tunnelOut=Join-Path $logRoot "reference-tunnel-$stamp.out.log"
$tunnel=Start-Process -FilePath $cloudflared -ArgumentList @('tunnel','--no-autoupdate','--url','http://127.0.0.1:8766') -WindowStyle Hidden -PassThru -RedirectStandardOutput $tunnelOut -RedirectStandardError $tunnelLog
$deadline=(Get-Date).AddSeconds(45);$public=''
do { Start-Sleep -Milliseconds 500;if(Test-Path -LiteralPath $tunnelLog){$match=[regex]::Match((Get-Content -LiteralPath $tunnelLog -Raw),'https://[a-z0-9-]+\.trycloudflare\.com');if($match.Success){$public=$match.Value;break}} } while((Get-Date)-lt $deadline -and -not $tunnel.HasExited)
if(-not $public){throw 'Cloudflare reference tunnel did not return a public HTTPS URL'}
Wait-Endpoint ($public+'/health') 45
$record=[ordered]@{publicBaseUrl=$public;relayPid=if($relay){$relay.Id}else{$state.relayPid};tunnelPid=$tunnel.Id;updatedAt=(Get-Date).ToString('o')}
[IO.File]::WriteAllText($stateFile,($record|ConvertTo-Json),(New-Object Text.UTF8Encoding($true)))
[pscustomobject]@{status='ready';publicBaseUrl=$public;reused=$false}|ConvertTo-Json -Compress

$ErrorActionPreference = 'Stop'
Unregister-ScheduledTask -TaskName 'YOUAI Video Stack Watchdog' -Confirm:$false -ErrorAction SilentlyContinue
Write-Output 'YOUAI Video Stack Watchdog removed.'

$ErrorActionPreference = 'Stop'
$ensureScript = Join-Path $PSScriptRoot 'ensure-video-stack.ps1'
$powershell = (Get-Command powershell.exe).Source
$action = New-ScheduledTaskAction -Execute $powershell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ensureScript`""
$logon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
Register-ScheduledTask -TaskName 'YOUAI Video Stack Watchdog' -Action $action -Trigger @($logon,$repeat) -Settings $settings -Description 'Keeps the local YOUAI video gateway and Douyin parser ready.' -Force | Out-Null
& $ensureScript

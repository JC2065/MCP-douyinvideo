$ErrorActionPreference = 'Stop'

$credentialFile = if ($env:YOUAI_REFERENCE_CREDENTIAL_FILE) {
  $env:YOUAI_REFERENCE_CREDENTIAL_FILE
} else {
  'E:\data\codexYOUAI-services\Douyin_TikTok_Download_API-5.1.3\.youai-parser.env'
}

if (-not (Test-Path -LiteralPath $credentialFile)) {
  throw "参考解析凭据文件不存在：$credentialFile"
}

$settings = @{}
Get-Content -LiteralPath $credentialFile | ForEach-Object {
  $separator = $_.IndexOf('=')
  if ($separator -gt 0) { $settings[$_.Substring(0, $separator)] = $_.Substring($separator + 1) }
}
if (-not $settings.DTK_API_KEY) { throw '参考解析凭据文件缺少 DTK_API_KEY' }

$env:YOUAI_REFERENCE_PARSER_URL = 'http://127.0.0.1:8000'
$env:YOUAI_REFERENCE_PARSER_KEY = $settings.DTK_API_KEY
& 'C:\Users\one\MoneyPrinterTurbo\.venv\Scripts\python.exe' (Join-Path $PSScriptRoot 'video-server.py')

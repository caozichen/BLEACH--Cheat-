[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$CheatsDir = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PPSSPP\PSP\Cheats'),
    [string]$Source = (Join-Path $PSScriptRoot '..\cheats\UCAS40234.ini')
)
$ErrorActionPreference = 'Stop'
$Source = (Resolve-Path -LiteralPath $Source).Path
$sourceText = Get-Content -LiteralPath $Source -Raw -Encoding UTF8
if ($sourceText -notmatch '(?m)^_S UCAS-40234\r?$') { throw '源文件的游戏 ID 不匹配。' }
$target = Join-Path ([IO.Path]::GetFullPath($CheatsDir)) 'UCAS40234.ini'
$sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
if ((Test-Path -LiteralPath $target) -and (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -eq $sourceHash) {
    [PSCustomObject]@{Status='AlreadyInstalled'; Target=$target; SHA256=$sourceHash} | ConvertTo-Json
    return
}
if (-not $PSCmdlet.ShouldProcess($target, '备份已有金手指并安装 UCAS40234.ini')) { return }
New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
$backup = $null
if (Test-Path -LiteralPath $target) {
    $backup = $target + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8) + '.bak'
    Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
}
Copy-Item -LiteralPath $Source -Destination $target -Force
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $sourceHash) { throw '安装后哈希不匹配。' }
[PSCustomObject]@{Status='Installed'; Target=$target; Backup=$backup; SHA256=$sourceHash} | ConvertTo-Json

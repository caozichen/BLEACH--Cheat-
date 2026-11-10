$ErrorActionPreference = 'Stop'
$repairRoot = $PSScriptRoot
$activeCheats = 'C:\Users\曹梓晨\Documents\PPSSPP\PSP\Cheats\UCAS40234.ini'
$originalBackup = Join-Path $repairRoot 'UCAS40234.before-attack-repair.ini'
$candidateCheats = Join-Path $repairRoot 'UCAS40234.repaired.ini'
$expectedHash = (Get-FileHash -LiteralPath $originalBackup -Algorithm SHA256).Hash
$currentHash = (Get-FileHash -LiteralPath $activeCheats -Algorithm SHA256).Hash
if ($currentHash -ne $expectedHash) {
    throw '金手指文件在分析后发生了变化，已停止写入以保留新改动。'
}
$localBackup = $activeCheats + '.before-20261031-attack-fix.bak'
if (Test-Path -LiteralPath $localBackup) {
    if ((Get-FileHash -LiteralPath $localBackup -Algorithm SHA256).Hash -ne $expectedHash) {
        throw '已有同名备份内容不同，已停止写入。'
    }
} else {
    Copy-Item -LiteralPath $activeCheats -Destination $localBackup
}
Copy-Item -LiteralPath $candidateCheats -Destination $activeCheats -Force
$candidateHash = (Get-FileHash -LiteralPath $candidateCheats -Algorithm SHA256).Hash
$installedHash = (Get-FileHash -LiteralPath $activeCheats -Algorithm SHA256).Hash
if ($installedHash -ne $candidateHash) {
    throw '写入后的校验失败。'
}
[PSCustomObject]@{
    Installed = $activeCheats
    Backup = $localBackup
    SHA256 = $installedHash
} | ConvertTo-Json

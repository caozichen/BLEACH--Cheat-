[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Emulator,
    [Parameter(Mandatory)][string]$Iso,
    [string]$State,
    [switch]$HighHp,
    [switch]$HighDefense,
    [string]$WorkDir = (Join-Path $PSScriptRoot '..\work')
)
$ErrorActionPreference = 'Stop'
$Emulator = (Resolve-Path -LiteralPath $Emulator).Path
$Iso = (Resolve-Path -LiteralPath $Iso).Path
$emulatorDir = Split-Path -Parent $Emulator
if ([IO.Path]::GetExtension($Emulator) -ne '.exe') { throw '请指定 PPSSPPWindows64.exe。' }
# Test-only portable emulator copies use a local memstick directory.
if (-not (Test-Path -LiteralPath (Join-Path $emulatorDir 'memstick\PSP\SYSTEM\ppsspp.ini'))) {
    throw '此脚本只用于已准备好本地 memstick 的独立模拟器副本。请先阅读 materials/README.md。'
}
if (Test-Path -LiteralPath (Join-Path $emulatorDir 'installed.txt')) {
    throw '副本含 installed.txt，可能转用原来的用户目录；请先按材料说明准备隔离副本。'
}
if (Get-Process -Name PPSSPPWindows64 -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $Emulator }) {
    throw '该测试副本已经运行，请正常关闭后重试。'
}
if ($State) { $State = (Resolve-Path -LiteralPath $State).Path }
$configPath = Join-Path $emulatorDir 'memstick\PSP\SYSTEM\ppsspp.ini'
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8
if ($config -notmatch '(?m)^EnableCheats\s*=') { throw '副本配置缺少 EnableCheats，请先运行一次并正常退出。' }
$config = $config -replace '(?m)^EnableCheats\s*=.*$', 'EnableCheats = True'
[IO.File]::WriteAllText($configPath, $config, [Text.UTF8Encoding]::new($false))
$cheats = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\cheats\UCAS40234.ini') -Raw -Encoding UTF8
if ($HighHp) { $cheats = $cheats.Replace('_C1 锁HP9999_', '_C0 锁HP9999_').Replace('_C0 锁HP99999_', '_C1 锁HP99999_') }
if ($HighDefense) { $cheats = $cheats.Replace('_C0 防御力9999_', '_C1 防御力9999_') }
$cheatsDir = Join-Path $emulatorDir 'memstick\PSP\Cheats'
New-Item -ItemType Directory -Path $cheatsDir -Force | Out-Null
[IO.File]::WriteAllText((Join-Path $cheatsDir 'UCAS40234.ini'), $cheats, [Text.UTF8Encoding]::new($false))
$emulatorArgs = '"' + $Iso + '"'
if ($State) { $emulatorArgs += ' "--state=' + $State + '"' }
$testProcess = Start-Process -FilePath $Emulator -ArgumentList $emulatorArgs -WorkingDirectory $emulatorDir -WindowStyle Hidden -PassThru
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
$testProcess.Id | Set-Content -LiteralPath (Join-Path $WorkDir 'test-pid.txt')
[PSCustomObject]@{PID=$testProcess.Id; Emulator=$Emulator; WorkDir=[IO.Path]::GetFullPath($WorkDir)} | ConvertTo-Json

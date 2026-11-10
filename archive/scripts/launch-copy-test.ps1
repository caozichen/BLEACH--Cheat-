param([switch]$HighHp, [switch]$HighDefense)
$ErrorActionPreference = 'Stop'
$testRoot = 'F:\死神嘉年华\金手指验证'
$testEmulator = Join-Path $testRoot 'PPSSPP-1.19.3'
$candidate = Get-Content -LiteralPath (Join-Path $testRoot 'UCAS40234.repaired.ini') -Raw -Encoding utf8
if ($HighHp) {
    $candidate = $candidate.Replace('_C1 锁HP9999_', '_C0 锁HP9999_').Replace('_C0 锁HP99999_', '_C1 锁HP99999_')
}
if ($HighDefense) {
    $candidate = $candidate.Replace('_C0 防御力9999_', '_C1 防御力9999_')
}
[IO.File]::WriteAllText((Join-Path $testEmulator 'memstick\PSP\Cheats\UCAS40234.ini'), $candidate, [Text.UTF8Encoding]::new($false))
$testIso = 'F:\死神嘉年华\(PSP)死神 灵魂嘉年华\灵魂嘉年华（魂之狂欢)【需要解压】\灵魂嘉年华（魂之狂欢)【需要解压】\灵魂嘉年华（魂之狂欢).iso'
$testState = Join-Path $testEmulator 'memstick\PSP\PPSSPP_STATE\UCAS40234_1.00_0.ppst'
$testArgs = '"' + $testIso + '" "--state=' + $testState + '"'
$testProcess = Start-Process -FilePath (Join-Path $testEmulator 'PPSSPPWindows64.exe') -ArgumentList $testArgs -WorkingDirectory $testEmulator -WindowStyle Hidden -PassThru
$testProcess.Id | Set-Content -LiteralPath (Join-Path $testRoot 'attack-test-pid.txt')
$testProcess | Select-Object Id,ProcessName

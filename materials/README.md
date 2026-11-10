# 预备材料与复现步骤

## 仓库内已有的材料

| 材料 | 用途 |
|---|---|
| `UCAS40234.original.ini` | 生成器输入，原始未修复 27 项金手指 |
| `ram/stage-RAM.dump` | 原金手指启用时的关卡 RAM，复核代码、指针和原攻击字段 |
| `ram/current-RAM.dump` | 世界地图场景 RAM，保留早期参照 |
| `ram/manifest.json` | 上述两份文件的大小、PSP 基址及 SHA-256 |
| `../evidence/` | 指针定位、离线检查和实际运行读回的原记录 |
| `../reference/` | PPSSPP v1.19.3 解释器、调试接口和内存映射源码 |
| `../archive/` | 原始一次性工作脚本、报告和未成功的 WebSocket 试验 |

两份快照均为从 PSP 地址 `0x08800000` 起导出的 `0x1800000` 字节，即 24 MiB；它们是分析输入，不是可独立运行的应用或游戏镜像。关卡快照是在修复前导出，不能把其中仍为零的攻击加成误认为修复版未生效。修复后的实际值记录在 `evidence/combined-runtime-validation.json`。

## 本机自行准备的运行条件

- PPSSPP v1.19.3 Windows x64，官方来源：https://www.ppsspp.org/ 。
- UCAS40234 / 1.00 的游戏镜像；其他地区、修改版和续作不能直接套用本项目的地址。
- 普通游戏存档；若需要直接进入同一关卡，也可以自行复制本机的 PPSSPP 即时存档。
- PowerShell 7、Node.js 20+；只读检查需要 Python x64；反汇编另安装 `requirements-analysis.txt`。

游戏镜像、PPSSPP 程序和资产、个人普通存档及即时存档、已安装的 Capstone 二进制均不随源码提供。Git 提交前的 `evidence/package-manifest.json` 列出实际纳入仓库的全部内容和哈希。

## 准备独立测试副本

1. 将 PPSSPP v1.19.3 的程序和 assets 复制到专用测试目录，例如 `D:\PPSSPP-Test`，保留原模拟器目录。
2. 将测试目录内的 `installed.txt` 移出测试目录；该文件可能使副本转用原用户的记忆棒。不要改动原安装的同名文件。
3. 准备测试目录下的 `memstick\PSP`。如需要存档，从原记忆棒复制 `SAVEDATA` 和 `PPSSPP_STATE` 到测试副本；避免让测试目录与原目录共用同一记忆棒。
4. 手工启动该副本一次，在设置中确认记忆棒指向测试目录并正常退出，让 `memstick\PSP\SYSTEM\ppsspp.ini` 生成。
5. 之后使用 `Start-Test.ps1`；它只接受已存在本地 memstick 配置且没有 `installed.txt` 的目录，写入测试目录金手指并启用副本的 `EnableCheats`。

```powershell
pwsh -File scripts/Start-Test.ps1 `
  -Emulator 'D:\PPSSPP-Test\PPSSPPWindows64.exe' `
  -Iso 'D:\Games\BLEACH.iso' `
  -HighHp -HighDefense
```

启动脚本记录实际 PID 到 `work/test-pid.txt`。默认以隐藏窗口样式启动测试进程；需要手工操作时，可从任务栏切到 PPSSPP。可选参数 `-State 'D:\PPSSPP-Test\memstick\PSP\PPSSPP_STATE\UCAS40234_1.00_0.ppst'` 加载自行准备的即时存档。没有即时存档时从普通存档进入可操控关卡。

## 读取运行效果

在已进入关卡、角色可走动的场景执行：

```powershell
$testPidValue = [int](Get-Content work/test-pid.txt)
python scripts/read_runtime.py --pid $testPidValue --expect-multiplier 32 --expect-hp 99999 --expect-defense 9999
```

脚本核对目标进程为 `PPSSPPWindows64.exe`，用快照中的 64 字节游戏指令定位 PSP RAM，然后读取静态指针及当前角色字段。它不使用 WriteProcessMemory，不改写进程。若系统因进程权限差异而拒绝读取，应在相同用户和权限级别的终端运行。

默认结果保存到 `work/runtime-validation.json`。如果没有启用高 HP 或防御选项，就不要传相应的 `--expect-hp`、`--expect-defense`。校验不符时进程退出码为 1，但仍保存读回结果供排查。

完成后正常关闭测试副本；此脚本不自动关闭模拟器、不自动覆盖普通游戏存档。

## 当前检查结论

2026-10-31 使用副本实际验证了 32 倍攻击字段、HP/最大 HP 99999、防御力 9999 和 SP 999。2026-11-10 整理便携工具时验证了生成一致性、备份安装行为、PowerShell/Python 语法、反汇编入口和材料哈希；没有再次启动游戏进行打怪或受击测试。历史证据与当前工具的检查范围应分别理解。

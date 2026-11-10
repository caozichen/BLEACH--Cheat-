# 验证记录索引

| 文件 | 时间 / 阶段 | 说明 |
|---|---|---|
| `evidence/cheat-analysis.json` | 修复前 | 对原 27 项金手指的结构分析；攻击、备用 SP 和 3 倍速度存在行数问题 |
| `evidence/stage-findings.json` | 修复前关卡 | 记录原静态指针、角色值和旧攻击链；此时六项攻击加成为零 |
| `evidence/attack_KEY_FINDING.txt` | 地址分析完成 | 修正 P+0x918 偏移，解释加成公式和伤害封顶 |
| `evidence/attack-repair-validation.json` | 生成修复版 | 在关卡快照上检查六个目标字段和其他字节不变 |
| `evidence/high-hp-runtime-validation.json` | 运行副本 | 32 倍攻击字段及当前/最大 HP 99999 的实际读回 |
| `evidence/combined-runtime-validation.json` | 最终运行副本 | 六项 3100、HP/最大 HP 99999、防御 9999、SP 999 |
| `evidence/attack-runtime-validation.json` | 最后一次读回 | 被历次检查覆盖后保存的最终记录，与 combined 记录一致 |
| `evidence/original-hashes.json` | 最初材料 | 当时原金手指、模拟器配置和个人存档的哈希，只作来源对照；配置和个人存档本体不发布 |
| `evidence/source-package-checks.json` | 源码整理 | 2026-11-10 的便携生成器、临时目录安装及语法检查结果 |
| `evidence/new-computer-validation.json` | 新电脑使用检查 | 从 GitHub ZIP 下载后的中文路径、全新安装、备份恢复及无开发工具手工复制验证，详见 `docs/new-computer-validation.md` |
| `evidence/package-manifest.json` | 打包 | 仓库内容清单，记录 SHA-256；不自包含自身和本地 Git 元数据 |

运行读回证明代码能执行并写到当前玩家字段；它不能证明所有招式、装备组合、敌人攻击和界面显示都已实战验证。64 倍选项经过源码公式与指令结构校验，未单独记录实战读回。

历史 PID 与宿主进程地址仅标识当时的测试实例，不能在新的电脑或新进程中复用。新检查由脚本重新定位 RAM，并将结果写入 `work/`。

# PPSSPP 参考源码

`ppsspp-v1.19.3/` 收录与本次分析有关的四份 PPSSPP v1.19.3 原始源码及上游许可证。只作为指令解释、调试接口和内存映射的参考，不是完整的模拟器源码或可构建项目。

| 文件 | 上游路径 | 用途 |
|---|---|---|
| `CwCheat-1.19.3.cpp` | `Core/CwCheat.cpp` | 核对 CWCheat 指针命令、附加行计数和跳过行为 |
| `MemMap-1.19.3.cpp` | `Core/MemMap.cpp` | 核对 PSP RAM 的宿主映射方式 |
| `MemorySubscriber-1.19.3.cpp` | `Core/Debugger/WebSocket/MemorySubscriber.cpp` | 调试接口参考，未作为最终成功验证途径 |
| `GameSubscriber-1.19.3.cpp` | `Core/Debugger/WebSocket/GameSubscriber.cpp` | 游戏状态接口参考 |

上游：https://github.com/hrydgard/ppsspp/tree/v1.19.3 。文件的确切下载地址和 SHA-256 见 `manifest.json`。

PPSSPP 上游声明为 GNU GPL v2 或后续版本，完整文本及例外说明见 `ppsspp-v1.19.3/LICENSE.TXT`。这些文件的版权及许可属于各自原作者。

校验整个材料包：

```powershell
python scripts/verify_materials.py
```

如需重新获取上游参考，运行以下命令。脚本会核对已记录的 SHA-256，不会覆盖内容不一致的已有源码：

```powershell
python scripts/fetch_reference.py
# 本机使用 FlClash 时，可为单次命令指定代理：
python scripts/fetch_reference.py --proxy http://127.0.0.1:7890
```

本机 Git 的代理、登录凭据和 CA 文件不属于代码内容，不随仓库发布。

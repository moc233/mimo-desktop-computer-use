# MIMO Desktop Computer Use (Windows MCP)

[English](./README.en.md)

把 **Xiaomi MIMO Desktop** Windows 安装包里的桌面操控运行时封装成通用 **stdio MCP**，让任意支持 MCP 的 AI 客户端操作本机桌面。

**仓库：** [https://github.com/moc233/mimo-desktop-computer-use](https://github.com/moc233/mimo-desktop-computer-use)

---

## 为什么做这个

海外版官网写明提供 **Computer control（Global only）**，但实际安装后 Windows 上用不了。

排查后发现：完整 Computer Use 插件链路目前只对接 **Mac（Apple 芯片）**，Windows 安装包里虽带有桌面运行时 `runtime.ps1`，却未接入主程序。

本项目将该运行时封装为通用 MCP，使 **国内版 / 海外版 MIMO Desktop** 以及其它 MCP 客户端都能在 Windows 上使用桌面操控。

---

## 给 AI 的安装提示词

复制下面整段给 AI 即可：

```text
请安装这个 Windows Computer Use MCP：
https://github.com/moc233/mimo-desktop-computer-use

步骤：
1. git clone 上面仓库（或下载 zip 解压）
2. 运行 python -u smoke_test.py，确认输出 SMOKE OK
3. 在 MIMO Desktop 的 ~/.config/mimocode/mimocode.json 里，mcp 下增加：
   "mimodesk-computer-use": {
     "type": "local",
     "command": ["python", "-u", "仓库路径/computer_use_mcp.py"],
     "environment": { "PYTHONIOENCODING": "utf-8" },
     "enabled": true
   }
   把 python 和仓库路径换成绝对路径。
4. 告诉我：配置只对新会话生效，请新开对话，再试 list_apps。
```

---

## 功能

| 工具 | 说明 |
|------|------|
| `list_apps` / `list_windows` | 列应用、列窗口 |
| `get_app_state` | 界面元素树 + 截图 |
| `click` / `scroll` / `drag` | 点击、滚动、拖拽 |
| `type_text` / `press_key` / `hotkey` / `paste_text` | 键盘输入 |
| `set_value` / `perform_secondary_action` | 写入控件、无障碍动作 |
| `handshake` | 探测运行时 |

密码管理器类进程会被运行时自动拒绝操作。

---

## 手动配置（MIMO Desktop）

```json
"mimodesk-computer-use": {
  "type": "local",
  "command": [
    "C:\\Path\\To\\python.exe",
    "-u",
    "E:\\path\\to\\mimo-desktop-computer-use\\computer_use_mcp.py"
  ],
  "environment": { "PYTHONIOENCODING": "utf-8" },
  "enabled": true
}
```

写入 `~/.config/mimocode/mimocode.json` 的 `mcp` 字段后，**新开会话**生效。

Claude Desktop 请写入 `mcpServers`，`command`/`args` 指向同一 Python 脚本。

---

## 验证

```bash
python -u smoke_test.py
```

看到 `SMOKE OK` 即可。也可在会话中说：**列出桌面上的应用**。

---

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `MIMO_CU_RUNTIME` | 脚本同目录 `runtime.ps1` | 运行时路径 |
| `MIMO_CU_PERSISTENT` | `1` | `1` 常驻进程（更快） |
| `MIMO_CU_TIMEOUT_MS` | `60000` | 超时毫秒 |

---

## 项目结构

```text
computer_use_mcp.py    # stdio MCP
persistent_host.ps1    # 常驻 PowerShell 宿主
runtime.ps1            # 运行时（来自 MIMO Desktop 安装包）
smoke_test.py          # 冒烟测试
README.md              # 中文说明（本文）
README.en.md           # English
```

---

## 许可证

- MCP 封装代码：MIT，见 [LICENSE](./LICENSE)
- `runtime.ps1`：提取自 Xiaomi MIMO Desktop，版权归原方，见 [NOTICE-runtime.md](./NOTICE-runtime.md)

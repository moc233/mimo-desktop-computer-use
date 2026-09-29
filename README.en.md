# MIMO Desktop Computer Use (Windows MCP)

[中文](./README.md)

Package the Windows desktop-automation runtime shipped with **Xiaomi MIMO Desktop** into a generic **stdio MCP**, so any MCP-capable AI client can drive the local desktop.

**Repository:** [https://github.com/moc233/mimo-desktop-computer-use](https://github.com/moc233/mimo-desktop-computer-use)

---

## Why this exists

The overseas product page advertises **Computer control (Global only)**, but on Windows the official Computer Use plugin does not actually work.

Investigation shows the full plugin path is wired for **macOS (Apple silicon)** only. The Windows installer still ships a runtime (`runtime.ps1`), but it is not connected to the desktop shell.

This project wraps that runtime as a generic MCP so **MIMO Desktop (CN / global)** and other MCP clients can use desktop control on Windows.

---

## Install prompt for your AI

Paste this block into your AI assistant:

```text
Please install this Windows Computer Use MCP:
https://github.com/moc233/mimo-desktop-computer-use

Steps:
1. git clone the repo above (or download and unzip)
2. Run: python -u smoke_test.py  and confirm SMOKE OK
3. For MIMO Desktop, add to mcp in ~/.config/mimocode/mimocode.json:
   "mimodesk-computer-use": {
     "type": "local",
     "command": ["python", "-u", "<repo-path>/computer_use_mcp.py"],
     "environment": { "PYTHONIOENCODING": "utf-8" },
     "enabled": true
   }
   Replace python and repo path with absolute paths.
4. Tell me: MCP config applies to new sessions only — open a new chat and test list_apps.
```

---

## Tools

| Tool | Description |
|------|-------------|
| `list_apps` / `list_windows` | List apps / windows |
| `get_app_state` | UI element tree + screenshot |
| `click` / `scroll` / `drag` | Mouse |
| `type_text` / `press_key` / `hotkey` / `paste_text` | Keyboard |
| `set_value` / `perform_secondary_action` | Accessibility |
| `handshake` | Probe runtime |

Password-manager processes are blocked by the runtime.

---

## Manual config (MIMO Desktop)

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

Add under `mcp` in `~/.config/mimocode/mimocode.json`, then **start a new session**.

For Claude Desktop, add the same script under `mcpServers`.

---

## Verify

```bash
python -u smoke_test.py
```

Expect `SMOKE OK`. In chat, try: **list the apps on my desktop**.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIMO_CU_RUNTIME` | `./runtime.ps1` | Runtime path |
| `MIMO_CU_PERSISTENT` | `1` | `1` = long-lived process (faster) |
| `MIMO_CU_TIMEOUT_MS` | `60000` | Timeout in ms |

---

## Layout

```text
computer_use_mcp.py    # stdio MCP server
persistent_host.ps1    # Persistent PowerShell host
runtime.ps1            # Runtime from MIMO Desktop installer
smoke_test.py          # Smoke test
README.md              # Chinese
README.en.md           # English (this file)
```

---

## License

- MCP wrapper: MIT — see [LICENSE](./LICENSE)
- `runtime.ps1`: extracted from Xiaomi MIMO Desktop — see [NOTICE-runtime.md](./NOTICE-runtime.md)

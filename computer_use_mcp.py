#!/usr/bin/env python3
"""
Generic Windows desktop Computer Use MCP (stdio).

Wraps a PowerShell UI-Automation runtime (`runtime.ps1`) that exposes
list/screenshot/click/drag/keyboard tools for local Windows desktops.

Default runtime path: `runtime.ps1` next to this file (bundled extract).
Override with env `MIMO_CU_RUNTIME`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import uuid
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RUNTIME = os.path.join(_HERE, "runtime.ps1")
RUNTIME = os.environ.get("MIMO_CU_RUNTIME", DEFAULT_RUNTIME)
POWERSHELL = os.environ.get(
    "MIMO_CU_POWERSHELL",
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
)
TIMEOUT_MS = int(os.environ.get("MIMO_CU_TIMEOUT_MS", "60000"))
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {
    "name": "windows-computer-use",
    "version": "0.1.0",
}


def _base_props() -> dict:
    return {
        "app": {
            "type": "string",
            "description": "Process name, window title fragment, or pid:<n>",
        },
        "windowId": {"type": ["string", "null"]},
        "windowIndex": {"type": ["integer", "null"]},
        "restoreWindow": {"type": "boolean", "default": False},
        "noScreenshot": {"type": "boolean", "default": False},
    }


def _schema(require_app: bool = True, extra: dict | None = None) -> dict:
    props = _base_props()
    if extra:
        props.update(extra)
    required = ["app"] if require_app else []
    return {"type": "object", "properties": props, "required": required}


TOOLS: list[dict[str, Any]] = [
    {
        "name": "handshake",
        "description": "Probe the Windows computer-use runtime and return capabilities.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_apps",
        "description": "List visible desktop applications with process ids.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_windows",
        "description": "List windows belonging to an application.",
        "inputSchema": _schema(),
    },
    {
        "name": "get_app_state",
        "description": "Read a window's UI element tree and optional screenshot.",
        "inputSchema": _schema(
            extra={
                "includeScreenshot": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include a PNG screenshot in the result",
                }
            }
        ),
    },
    {
        "name": "click",
        "description": "Click an element_index or coordinates in a window.",
        "inputSchema": _schema(
            extra={
                "element": {"type": ["integer", "null"]},
                "x": {"type": ["number", "null"]},
                "y": {"type": ["number", "null"]},
                "mouse_button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "default": "left",
                },
                "click_count": {"type": "integer", "minimum": 1, "default": 1},
            }
        ),
    },
    {
        "name": "perform_secondary_action",
        "description": "Invoke an accessibility action on an element.",
        "inputSchema": _schema(
            extra={
                "element": {"type": "integer"},
                "action": {"type": "string", "enum": ["invoke", "select", "toggle"]},
            }
        ),
    },
    {
        "name": "scroll",
        "description": "Scroll a window or coordinates.",
        "inputSchema": _schema(
            extra={
                "element": {"type": ["integer", "null"]},
                "x": {"type": ["number", "null"]},
                "y": {"type": ["number", "null"]},
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "left", "right"],
                    "default": "down",
                },
                "pages": {"type": "number", "minimum": 0.1, "default": 1},
            }
        ),
    },
    {
        "name": "drag",
        "description": "Drag from element/coords to element/coords (window-relative).",
        "inputSchema": _schema(
            extra={
                "fromElement": {"type": ["integer", "null"]},
                "toElement": {"type": ["integer", "null"]},
                "from_x": {"type": ["number", "null"]},
                "from_y": {"type": ["number", "null"]},
                "to_x": {"type": ["number", "null"]},
                "to_y": {"type": ["number", "null"]},
            }
        ),
    },
    {
        "name": "type_text",
        "description": "Type text into the target window.",
        "inputSchema": _schema(extra={"text": {"type": "string"}}),
    },
    {
        "name": "press_key",
        "description": "Press a named key (enter, tab, escape, ...).",
        "inputSchema": _schema(extra={"key": {"type": "string"}}),
    },
    {
        "name": "hotkey",
        "description": "Send a hotkey chord, e.g. ctrl+s or alt+tab.",
        "inputSchema": _schema(extra={"key": {"type": "string"}}),
    },
    {
        "name": "paste_text",
        "description": "Paste text via clipboard into the target window.",
        "inputSchema": _schema(extra={"text": {"type": "string"}}),
    },
    {
        "name": "set_value",
        "description": "Set an editable element's value through UI Automation.",
        "inputSchema": _schema(
            extra={"element": {"type": "integer"}, "value": {"type": "string"}}
        ),
    },
]


HOST_PS1 = os.path.join(_HERE, "persistent_host.ps1")
USE_PERSISTENT = os.environ.get("MIMO_CU_PERSISTENT", "1") == "1"
_host_proc: subprocess.Popen | None = None
_host_ready = False


def _spawn_host() -> bool:
    global _host_proc, _host_ready
    if not USE_PERSISTENT or not os.path.isfile(HOST_PS1) or not os.path.isfile(RUNTIME):
        return False
    if _host_proc is not None and _host_proc.poll() is None and _host_ready:
        return True
    try:
        if _host_proc is not None and _host_proc.poll() is None:
            _host_proc.kill()
        _host_proc = subprocess.Popen(
            [
                POWERSHELL,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                HOST_PS1,
                "-RuntimePath",
                RUNTIME,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        # First stdout line is host handshake
        assert _host_proc.stdout is not None
        ready_line = _host_proc.stdout.readline()
        if not ready_line:
            _host_proc.kill()
            _host_proc = None
            return False
        _host_ready = True
        return True
    except Exception:
        _host_proc = None
        _host_ready = False
        return False


def _run_oneshot(op: dict[str, Any]) -> dict[str, Any]:
    if not os.path.isfile(RUNTIME):
        return {
            "ok": False,
            "error": (
                f"runtime.ps1 not found: {RUNTIME}. "
                "Place runtime.ps1 next to computer_use_mcp.py or set MIMO_CU_RUNTIME."
            ),
        }
    op_path = os.path.join(tempfile.gettempdir(), f"cu-{uuid.uuid4().hex}.json")
    with open(op_path, "w", encoding="utf-8") as f:
        json.dump(op, f, ensure_ascii=False)
    try:
        cmd = [
            POWERSHELL,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            RUNTIME,
            "-OperationPath",
            op_path,
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=TIMEOUT_MS / 1000.0,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        if not out:
            err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
            return {"ok": False, "error": err or f"empty stdout exit={proc.returncode}"}
        lines = [ln for ln in out.splitlines() if ln.strip()]
        try:
            return json.loads(lines[-1])
        except json.JSONDecodeError:
            return {"ok": False, "error": f"invalid JSON from runtime: {out[:500]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "runtime timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            os.remove(op_path)
        except OSError:
            pass


def _run_persistent(op: dict[str, Any]) -> dict[str, Any] | None:
    global _host_ready
    if not _spawn_host() or _host_proc is None:
        return None
    try:
        payload = (json.dumps(op, ensure_ascii=False) + "\n").encode("utf-8")
        assert _host_proc.stdin and _host_proc.stdout
        _host_proc.stdin.write(payload)
        _host_proc.stdin.flush()
        line = b""
        # Read one result line (may be large)
        while True:
            chunk = _host_proc.stdout.readline()
            if not chunk:
                _host_ready = False
                return None
            line += chunk
            if line.endswith(b"\n"):
                break
        text = line.decode("utf-8", errors="replace").strip()
        return json.loads(text)
    except Exception:
        _host_ready = False
        try:
            if _host_proc:
                _host_proc.kill()
        except Exception:
            pass
        return None


def run_operation(op: dict[str, Any]) -> dict[str, Any]:
    if USE_PERSISTENT:
        result = _run_persistent(op)
        if result is not None:
            return result
    return _run_oneshot(op)


def strip_screenshot(payload: Any) -> Any:
    if isinstance(payload, dict):
        out = {}
        for k, v in payload.items():
            if k in ("screenshot", "png", "image") and isinstance(v, str) and len(v) > 200:
                out[k] = f"<omitted {len(v)} chars>"
            else:
                out[k] = strip_screenshot(v)
        return out
    if isinstance(payload, list):
        return [strip_screenshot(x) for x in payload]
    return payload


def tool_result(payload: dict[str, Any], include_screenshot: bool) -> list[dict]:
    data = payload if include_screenshot else strip_screenshot(payload)
    text = json.dumps(data, ensure_ascii=False)
    if len(text) > 200_000:
        data = strip_screenshot(payload)
        data["_truncated"] = True
        text = json.dumps(data, ensure_ascii=False)
    return [{"type": "text", "text": text}]


def handle_call(name: str, arguments: dict[str, Any]) -> list[dict]:
    args = dict(arguments or {})
    include_shot = bool(args.pop("includeScreenshot", True))
    if args.get("noScreenshot"):
        include_shot = False
    op: dict[str, Any] = {"tool": name, **args}
    if name == "get_app_state":
        if include_shot:
            op.pop("noScreenshot", None)
        else:
            op["noScreenshot"] = True
    payload = run_operation(op)
    return tool_result(payload, include_screenshot=include_shot)


def send(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method")
        req_id = req.get("id")
        if method == "initialize":
            send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": req.get("params", {}).get(
                            "protocolVersion", PROTOCOL_VERSION
                        ),
                        "capabilities": {"tools": {}},
                        "serverInfo": SERVER_INFO,
                    },
                }
            )
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            known = {t["name"] for t in TOOLS}
            if name not in known:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": f"unknown tool: {name}"}],
                            "isError": True,
                        },
                    }
                )
                continue
            try:
                content = handle_call(name, args)
                is_err = bool(
                    content
                    and content[0].get("text", "").startswith('{"ok":false')
                )
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": content, "isError": is_err},
                    }
                )
            except Exception as e:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": str(e)}],
                            "isError": True,
                        },
                    }
                )
        elif method == "ping":
            send({"jsonrpc": "2.0", "id": req_id, "result": {}})
        elif req_id is not None:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"method not found: {method}",
                    },
                }
            )


if __name__ == "__main__":
    main()

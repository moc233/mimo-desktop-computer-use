#!/usr/bin/env python3
"""Smoke-test the MCP server over stdio (list_apps)."""
import json
import subprocess
import sys
import os

py = sys.executable
server = os.path.join(os.path.dirname(__file__), "computer_use_mcp.py")
proc = subprocess.Popen(
    [py, "-u", server],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)


def send(obj):
    proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
    proc.stdin.flush()


def recv():
    line = proc.stdout.readline()
    if not line:
        err = proc.stderr.read()
        raise RuntimeError(f"server closed: {err}")
    return json.loads(line)


send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "smoke", "version": "0"}}})
print("init:", recv())
send({"jsonrpc": "2.0", "method": "notifications/initialized"})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
tools = recv()
names = [t["name"] for t in tools["result"]["tools"]]
print("tools:", names)
send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "list_apps", "arguments": {}}})
result = recv()
text = result["result"]["content"][0]["text"]
data = json.loads(text)
print("list_apps ok=", data.get("ok"), "n_apps=", len(data.get("apps") or []))
if not data.get("ok"):
    print("ERROR", data)
    sys.exit(1)
print("SMOKE OK")
proc.stdin.close()
proc.terminate()

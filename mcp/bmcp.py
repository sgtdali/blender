"""Blender MCP eklentisinin soketine doğrudan komut gönderir (port 9876).

Kullanım:
  python bmcp.py <komut> [json_parametreler]
  python bmcp.py execute_code --file script.py
Örnek: python bmcp.py get_viewport_screenshot '{"filepath": "C:/tmp/v.png"}'
"""
import json
import socket
import sys


def send(cmd, params=None, timeout=300):
    s = socket.create_connection(("localhost", 9876), timeout)
    s.sendall(json.dumps({"type": cmd, "params": params or {}}).encode("utf-8"))
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            return json.loads(buf.decode("utf-8"))
        except ValueError:
            continue
    return json.loads(buf.decode("utf-8"))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if len(sys.argv) > 3 and sys.argv[2] == "--file":
        params = {"code": open(sys.argv[3], encoding="utf-8").read()}
    else:
        params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    out = send(cmd, params)
    sys.stdout.reconfigure(encoding="utf-8")
    res = out.get("result")
    if isinstance(res, dict) and "result" in res and isinstance(res["result"], str):
        print(res["result"][-6000:])  # execute_code: yalnızca çıktının sonu
    else:
        print(json.dumps(out, ensure_ascii=False, indent=1)[:20000])

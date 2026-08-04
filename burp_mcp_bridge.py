#!/usr/bin/env python3
"""
Burp MCP Bridge - Controls Burp Suite via MCP through Codebuff.
Uses NDJSON format (newline-delimited JSON) and waits for SSE connection.
"""

import os
import subprocess, json, sys, time, threading

# The JAR is resolved relative to this script, so the project works from any
# install location: C:\Burp-MCP-Bridge, C:\Users\<any-user>\Documents\Burp-MCP-Bridge, ...
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
JAR = os.path.join(BASE_DIR, "mcp-proxy-all.jar")
SSE = "http://127.0.0.1:9876"

class MCPClient:
    def __init__(self):
        self.proc = None
        self.lock = threading.Lock()
        self.resps = {}
        self.nid = 1
        self.ready = threading.Event()
        self.conn = threading.Event()

    def start(self):
        if not os.path.isfile(JAR):
            print(f"[!] mcp-proxy-all.jar not found next to this script: {JAR}", flush=True)
            print("[!] Keep burp_mcp_bridge.py and mcp-proxy-all.jar in the same folder", flush=True)
            return self
        print("[*] Starting mcp-proxy-all.jar...", flush=True)
        self.proc = subprocess.Popen(
            ["java", "-jar", JAR, "--sse-url", SSE],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        threading.Thread(target=self._rdout, daemon=True).start()
        threading.Thread(target=self._rderr, daemon=True).start()
        if not self.conn.wait(timeout=15):
            print("[!] Timeout waiting for SSE connection", flush=True)
            return self
        print("[+] SSE connection established", flush=True)
        time.sleep(0.5)
        return self

    def _rdout(self):
        try:
            while self.proc and self.proc.poll() is None:
                line = self.proc.stdout.readline()
                if not line: break
                line = line.decode("utf-8", errors="replace").strip()
                if not line: continue
                try:
                    msg = json.loads(line)
                    if isinstance(msg, dict) and msg.get("id") is not None:
                        with self.lock:
                            self.resps[msg["id"]] = msg
                            self.ready.set()
                except: pass
        except: pass

    def _rderr(self):
        try:
            while self.proc and self.proc.poll() is None:
                line = self.proc.stderr.readline()
                if not line: break
                line = line.decode("utf-8", errors="replace").strip()
                if not line: continue
                print(f"[proxy] {line}", file=sys.stderr, flush=True)
                if "Successfully connected" in line:
                    self.conn.set()
        except: pass

    def _send(self, method, params=None, mid=None):
        if mid is None:
            mid = self.nid; self.nid += 1
        req = {"jsonrpc": "2.0", "id": mid, "method": method}
        if params: req["params"] = params
        data = json.dumps(req, separators=(",", ":")) + "\n"
        if self.proc and self.proc.stdin:
            self.proc.stdin.write(data.encode("utf-8"))
            self.proc.stdin.flush()
        return mid

    def req(self, method, params=None, timeout=15):
        self.ready.clear()
        mid = self._send(method, params)
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if mid in self.resps:
                    r = self.resps.pop(mid)
                    if "error" in r:
                        raise Exception(f"MCP Error: {r['error']}")
                    return r.get("result")
            time.sleep(0.05)
        raise TimeoutError(f"No response for '{method}' after {timeout}s")

    def init(self):
        print("[*] Sending initialize...", flush=True)
        r = self.req("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "codebuff-burp", "version": "1.0.0"}
        })
        si = r.get("serverInfo", {})
        print(f"[+] Initialized: {si.get('name','?')} v{si.get('version','?')}", flush=True)
        print(f"[+] Protocol: {r.get('protocolVersion','?')}", flush=True)
        self._send("notifications/initialized", mid=0)
        return r

    def list_tools(self):
        print("\n[*] Listing tools...", flush=True)
        r = self.req("tools/list", timeout=15)
        tools = r.get("tools", [])
        print(f"[+] Found {len(tools)} tools:\n", flush=True)
        for t in tools:
            name = t.get("name", "?")
            desc = t.get("description", "")
            print(f"  [+] {name}", flush=True)
            print(f"      {desc}", flush=True)
            props = t.get("inputSchema", {}).get("properties", {})
            if props:
                reqs = set(t.get("inputSchema", {}).get("required", []))
                print("      Parameters:", flush=True)
                for pn, pi in props.items():
                    rq = "*required*" if pn in reqs else "optional"
                    print(f"        - {pn} ({pi.get('type','any')}, {rq}): {pi.get('description','')}", flush=True)
            print(flush=True)
        return tools

    def call(self, tool, args=None, timeout=90):
        print(f"\n[*] Calling: {tool}...", flush=True)
        if args: print(f"[*] Args: {json.dumps(args)}", flush=True)
        r = self.req("tools/call", {"name": tool, "arguments": args or {}}, timeout=timeout)
        for item in r.get("content", []):
            if item.get("type") == "text":
                text = item.get('text','')
                safe = text.encode('ascii', errors='xmlcharrefreplace').decode('ascii')
                print(f"[+] Result:\n{safe}", flush=True)
            else:
                safe = json.dumps(item, indent=2, default=str)
                safe = safe.encode('ascii', errors='xmlcharrefreplace').decode('ascii')
                print(f"[+] {safe}", flush=True)
        return r

    def close(self):
        if self.proc:
            self.proc.terminate()
            try: self.proc.wait(timeout=5)
            except: self.proc.kill()

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "list-tools"
    c = MCPClient()
    try:
        c.start()
        if not c.conn.is_set():
            print("[!] Cannot connect to Burp MCP", flush=True)
            sys.exit(1)
        if action == "list-tools":
            c.init(); c.list_tools()
        elif action == "call":
            if len(sys.argv) < 3:
                print("Usage: call <tool_name> [args_json]")
                sys.exit(1)
            c.init()
            c.call(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
        else:
            print(f"Unknown: {action}")
    finally:
        c.close()

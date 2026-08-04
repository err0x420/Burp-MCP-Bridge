#!/usr/bin/env python3
"""
Burp MCP Bridge - one-shot installer.

Running `python install.py` sets up everything a new user needs:

1. Downloads the official PortSwigger MCP stdio proxy (mcp-proxy-all.jar)
   from the PortSwigger/mcp-server repository (pinned commit + SHA-256
   checksum verification, with automatic retries for flaky connections).
2. Installs the bridge script + proxy jar into ~/.burp-mcp/  (the home
   directory is resolved by Python, so this works on Windows, macOS and
   Linux without hardcoding any paths).
3. Installs the global agent skill into
   ~/.agents/skills/burp-mcp/SKILL.md  (the standard skills location used
   by Freebuff / Claude Code) with the resolved absolute path already
   written inside.

After this, any Freebuff session can use the `burp-mcp` skill from any
workspace folder, connecting to the local Burp MCP Server on
127.0.0.1:9876.

The proxy jar is a third-party artifact (PortSwigger, GPL-3.0). This project
does NOT redistribute it - the installer only downloads it from the official
source.

VERSION PINNING
---------------
This bridge is tested against ONE exact proxy build. The URL below is pinned
to the specific repo commit whose libs/mcp-proxy-all.jar we verified, and the
checksum locks the exact bytes. The installer will never install another
build silently: if PortSwigger changes the proxy, this installer fails loudly
until the pinned version and checksum are updated.

To update: download the new proxy, test it with burp_mcp_bridge.py, then
bump PROXY_COMMIT and EXPECTED_SHA256 below.
"""

import hashlib
import os
import pathlib
import shutil
import sys
import time
import urllib.request

JAR_NAME = "mcp-proxy-all.jar"
# Pinned to the exact commit we verified (PortSwigger/mcp-server main, 2026-05-26).
PROXY_COMMIT = "5f76126409780ecba2b766c7f7388f465c5b5f94"
URL = f"https://github.com/PortSwigger/mcp-server/raw/{PROXY_COMMIT}/libs/{JAR_NAME}"
# SHA-256 of the pinned proxy jar (verified 2026-08-04).
EXPECTED_SHA256 = "b376b860f114f67e8301e50b06760f1edd23dd99e860c3646cbeac144ce7821a"

# Retry policy for flaky connections.
MAX_ATTEMPTS = 5
RETRY_DELAY_SECONDS = 3

# Install locations (standard user-directory conventions, resolved by Python).
HOME = pathlib.Path.home()
BURP_DIR = HOME / ".burp-mcp"
BRIDGE_DST = BURP_DIR / "burp_mcp_bridge.py"
JAR_PATH = BURP_DIR / JAR_NAME
SKILL_DIR = HOME / ".agents" / "skills" / "burp-mcp"
SKILL_PATH = SKILL_DIR / "SKILL.md"

# Sources inside this repo.
BASE_DIR = pathlib.Path(__file__).resolve().parent
BRIDGE_SRC = BASE_DIR / "burp_mcp_bridge.py"
SKILL_TEMPLATE_SRC = BASE_DIR / "templates" / "burp-mcp" / "SKILL.md"
PLACEHOLDER = "__BURP_MCP_BRIDGE__"
# The exact Python interpreter that ran this installer (e.g. "python" on
# Windows, "python3" on most Linux). Using the full resolved path guarantees
# the skill's commands work on any OS and with any venv - even when the bare
# name would not be found in PATH. Forward slashes keep it shell-safe.
PYTHON_CMD = sys.executable.replace("\\", "/")
# Marker replaced in the skill template (Python portability: see above).
PYTHON_PLACEHOLDER = "__BURP_MCP_PYTHON__"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    tmp = str(dest) + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "burp-mcp-bridge-installer"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as out:
            shutil.copyfileobj(resp, out)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    os.replace(tmp, dest)


def download_with_retries(url, dest):
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[*] Downloading proxy from {url} (attempt {attempt}/{MAX_ATTEMPTS})", flush=True)
        try:
            download(url, dest)
            return
        except Exception as e:
            last_err = e
            if os.path.exists(str(dest) + ".part"):
                os.remove(str(dest) + ".part")
            if attempt < MAX_ATTEMPTS:
                print(f"[!] Attempt {attempt} failed: {e}", file=sys.stderr)
                print(f"[!] Retrying in {RETRY_DELAY_SECONDS} seconds...", file=sys.stderr)
                time.sleep(RETRY_DELAY_SECONDS)
    raise last_err


def install_skill():
    if not SKILL_TEMPLATE_SRC.is_file():
        print(f"[!] Skill template not found: {SKILL_TEMPLATE_SRC}", file=sys.stderr)
        sys.exit(1)
    template = SKILL_TEMPLATE_SRC.read_text(encoding="utf-8")
    # Forward slashes keep the path shell-safe on every OS (bash/cmd/PowerShell).
    bridge_path = str(BRIDGE_DST).replace("\\", "/")
    skill = template.replace(PYTHON_PLACEHOLDER, PYTHON_CMD)
    skill = skill.replace(PLACEHOLDER, bridge_path)
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    SKILL_PATH.write_text(skill, encoding="utf-8")
    print(f"[+] Skill installed: {SKILL_PATH}", flush=True)


def main():
    if not shutil.which("java"):
        print("[!] Java not found in PATH. The bridge needs Java to run the proxy jar.", file=sys.stderr)
        sys.exit(1)
    if not BRIDGE_SRC.is_file():
        print(f"[!] burp_mcp_bridge.py not found next to this script: {BRIDGE_SRC}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Installing into: {BURP_DIR}", flush=True)
    BURP_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Proxy jar (pinned + checksum verified).
    if JAR_PATH.is_file() and sha256_of(JAR_PATH) == EXPECTED_SHA256:
        print(f"[+] {JAR_NAME} already present and verified. Nothing to do.", flush=True)
    else:
        if JAR_PATH.is_file():
            print(f"[!] Existing {JAR_NAME} does not match the expected checksum; re-downloading.", flush=True)
        try:
            download_with_retries(URL, JAR_PATH)
        except Exception as e:
            print(f"[!] Download failed after {MAX_ATTEMPTS} attempts: {e}", file=sys.stderr)
            print("[!] Check your internet connection and try again.", file=sys.stderr)
            sys.exit(1)
        actual = sha256_of(JAR_PATH)
        if actual != EXPECTED_SHA256:
            JAR_PATH.unlink(missing_ok=True)
            print(f"[!] Checksum mismatch (got {actual}, expected {EXPECTED_SHA256}). File removed.", file=sys.stderr)
            sys.exit(1)
        print(f"[+] Installed {JAR_NAME} ({JAR_PATH.stat().st_size} bytes) with valid checksum.", flush=True)

    # 2) Bridge script.
    shutil.copy2(BRIDGE_SRC, BRIDGE_DST)
    print(f"[+] Bridge installed: {BRIDGE_DST}", flush=True)

    # 3) Global skill.
    install_skill()

    print("\n[+] Done! The 'burp-mcp' skill is now available globally.", flush=True)
    print(f"    - Bridge + proxy: {BURP_DIR}", flush=True)
    print(f"    - Skill:          {SKILL_PATH}", flush=True)
    print("    Start a Freebuff session in any workspace and ask for Burp Suite help.", flush=True)


if __name__ == "__main__":
    main()

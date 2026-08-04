#!/usr/bin/env python3
"""
Burp MCP Bridge - dependency installer.

Downloads the official PortSwigger MCP stdio proxy (mcp-proxy-all.jar)
from the PortSwigger/mcp-server repository and saves it as mcp-proxy-all.jar
next to this script, verifying its SHA-256 checksum.

The proxy jar is a third-party artifact (PortSwigger, GPL-3.0). This project
does NOT redistribute it - the installer only points to the official source.

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
import shutil
import sys
import time
import urllib.request

JAR_NAME = "mcp-proxy-all.jar"
# Pinned to the exact commit we verified (PortSwigger/mcp-server main, 2026-05-26).
PROXY_COMMIT = "5f76126409780ecba2b766c7f7388f465c5b5f94"
URL = f"https://github.com/PortSwigger/mcp-server/raw/{PROXY_COMMIT}/libs/mcp-proxy-all.jar"
# SHA-256 of the pinned proxy jar (verified 2026-08-04).
EXPECTED_SHA256 = "b376b860f114f67e8301e50b06760f1edd23dd99e860c3646cbeac144ce7821a"

# Retry policy for flaky connections.
MAX_ATTEMPTS = 5
RETRY_DELAY_SECONDS = 3

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DEST = os.path.join(BASE_DIR, JAR_NAME)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    tmp = dest + ".part"
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
            if os.path.exists(dest + ".part"):
                os.remove(dest + ".part")
            if attempt < MAX_ATTEMPTS:
                print(f"[!] Attempt {attempt} failed: {e}", file=sys.stderr)
                print(f"[!] Retrying in {RETRY_DELAY_SECONDS} seconds...", file=sys.stderr)
                time.sleep(RETRY_DELAY_SECONDS)
    raise last_err


def main():
    if not shutil.which("java"):
        print(
            "[!] Java not found in PATH. The bridge needs Java to run the proxy jar.",
            file=sys.stderr,
        )
        sys.exit(1)

    if os.path.isfile(DEST):
        if sha256_of(DEST) == EXPECTED_SHA256:
            print(f"[+] {JAR_NAME} already present and verified. Nothing to do.")
            return
        print(f"[!] Existing {JAR_NAME} does not match the expected checksum; re-downloading.")

    try:
        download_with_retries(URL, DEST)
    except Exception as e:
        print(f"[!] Download failed after {MAX_ATTEMPTS} attempts: {e}", file=sys.stderr)
        print("[!] Check your internet connection or try the manual alternative in the README.", file=sys.stderr)
        sys.exit(1)

    actual = sha256_of(DEST)
    if actual != EXPECTED_SHA256:
        os.remove(DEST)
        print(f"[!] Checksum mismatch (got {actual}, expected {EXPECTED_SHA256}). File removed.", file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(DEST)
    print(f"[+] Installed {JAR_NAME} ({size} bytes) with valid checksum. Ready to use.")


if __name__ == "__main__":
    main()

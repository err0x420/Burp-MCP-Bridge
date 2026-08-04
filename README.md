# Burp MCP Bridge for Freebuff

Bring the full power of **Burp Suite** into your **Freebuff** agent.

[Freebuff](https://freebuff.com/) is the free coding agent — `npm install -g freebuff` and you're ready to code. This project bridges Burp Suite's official [MCP Server](https://github.com/PortSwigger/mcp-server) into Freebuff, so your agent can drive Burp directly from the conversation: send HTTP requests, create Repeater tabs, fire Intruder payloads, check Scanner issues, poll Collaborator, and more.

No third-party Python packages required — only the standard library.

## Quick start

A new user gets from zero to "Freebuff driving Burp" in 5 minutes:

1. **Install the tools** — [Python 3](https://www.python.org/downloads/) and [Java 11+](https://www.oracle.com/java/technologies/downloads/). No `pip install` needed.
2. **Install Freebuff** (if you don't have it): `npm install -g freebuff`
3. **Install this bridge** — clone and run the one-command installer:
   ```bash
   git clone https://github.com/err0x420/Burp-MCP-Bridge
   cd Burp-MCP-Bridge
   python install.py
   ```
   This downloads the official proxy jar (checksum-verified), installs the bridge + skill globally into `~/.burp-mcp/` and `~/.agents/skills/`, and **writes the correct path for your machine automatically**. That's it — nothing else to configure.
4. **Open Burp Suite** with the MCP Server extension running (see [Burp Suite setup](#burp-suite-setup)).
5. **Start Freebuff in any folder** (your bug bounty folder, your docs, anywhere) and simply ask, e.g.: *"ayúdame con la sesión de Burp que tengo abierta"*. The agent loads the `burp-mcp` skill and drives Burp for you.

> **Important:** if Freebuff was already open when you ran `install.py`, **close it and start a new session** — skills are loaded at startup.

## Why this project exists

There are already many "Burp MCP bridges" on GitHub, but none of them were made with Freebuff in mind. This one is built specifically for Freebuff users:

- A minimal, dependency-free **Python** bridge you can drop anywhere.
- **One-command setup** that installs the bridge and a **global skill**, so it works from any Freebuff workspace without per-project configuration.
- Works from **any install location** — no hardcoded paths, no usernames in the code, no matter where you put the folder.
- Cross-platform (Windows, macOS, Linux) as long as **Java** and **Python 3** are available.

## Using it with Freebuff

Once `python install.py` has run (see [Installation](#installation)), the **`burp-mcp` skill is installed globally** (`~/.agents/skills/burp-mcp/SKILL.md`), so **any** Freebuff session in **any** workspace folder can drive your Burp Suite automatically — no per-project setup, no paths to type.

1. Make sure Burp Suite is running with the MCP Server extension enabled (see [Burp Suite setup](#burp-suite-setup)).
2. Start Freebuff in **any** workspace folder (a bug bounty folder, your docs folder, …).
3. Just ask, e.g. *"ayúdame con la sesión de Burp que tengo abierta"* or *"lista lo último del historial del proxy"*. The agent loads the skill and drives Burp through the bridge.

Under the hood, the skill tells the agent to run:

```bash
# Discover what Burp can do
python ~/.burp-mcp/burp_mcp_bridge.py list-tools

# Perform actions in Burp
python ~/.burp-mcp/burp_mcp_bridge.py call send_http1_request '{"targetHostname": "example.com", "targetPort": 80, "usesHttps": false, "content": "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"}'
```

The skill actually contains the **full resolved path** (no `~` guessing) — the installer writes it automatically. Freebuff agents can chain these calls into full workflows — e.g. read the proxy history, craft a request, send it, create a Repeater tab, and check the response — all from the same session.

## CLI usage

The commands below run the bridge script directly. If you have already run `python install.py`, the canonical copy lives at `~/.burp-mcp/burp_mcp_bridge.py` (together with the jar) and the `burp-mcp` skill uses that path automatically — so you can run `python ~/.burp-mcp/burp_mcp_bridge.py list-tools` from any folder. To run it from this repo folder instead, keep `mcp-proxy-all.jar` next to `burp_mcp_bridge.py`.

### List all available tools

```bash
python burp_mcp_bridge.py list-tools
```

This is also the default action:

```bash
python burp_mcp_bridge.py
```

### Call a tool

```bash
python burp_mcp_bridge.py call <tool_name> [arguments_json]
```

More examples:

```bash
python burp_mcp_bridge.py call url_encode '{"content": "a b&c"}'

python burp_mcp_bridge.py call base64_decode '{"content": "aGVsbG8="}'

python burp_mcp_bridge.py call get_proxy_http_history '{"count": 10, "offset": 0}'
```

## How it works

```
Freebuff agent ──> burp_mcp_bridge.py (Python MCP client)
                          │  NDJSON over stdin/stdout
                          ▼
              mcp-proxy-all.jar (Java proxy)
                          │  SSE over HTTP
                          ▼
               Burp Suite MCP Server (http://127.0.0.1:9876)
```

The bridge launches the proxy with `java -jar`, speaks NDJSON (newline-delimited JSON) to it, and relays requests to Burp's MCP Server over SSE.

## Requirements

- **Python 3** (3.8+; no `pip install` needed)
- **Java** 11+ available in your `PATH` (to run `mcp-proxy-all.jar`)
- **Burp Suite** (Community or Professional) with the **MCP Server** extension installed and running

## Installation

One command is all it takes:

```bash
git clone https://github.com/err0x420/Burp-MCP-Bridge
cd Burp-MCP-Bridge
python install.py
```

`python install.py` does everything automatically:

1. **Downloads** the official PortSwigger proxy `mcp-proxy-all.jar` (pinned commit + SHA-256 checksum, with retries for flaky connections).
2. **Installs** the bridge + proxy into `~/.burp-mcp/` (your home directory — resolved automatically by Python, works on Windows, macOS and Linux).
3. **Installs the global skill** `burp-mcp` into `~/.agents/skills/burp-mcp/SKILL.md`, with the resolved path already written inside — no paths to type, nothing to configure.

That's it. From then on, any Freebuff session can use the skill from any folder — see [Using it with Freebuff](#using-it-with-freebuff).

> **Tip:** if Freebuff was already running when you ran the installer, restart it once so it picks up the new skill.

> **Version pinning:** the installer always fetches the **exact proxy build this bridge was tested with** (pinned commit + checksum) — never a silent "latest". If PortSwigger ships a new proxy, the installer fails loudly until the new build is verified and the pinned version in `install.py` is updated.

> **Note:** `mcp-proxy-all.jar` is a third-party artifact (PortSwigger, GPL-3.0). This project does **not** redistribute it — it only downloads it from the official source. The skill tells the agent to run the bridge from `~/.burp-mcp/burp_mcp_bridge.py`, which looks for the jar right next to itself.

## Uninstall

Removing this bridge leaves **no residue**. The installer writes to exactly two places, so uninstalling is just deleting them:

```bash
# 1. Remove the bridge + proxy jar installed globally
rm -rf ~/.burp-mcp

# 2. Remove the global Freebuff skill
rm -rf ~/.agents/skills/burp-mcp

# 3. (Optional) delete the cloned repo folder itself
#    cd ..  &&  rm -rf Burp-MCP-Bridge
```

That's it. The installer never touches your `PATH`, environment variables, the Windows registry, pip, npm (it doesn't install `freebuff` for you — that's a separate step), or Burp Suite itself.

**What stays behind (on purpose):**

- **Burp Suite** and its **MCP Server extension** — they are separate tools you manage from Burp's own Extensions tab. Removing the bridge does not remove them.
- **Python and Java** — plain system requirements, not installed by this project.
- **Other skills** you may have in `~/.agents/skills/` — only the `burp-mcp` subfolder is removed.
- **Freebuff itself** — if you also want to uninstall the agent, that's a separate step: `npm uninstall -g freebuff`.

> **Windows (cmd/PowerShell):** the bash commands above work in Git Bash. Equivalent in cmd:
> `rmdir /s /q "%USERPROFILE%\.burp-mcp"` and `rmdir /s /q "%USERPROFILE%\.agents\skills\burp-mcp"`.

## Burp Suite setup

1. In Burp Suite, install the **MCP Server** extension (BApp Store → "MCP Server").
2. Make sure the extension is running and listening on `http://127.0.0.1:9876`.

> **Note:** by default the MCP server has **no authentication configured** and only listens on localhost. Do not expose port `9876` to other networks.

## Available tools

The Burp MCP Server exposes tools for:

- **HTTP** — `send_http1_request`, `send_http2_request`
- **Repeater** — `create_repeater_tab`, `create_repeater_tab_http2`
- **Intruder** — `send_to_intruder`
- **Encoding helpers** — `url_encode`, `url_decode`, `base64_encode`, `base64_decode`, `generate_random_string`
- **Configuration** — `output_project_options`, `set_project_options`, `output_user_options`, `set_user_options`
- **Scanner** — `get_scanner_issues`
- **Collaborator (OOB testing)** — `generate_collaborator_payload`, `get_collaborator_interactions`
- **History** — `get_proxy_http_history`, `get_proxy_http_history_regex`, `get_proxy_websocket_history`, `get_proxy_websocket_history_regex`, `get_organizer_items`, `get_organizer_items_regex`
- **Control** — `set_task_execution_engine_state`, `set_proxy_intercept_state`
- **Editor** — `get_active_editor_contents`, `set_active_editor_contents`

Run `list-tools` to see every tool with its full parameter schema (the exact set depends on your MCP Server extension version — this bridge was verified against v1.1.2 with 27 tools).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `[!] mcp-proxy-all.jar not found next to this script` | Run `python install.py` once, or make sure `mcp-proxy-all.jar` is next to `burp_mcp_bridge.py` |
| The agent doesn't find the `burp-mcp` skill | Re-run `python install.py` — it (re)installs the skill into `~/.agents/skills/burp-mcp/SKILL.md` |
| `Timeout waiting for SSE connection` | Burp Suite must be running with the MCP Server extension enabled on `127.0.0.1:9876` |
| `[Errno 2] No such file or directory: 'java'` | Install Java and make sure `java` is in your `PATH` |
| `[!] Cannot connect to Burp MCP` | Check that the Burp MCP Server extension is actually running |

## Security notes

- Everything runs on `127.0.0.1` (loopback) only.
- The Burp MCP Server has no authentication by default — anyone who can reach port `9876` could drive Burp, so **keep it local**.
- The bridge itself only sends the commands you give it.

## License

© 2026 err0x420. Licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International** license ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)).

- **Free to use, copy, modify and share** — for any **non-commercial** purpose.
- **Attribution required** — you must give credit to the original author.
- **ShareAlike** — derivative works must stay under the same license.

> **Note:** `mcp-proxy-all.jar` is a **third-party artifact** (PortSwigger, **GPL-3.0**) and is **not** covered by this project's license. It is downloaded at install time from the official PortSwigger source — see [Installation](#installation).

## Acknowledgments

- [Freebuff](https://freebuff.com/) — the free coding agent this bridge was built for.
- [PortSwigger MCP Server](https://github.com/PortSwigger/mcp-server) — the official MCP server extension for Burp Suite and the `mcp-proxy-all.jar` proxy.
- [Model Context Protocol](https://modelcontextprotocol.io)

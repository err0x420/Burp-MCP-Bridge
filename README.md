# Burp MCP Bridge for Freebuff

Bring the full power of **Burp Suite** into your **Freebuff** agent.

[Freebuff](https://freebuff.com/) is the free coding agent — `npm install -g freebuff` and you're ready to code. This project bridges Burp Suite's official [MCP Server](https://github.com/PortSwigger/mcp-server) into Freebuff, so your agent can drive Burp directly from the conversation: send HTTP requests, create Repeater tabs, fire Intruder payloads, check Scanner issues, poll Collaborator, and more.

No third-party Python packages required — only the standard library.

## Why this project exists

There are already many "Burp MCP bridges" on GitHub, but none of them were made with Freebuff in mind. This one is built specifically for Freebuff users:

- A minimal, dependency-free **Python** bridge you can drop anywhere.
- Works from **any install location** — the proxy jar is resolved relative to the script, so it doesn't matter where you put the folder or what your username is.
- Cross-platform (Windows, macOS, Linux) as long as **Java** and **Python 3** are available.

## Using it with Freebuff

1. Make sure `burp_mcp_bridge.py` and `mcp-proxy-all.jar` are in the **same folder**, and Burp Suite is running with the MCP Server extension enabled (see [Burp Suite setup](#burp-suite-setup)).
2. Start a Freebuff session in that folder.
3. Ask the agent to drive Burp through the bridge:

```bash
# Discover what Burp can do
python burp_mcp_bridge.py list-tools

# Perform actions in Burp
python burp_mcp_bridge.py call send_http1_request '{"targetHostname": "example.com", "targetPort": 80, "usesHttps": false, "content": "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"}'
```

Freebuff agents can chain these calls into full workflows — e.g. read the proxy history, craft a request, send it, create a Repeater tab, and check the response — all from the same session.

## CLI usage

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

1. Download `burp_mcp_bridge.py` (and `install.py`).
2. Put them in **any folder** (`C:\Burp-MCP-Bridge`, `~/tools/burp-mcp`, … — it doesn't matter).
3. Run the installer to fetch the official PortSwigger proxy:

   ```bash
   python install.py
   ```

   It downloads `mcp-proxy-all.jar` from the official [PortSwigger MCP Server](https://github.com/PortSwigger/mcp-server) repository, verifies its SHA-256 checksum, and saves it as `mcp-proxy-all.jar` next to the script.

   > **Version pinning:** the installer always fetches the **exact proxy build this bridge was tested with** (pinned commit + checksum) — never a silent "latest". If PortSwigger ships a new proxy, the installer fails loudly until the new build is verified and the pinned version in `install.py` is updated.

   *Manual alternative:* download `libs/mcp-proxy-all.jar` from the [PortSwigger repo](https://github.com/PortSwigger/mcp-server) and place it in the same folder (no rename needed).

> **Note:** `mcp-proxy-all.jar` is a third-party artifact (PortSwigger, GPL-3.0). This project does **not** redistribute it — it only downloads it from the official source. The bridge looks for `mcp-proxy-all.jar` right next to itself, so the project runs identically no matter where it is installed.

## Burp Suite setup

1. In Burp Suite, install the **MCP Server** extension (BApp Store → "MCP Server").
2. Make sure the extension is running and listening on `http://127.0.0.1:9876`.

> **Note:** by default the MCP server has **no authentication configured** and only listens on localhost. Do not expose port `9876` to other networks.

## Available tools (27)

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

Run `list-tools` to see every tool with its full parameter schema.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `[!] mcp-proxy-all.jar not found next to this script` | Make sure `mcp-proxy-all.jar` is in the same folder as `burp_mcp_bridge.py` |
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

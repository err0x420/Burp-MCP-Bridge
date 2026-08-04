---
name: burp-mcp
description: Controls the user's Burp Suite session (HTTP requests, Repeater, Intruder, Scanner, Collaborator, proxy history, config, etc.) through the official Burp MCP Server. Use it whenever the user mentions Burp, web requests, findings, or pentesting.
---

# burp-mcp — Burp Suite bridge

El usuario tiene Burp Suite abierto con la extensión oficial "MCP Server" activa.
Para interactuar con su sesión, ejecuta el bridge (Python) indicado abajo.

## Comandos

- Descubrir todo lo que Burp puede hacer (herramientas y parámetros):
  ```
  "__BURP_MCP_PYTHON__" "__BURP_MCP_BRIDGE__" list-tools
  ```
- Ejecutar una herramienta de Burp (los argumentos son JSON):
  ```
  "__BURP_MCP_PYTHON__" "__BURP_MCP_BRIDGE__" call <tool_name> '<json>'
  ```

## Ejemplos

```
"__BURP_MCP_PYTHON__" "__BURP_MCP_BRIDGE__" call get_proxy_http_history '{"count": 10, "offset": 0}'
"__BURP_MCP_PYTHON__" "__BURP_MCP_BRIDGE__" call url_encode '{"content": "a b&c"}'
"__BURP_MCP_PYTHON__" "__BURP_MCP_BRIDGE__" call send_http1_request '{"targetHostname":"example.com","targetPort":80,"usesHttps":false,"content":"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"}'
```

## Notas

- El bridge se conecta al MCP Server de Burp en `http://127.0.0.1:9876` (debe estar corriendo).
- Usa `list-tools` primero para ver la lista completa de herramientas disponibles con sus parámetros.
- Si algo falla al ejecutar, lanza `list-tools` y pega el error al usuario.

<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0006 — MCP server

**Status:** Accepted (implementation is phase 3).

## What we found

- The official SDKs are listed at [modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk)
  and live in the [modelcontextprotocol GitHub org](https://github.com/orgs/modelcontextprotocol/repositories):
  TypeScript, Python, C#, Go, Rust, Ruby, Java, Kotlin, PHP, Swift. **There is no official C++
  SDK.**
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) is MIT
  licensed (compatible).
- Slyce already embeds CPython for plugins (inherited from OrcaSlicer).

## Decision

- `slyce-mcp`: a separate Python process built on the official **Python** MCP SDK, speaking stdio
  (and optionally streamable HTTP) to MCP clients.
- It talks to a running Slyce app through a **local control API** (JSON over a loopback socket,
  random per-session token written to the user data dir). With no app running it can still slice
  headlessly through the Slyce CLI.
- Tool groups: CAD (create/modify features), model import/export, slicing with chosen presets and
  overrides, simulation run + results, printer `status` / `send` / `start`.
- **Confirmation:** every physical or destructive action (start print, heat, move, delete files on
  the printer, overwrite a project) produces a confirmation prompt **inside the Slyce app**; the
  MCP call blocks until the user answers, and a denial is returned to the client as an error.
  The MCP server cannot bypass this because the gate lives in the app.
- The in-app AI assistant ([0010](0010-strengthening-and-ai.md)) calls the same control API.
- Setup docs for Claude Desktop / Claude Code, Codex CLI, and generic MCP clients ship with it.

## Why not a C++ MCP server inside the app

No official C++ SDK, and the brief requires the official SDK. Keeping it out of process also means
a misbehaving client cannot crash the app.

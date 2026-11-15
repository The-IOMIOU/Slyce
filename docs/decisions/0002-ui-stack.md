<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0002 — UI stack: wxWidgets + OpenGL (inherited)

**Status:** Accepted (2026-11-15)

## Context

The brief says to pick the UI stack based on what the forked slicer uses. OrcaSlicer
([0001](0001-base-slicer.md)) is C++17 with wxWidgets for windows, panels and dialogs, an
OpenGL 3D canvas (`GLCanvas3D`), and ImGui for in-canvas overlays (gizmos, the G-code legend).

## Options considered

1. **Keep wxWidgets + OpenGL + ImGui.** Zero porting, native on Windows, macOS, Linux.
2. **Replace the shell with Qt or a web UI (Electron/Tauri) and keep `libslic3r` as a library.**
   A nicer theming story, but every panel, the plater, preset tabs and the Design tab would have to
   be rewritten, and upstream merges of GUI code would stop working. Rejected: it would spend the
   project's effort on re-implementing working UI instead of on Slyce's new features.

## Decision

Keep wxWidgets + OpenGL + ImGui. The "cozy, polished" look is delivered inside this stack:

- **Theme:** OrcaSlicer already has light and dark themes driven by a colour table
  (`StateColor`, `wxGetApp().dark_mode()`); Slyce adds a warm theme to that table rather than
  restyling widgets one by one. *Planned.*
- **Typography:** bundle an open-licence (OFL) font through the existing font loading path.
  *Planned; font not yet chosen.*
- **Animation:** limited to what wx and the GL canvas can do smoothly (canvas transitions,
  ImGui overlays). Native wx widgets do not animate well; we will not promise more than that.
- **Customisation:** shortcuts are already rebindable; panel layout and themes are planned and
  will be stored in `AppConfig`.

## Consequences

- Cross-platform builds use upstream's scripts unchanged.
- Some "funky" UI ideas that need a browser engine are out of scope unless done inside an
  existing `wxWebView` page (OrcaSlicer already uses WebView for the home page and some dialogs).

<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# Slyce architecture

Slyce is a fork of [OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer) (AGPL-3.0), taken at
the `v2.5.1` release tag (upstream commit `eef7710cb102fdb51a9bcdbd9efd61047f44774a`) with the
full upstream history kept, so upstream fixes can be merged rather than re-applied.

This document describes how the Slyce subsystems fit together and which parts are inherited,
adapted or new. Why each part was chosen is in [`docs/decisions/`](decisions/). Status words
used below are exact: **inherited** means it is upstream OrcaSlicer code we have not changed,
**planned** means only a decision record exists, nothing is built yet.

## One process, one codebase

```text
                         Slyce desktop app (C++17, wxWidgets, OpenGL)
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  Design (CAD)    Prepare     Preview     Device    Simulate*   Assistant*    │  GUI tabs
 ├──────────────────────────────────────────────────────────────────────────────┤
 │  libslic3r/CAD   libslic3r (slicing, G-code)   DeviceManager / printer agents │
 │  OCCT + slvs     Arachne, supports, AMS/tool   ├─ Bambu agent (upstream)       │
 │                  changes, Bambu profiles       ├─ Moonraker agent (upstream)   │
 │                                                └─ Slyce Bambu LAN agent*       │
 │  Technique plugins* (planar = default, non-planar)    FEA bridge*            │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │  Embedded Python plugin runtime (upstream) — audit-hook permissions          │
 └───────────────▲───────────────────────────────────────────────▲──────────────┘
                 │ local control API* (JSON over loopback,          │ CLI (headless slice)
                 │ confirmation prompts in the app)                 │
        ┌────────┴─────────┐                              ┌─────────┴─────────┐
        │ slyce-mcp*       │ ← Claude, Codex, other MCP   │ tools/gcode_parity │
        │ (official Python │   clients over stdio         │ (regression diff)  │
        │  MCP SDK)        │                              └────────────────────┘
        └──────────────────┘
                                             * = planned / new in Slyce
```

### Inherited from OrcaSlicer (working today)

| Subsystem | Where | Notes |
| --- | --- | --- |
| Slicing pipeline and G-code | `src/libslic3r/` (`Print.cpp`, `GCode/`) | Same engine Bambu Studio derives from (both descend from PrusaSlicer / Slic3r). |
| Bambu printer profiles | `resources/profiles/BBL*` | Maintained upstream. |
| Prepare / Preview / Device tabs, plate view, object list, process/filament/printer panels, layer slider | `src/slic3r/GUI/` | OrcaSlicer kept Bambu Studio's layout. |
| Parametric CAD "Design" tab | `src/libslic3r/CAD/`, `src/slic3r/GUI/CAD/` | OCCT kernel + vendored SolveSpace `libslvs` solver (GPL-3.0). See [docs/HLSD/design-tab.md](HLSD/design-tab.md). |
| Printer agent boundary | `src/slic3r/Utils/*Agent*` | See [docs/HLSD/printer-agent.md](HLSD/printer-agent.md). |
| Python plugin runtime + permissions | `src/slic3r/plugin/` | See [docs/HLSD/plugin-permissions.md](HLSD/plugin-permissions.md). |
| Rebindable shortcuts registry | `src/slic3r/GUI/Shortcuts.cpp` | See [docs/HLSD/keyboard-shortcuts.md](HLSD/keyboard-shortcuts.md). |
| Headless CLI | `src/OrcaSlicer.cpp` | `--slice`, `--export-3mf`, `--load-settings`, … Used by the parity harness and later the MCP server. |

### Slyce-specific (this repository)

| Subsystem | Status | Decision record |
| --- | --- | --- |
| Fork, history, branding, separate data dir | done (minimal rebrand, see record) | [0009](decisions/0009-fork-history-and-branding.md) |
| G-code parity harness vs Bambu Studio | harness + unit tests written; parity **not yet measured** | [0008](decisions/0008-gcode-parity-harness.md) |
| Bambu LAN agent (MQTT 8883 / FTPS 990 / camera) | planned (phase 2) | [0005](decisions/0005-bambu-connectivity.md) |
| MCP server + local control API | planned (phase 3) | [0006](decisions/0006-mcp-server.md) |
| Fusion-style layout for the Design tab | planned (phase 4) | [0003](decisions/0003-cad-kernel-and-solver.md) |
| Stress simulation (MFEM + CGAL, in-process) | planned (phase 5) | [0004](decisions/0004-fea-solver.md) |
| Bambu presets identical to Bambu Studio 02.09.01.70 | done (all models except H3C); Bambu-only engine features still to port | [0011](decisions/0011-bambu-presets.md) |
| Non-planar technique plugins | research only (phase 6) | [0007](decisions/0007-nonplanar-printing.md) |
| Support-free overhangs (WaveOverhangs port) | planned | [0013](decisions/0013-support-free-overhangs.md) |
| Strengthening + AI design help | planned (phase 7), consumes FEA results and MCP tools | [0010](decisions/0010-strengthening-and-ai.md) |

## Data flow for the core loop

1. **Design** builds a feature recipe (OCCT). *Commit to Plate* converts bodies to `ModelObject`s.
2. **Prepare** holds the `Model` + presets (`PresetBundle`: printer / process / filament).
3. **Slice**: `Print::process()` → `GCode::do_export()` produces G-code (or a `.gcode.3mf`).
4. **Preview** reads the `GCodeProcessor` result.
5. **Device** sends the job through the selected printer agent.

Slyce adds two branches to that loop:

- **Simulate** (planned) takes the same OCCT/mesh geometry, meshes it (CGAL), solves it in-process (MFEM),
  and maps the stress field back onto the model. The stress field is also the input for
  strengthening (ribs, wall counts, stress-following infill density).
- **Technique plugins** (planned) replace the planar layer generator for objects that opt in.
  Planar slicing stays the default and must produce byte-identical output when no technique
  plugin is active.

## Rules that every subsystem follows

- **Research before code.** Every subsystem has a decision record with sources and a licence
  check before code lands. Unknowns are written down as unknowns.
- **AGPL-3.0 compatibility.** Every dependency is checked; see the licence table in
  [decisions/README.md](decisions/README.md).
- **Physical actions need confirmation in the app.** Starting a print, heating, moving axes —
  whether triggered by the UI, a plugin, the AI assistant or an MCP client — goes through one
  confirmation gate in the GUI.
- **No Bambu Lab or Autodesk branding or assets.** We match layout and workflow, not visuals.
- **Upstream stays mergeable.** Slyce changes are kept small and marked `// Slyce:` where they
  touch upstream files, and new subsystems live in their own directories.

## Build

Same as upstream: `build_win.bat -ds` (Windows), `build_linux.sh`, `build_release_macos.sh`.
See [docs/BUILDING.md](BUILDING.md) for the Slyce notes, including a fix for CMake builds whose
curl has no CA bundle.

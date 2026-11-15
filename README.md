<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
<!-- DEMO GIF SLOT: replace the line below with the demo GIF once one is recorded, e.g.
     <p align="center"><img src="docs/media/demo.gif" alt="Slyce demo" width="800"></p> -->
<p align="center"><em>Demo GIF coming soon.</em></p>

# Slyce

**A free, open-source, all-in-one 3D printing app: slicer, parametric CAD, stress simulation,
and an MCP server so AI agents can drive it. Print the way *you* want.**

Slyce is a fork of [OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer), which descends from
[Bambu Studio](https://github.com/bambulab/BambuStudio), [PrusaSlicer](https://github.com/prusa3d/PrusaSlicer)
and [Slic3r](https://github.com/slic3r/Slic3r). All of the slicing engine, the Bambu-style
Prepare / Preview / Device workflow, printer profiles and the parametric Design tab come from
that work, and its authors keep the credit and the copyright.

> **Status: early.** Today Slyce is OrcaSlicer 2.5.1 with a Slyce name and its own settings
> folder, plus the project's architecture, decision records and a G-code parity harness.
> Everything below marked *planned* does not exist yet. See [what works](#what-works-today).

## What Slyce is going to be

| Feature | Status |
| --- | --- |
| Slicer with a Bambu Studio-style layout and Bambu printer profiles | ✅ inherited from OrcaSlicer |
| G-code close to Bambu Studio's for the same model and settings | 🧪 harness built, **parity not yet measured** |
| Parametric CAD (OCCT kernel, constraint sketches, feature timeline) | ✅ inherited Design tab · Fusion-style layout *planned* |
| Direct LAN sending to Bambu printers with an open client | *planned* (phase 2) |
| MCP server for Claude, Codex and other agents | *planned* (phase 3) |
| Stress simulation with printing anisotropy, heatmaps and fix suggestions | *planned* (phase 5) |
| Non-planar printing as technique plugins | *research* (phase 6) |
| Simulation-driven strengthening and an AI design assistant | *planned* (phase 7) |
| Warm, polished UI with deep customisation | *planned*; rebindable shortcuts and Python plugins already inherited |

## What works today

- Everything OrcaSlicer 2.5.1 does (slicing, Bambu and many other printer profiles, Design tab,
  plugins), built from this repository.
- Slyce keeps its settings in its own folder (`%APPDATA%\Slyce`, `~/Library/Application Support/Slyce`,
  `~/.config/Slyce`), so it can sit next to an OrcaSlicer install without touching it.
- `tools/gcode_parity`: a harness that slices the same cases in Bambu Studio and Slyce and reports
  per-category differences. Its self-tests run in CI on Windows, macOS and Linux.

## Design docs

- [Architecture](docs/ARCHITECTURE.md)
- [Decision records](docs/decisions/) — research, sources and licence checks for every subsystem
- [Building](docs/BUILDING.md)

## Building

Same as OrcaSlicer. On Windows: `build_win.bat -d` once for the dependencies, then
`build_win.bat -s`. Details and a fix for a common certificate error: [docs/BUILDING.md](docs/BUILDING.md).

## Bambu printers and Bambu's authorisation change

Since 2025 Bambu firmware restricts third-party control unless the printer is in LAN-only mode with
Developer Mode enabled. Slyce's planned open LAN client targets that mode and will say clearly that it
disconnects the printer from Bambu Cloud. Slyce does not ship Bambu's closed network plugin and does not
implement cloud sending. Full write-up with sources: [decision 0005](docs/decisions/0005-bambu-connectivity.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [CLA note](CLA.md).

## Licence

[GNU Affero General Public License v3.0](LICENSE.txt). Slyce-authored files carry
`Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0`; upstream files keep their original
notices. Slyce is not affiliated with Bambu Lab, Autodesk, Prusa Research or the OrcaSlicer project,
and uses none of their logos or brand assets.

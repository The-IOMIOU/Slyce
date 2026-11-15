<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# Decision records

Each major subsystem gets a record **before** code lands: what exists, what we picked, why,
and whether the licence is compatible with AGPL-3.0. Records say "unknown" or "not verified"
where that is the truth.

| # | Topic | Status |
| --- | --- | --- |
| [0001](0001-base-slicer.md) | Base slicer: fork OrcaSlicer | Accepted |
| [0002](0002-ui-stack.md) | UI stack: wxWidgets + OpenGL (inherited) | Accepted |
| [0003](0003-cad-kernel-and-solver.md) | CAD: OCCT + SolveSpace `libslvs`, Fusion-style layout | Accepted (kernel inherited; layout work planned) |
| [0004](0004-fea-solver.md) | Stress simulation solver and mesher | **Proposed — needs owner decision on a licence question** |
| [0005](0005-bambu-connectivity.md) | Bambu printer connection | Accepted for LAN; cloud rejected for now |
| [0006](0006-mcp-server.md) | MCP server | Accepted |
| [0007](0007-nonplanar-printing.md) | Non-planar printing | Research record; implementation not started |
| [0008](0008-gcode-parity-harness.md) | G-code parity harness vs Bambu Studio | Accepted; harness built, parity not yet measured |
| [0009](0009-fork-history-and-branding.md) | Fork history, branding, copyright headers | Accepted |
| [0010](0010-strengthening-and-ai.md) | Strengthening + AI design help | Proposed |

## Licence compatibility table

Checked against each project's own repository (GitHub licence metadata plus source headers where
the metadata was ambiguous), November 2026.

| Component | Licence | Compatible with AGPL-3.0? | Use |
| --- | --- | --- | --- |
| OrcaSlicer | AGPL-3.0 | Yes (same) | Base of the app |
| Bambu Studio, PrusaSlicer | AGPL-3.0 | Yes | Reference only (parity target) |
| OpenCASCADE (OCCT) | LGPL-2.1 + OCCT exception | Yes | CAD kernel (already linked upstream) |
| SolveSpace `libslvs` | GPL-3.0 | Yes (GPLv3 §13 / AGPLv3 §13) | Sketch solver (already vendored upstream) |
| build123d | Apache-2.0 | Yes (Apache-2.0 → GPLv3/AGPLv3 one-way) | Reference / optional Python plugin |
| CadQuery | Apache-2.0 (GitHub shows NOASSERTION; repo `LICENSE` is Apache-2.0 — re-check before vendoring) | Yes | Reference |
| FreeCAD | LGPL-2.1+ | Yes | Reference for history model |
| Gmsh | GPL-2.0-or-later + linking exception | Yes (used under GPL-3) | Mesher (proposed) |
| CalculiX `ccx` | **GPL-2.0-only** (source headers say "version 2", no "or later") | **No, not for linking or combining.** Separate-program use needs an owner decision | Solver candidate |
| FEniCSx / DOLFINx | LGPL-3.0 | Yes | Solver candidate |
| Elmer | GPL-2.0 (solver) / LGPL-2.1 (libs) — "or later" not verified | Not verified | Not chosen |
| CurviSlicer | AGPL-3.0 | Yes | Non-planar reference |
| S4 Slicer | GPL-3.0 | Yes | Non-planar reference |
| MCP Python SDK | MIT | Yes | MCP server |
| bambulabs_api, ha-bambulab | MIT | Yes | Protocol reference |
| OpenBambuAPI | GFDL-1.3 (documentation) | Docs only; we re-implement from it, we do not copy text into code | Protocol reference |

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
| [0004](0004-fea-solver.md) | Stress simulation: MFEM solver + CGAL mesher, built into the app | Accepted |
| [0005](0005-bambu-connectivity.md) | Bambu printer connection | Accepted for LAN; cloud rejected for now |
| [0006](0006-mcp-server.md) | MCP server | Accepted |
| [0007](0007-nonplanar-printing.md) | Non-planar printing | Research record; implementation not started |
| [0008](0008-gcode-parity-harness.md) | G-code parity harness vs Bambu Studio | Accepted; harness built, parity not yet measured |
| [0009](0009-fork-history-and-branding.md) | Fork history, branding, copyright headers | Accepted |
| [0010](0010-strengthening-and-ai.md) | Strengthening + AI design help | Proposed |
| [0011](0011-bambu-presets.md) | Bambu presets copied exactly from Bambu Studio | Accepted; done for all models except H3C |
| [0012](0012-bambu-engine-parity.md) | Bambu Studio engine behaviour on Bambu printers | In progress |
| [0013](0013-support-free-overhangs.md) | Support-free overhangs: port WaveOverhangs | Accepted; port planned |

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
| Gmsh | GPL-2.0-or-later + linking exception | Yes (used under GPL-3) | Not chosen (CGAL already covers meshing) |
| CGAL (Mesh_3) | GPL-3.0-or-later | Yes | Tet mesher for simulation (already a dependency) |
| MFEM | BSD-3-Clause | Yes | FEA solver, linked into the app |
| Eigen | MPL-2.0 | Yes | Already a dependency |
| CalculiX `ccx` | **GPL-2.0-only** (source headers say "version 2", no "or later") | **No** | Rejected |
| FEniCSx / DOLFINx | LGPL-3.0 | Yes | Not chosen (too heavy to embed) |
| Elmer | GPL-2.0 (solver) / LGPL-2.1 (libs) — "or later" not verified | Not verified | Not chosen |
| CurviSlicer | AGPL-3.0 | Yes | Non-planar reference |
| S4 Slicer | GPL-3.0 | Yes | Non-planar reference |
| WaveOverhangs (OrcaSlicer fork) | AGPL-3.0 | Yes (same) | Support-free overhangs, to be ported |
| arc-overhang (McCulloch, CNC Kitchen, PrusaSlicer integration) | GPL-3.0 | Yes | Reference |
| MCP Python SDK | MIT | Yes | MCP server |
| bambulabs_api, ha-bambulab | MIT | Yes | Protocol reference |
| OpenBambuAPI | GFDL-1.3 (documentation) | Docs only; we re-implement from it, we do not copy text into code | Protocol reference |

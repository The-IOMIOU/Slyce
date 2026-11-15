<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0003 — CAD: OCCT kernel, SolveSpace solver, Fusion-style layout

**Status:** Accepted for kernel and solver (inherited). Layout work planned for phase 4.

## What we found

- OrcaSlicer v2.5.1 already ships a parametric **Design** tab
  ([design-tab.md](../HLSD/design-tab.md), [SKETCHER_TOOL_ARCHITECTURE.md](../CAD/design/SKETCHER_TOOL_ARCHITECTURE.md)):
  - Kernel: OpenCASCADE (OCCT), LGPL-2.1 with exception —
    [Open-Cascade-SAS/OCCT](https://github.com/Open-Cascade-SAS/OCCT).
  - Sketch solver: a vendored subset of SolveSpace's `libslvs`, GPL-3.0 —
    [solvespace/solvespace](https://github.com/solvespace/solvespace). Combining GPLv3 and
    AGPLv3 code is permitted by §13 of both licences.
  - Model = ordered feature recipe replayed on edit (the same idea as FreeCAD's and Fusion's
    timeline), with undo as feature-list snapshots and a versioned, append-only 3MF entry.
- Other projects the brief named, and what we take from them:
  - [build123d](https://github.com/gumyr/build123d) (Apache-2.0) and
    [CadQuery](https://github.com/CadQuery/cadquery): Python OCCT wrappers. Useful as reference
    implementations of fillet/shell/loft calls and as an optional scripting plugin. Not needed as a
    dependency because the C++ app calls OCCT directly.
  - [FreeCAD](https://github.com/FreeCAD/FreeCAD) (LGPL-2.1+): reference for history and
    topological naming problems. OrcaSlicer's design doc explicitly makes face/edge ids
    session-scoped, which is the same problem FreeCAD's TNP work addresses; a robust fix is
    future work.

## Fusion 360 workflow: what has to be matched

Not yet researched in enough depth to implement. Before phase 4 code, write
`docs/cad/fusion-workflow.md` from Autodesk's own product documentation and tutorials, covering:
workspace switcher, toolbar tabs (Solid / Surface / Mesh / Sheet Metal …), Create / Modify /
Construct / Inspect / Insert / Select menus, Browser tree (Document Settings, Named Views, Origin,
Sketches, Bodies, Components), Timeline with rollback marker and feature editing, ViewCube
behaviour, the sketch palette, and the default keyboard shortcuts. Shortcuts listed in the brief
(S, E, Q, D, L) must be checked against that documentation, not assumed.

Gap analysis against the existing Design tab is part of that document.

## Decision

- Keep OCCT and `libslvs` as inherited. Do not write a new solver.
- Phase 4 adapts the Design tab's layout and command set to Fusion's workflow, using Slyce's own
  names and icons (no Autodesk names, icons or assets).
- STEP/STL/3MF/OBJ import and export: OrcaSlicer imports all four (STEP through OCCT in
  `Format/STEP.cpp`). Which exports exist from Prepare and from the Design tab, STEP in
  particular, is not yet checked; that is the first task of phase 4.

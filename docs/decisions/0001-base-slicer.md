<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0001 — Base slicer: fork OrcaSlicer

**Status:** Accepted (2026-11-15)

## Question

Build Slyce on OrcaSlicer, Bambu Studio, PrusaSlicer, or a new core?

## What we found

Facts below were read from each project's GitHub repository on 2026-11-15.

| | OrcaSlicer | Bambu Studio | PrusaSlicer |
| --- | --- | --- | --- |
| Repo | [OrcaSlicer/OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer) | [bambulab/BambuStudio](https://github.com/bambulab/BambuStudio) | [prusa3d/PrusaSlicer](https://github.com/prusa3d/PrusaSlicer) |
| Licence | AGPL-3.0 | AGPL-3.0 | AGPL-3.0 |
| Latest release | v2.5.1 (2026-11-14) | v02.09.01.70 (2026-11-03) | 2.9.7 (2026-11-02) |
| Stars | ~16.5k | ~5.3k | ~9.5k |
| Bambu printer profiles | Yes (`resources/profiles/BBL*`) | Yes (vendor) | No |
| Bambu-style UI (Prepare / Preview / Device, plate view, AMS) | Yes — derived from Bambu Studio | Yes (the original) | No (different layout) |
| Multi-vendor profiles | Many vendors | Bambu only | Prusa + community |
| Parametric CAD | **Yes — "Design" tab on OCCT with SolveSpace's solver** ([design-tab.md](../HLSD/design-tab.md)) | No | No |
| Printer agent abstraction (Bambu, Moonraker, plugin-provided) | Yes ([printer-agent.md](../HLSD/printer-agent.md)) | Bambu only | PrusaLink/OctoPrint etc. |
| Python plugin runtime with permission model | Yes ([plugin-permissions.md](../HLSD/plugin-permissions.md)) | No | No |
| Rebindable shortcuts | Yes ([keyboard-shortcuts.md](../HLSD/keyboard-shortcuts.md)) | No | Limited |
| Headless CLI | Yes ([wiki](https://www.orcaslicer.com/wiki/cli/cli_mode)) | Yes ([wiki](https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage)) | Yes |

Lineage: Bambu Studio is a fork of PrusaSlicer; OrcaSlicer is a fork of Bambu Studio. All three
share `libslic3r`, so OrcaSlicer's G-code generator is a close relative of Bambu Studio's.

A from-scratch core was rejected immediately: G-code generation, Arachne variable-width perimeters,
supports, AMS/tool-change sequencing and printer profiles represent years of tested work, and the
project rule is to reuse proven code.

## Decision

**Fork OrcaSlicer**, at release `v2.5.1`, keeping upstream history.

Why OrcaSlicer over Bambu Studio, even though Bambu Studio is the G-code parity target:

1. It already has most of what Slyce asks for: a Bambu-style layout, Bambu profiles, an OCCT CAD
   tab with a real constraint solver, a printer-agent boundary for open LAN clients, a Python
   plugin system with permissions, and rebindable shortcuts. Starting from Bambu Studio would
   mean re-porting all of that.
2. It is multi-vendor, which supports "print how you want".
3. It is the most active of the three (most stars, daily commits).

The cost: OrcaSlicer's G-code is **not** identical to Bambu Studio's (it diverged in features and
defaults). Parity therefore has to be measured and narrowed with the harness in
[0008](0008-gcode-parity-harness.md); we do not assume it.

## Consequences

- Upstream merges: keep Slyce changes small, marked `// Slyce:`, and new subsystems in their own
  directories.
- Build system, dependencies and CI are OrcaSlicer's. See [docs/BUILDING.md](../BUILDING.md).

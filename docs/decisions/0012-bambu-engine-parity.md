<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0012 — Bambu Studio engine behaviour on Bambu printers

**Status:** In progress. Loop direction ported; the rest are planned, in order of measured impact.

## Why

[0011](0011-bambu-presets.md) made the presets identical. Identical presets are not identical
G-code: OrcaSlicer's engine diverged from Bambu Studio's, and some settings in Bambu's P1S/P2S
presets drive Bambu Studio features that Slyce's engine does not have. Bambu Studio is AGPL-3.0, so
its code can be ported into Slyce with attribution.

## Rule for every port

- **Only on Bambu printers** (`Print::is_BBL_printer()`), so other printers keep OrcaSlicer's
  behaviour, and gated by the same setting key Bambu uses, so Bambu's presets drive it unchanged.
- Cite the Bambu Studio file and function in a `// Slyce:` comment at the change.
- A regression test in the matching suite, and a parity-harness run against Bambu Studio
  02.09.01.70 before and after.

## Features (from the P1S/P2S presets, Bambu Studio 02.09.01.70)

| Feature | Bambu source | P1S | P2S | Status |
| --- | --- | --- | --- | --- |
| Loop direction: every loop, holes included, one direction from the printer's `print_in_clockwise` | `GCode.cpp` `GCode::extrude_loop` | ✓ (CCW) | ✓ (CW) | **Ported** (`PerimeterGenerator::loop_counter_clockwise`, test in `tests/fff_print/test_perimeters.cpp`). OrcaSlicer ran holes opposite to contours, so this changed P1S holes too. On Bambu printers the process setting *Wall loop direction* is greyed out; *Print loops clockwise* is in the printer settings. OrcaSlicer's *reverse on odd* overhang option runs after it and still works. |
| Monotonic-line top surface with gap fill and link extension (`monotonic_travel_into_wall`) | `Fill/FillRectilinear.cpp` `FillMonotonicLineWGapFill`, `plan_monotonic_route`, `append_monotonic_route`; `ExtrusionEntity.hpp` `extrusion_entities_append_paths_with_wipe` | top surface on 24/29 processes | 45 % on all processes | **Ported, not yet compiled or measured.** OrcaSlicer had replaced this class with PrusaSlicer's `FillMonotonicLines`, so Bambu-printer top surfaces differed. `Layer::make_fills` now uses Bambu's class for `monotonicline` top surfaces on Bambu printers; `monotonic_travel_into_wall` is a process setting with Bambu's key, limits and default. |
| Floating vertical shells (`detect_floating_vertical_shell`) | `PrintObject.cpp` (shell discovery), `Fill/FillFloatingConcentric.cpp` (984 lines), surface type `stFloatingVerticalShell`, role `erFloatingVerticalShell` | ✓ | ✓ | Planned. Large: new surface type, role and fill. |
| Cooling slowdown `uniform_cooling` | `GCode/CoolingBuffer.cpp` | ✓ | ✓ | Likely already equivalent: uniform is the classic proportional/non-proportional slowdown OrcaSlicer inherited; Bambu's new path is `consistent_surface`, unused by these presets. To confirm with the harness. |
| Preheat next filament before AMS change (`filament_pre_heating_enabled`) | `GCode/WipeTower.cpp`, `GCode/GCodeProcessor.cpp` | ✓ | ✓ | Planned; multi-colour prints only. |
| Prime tower line ironing (`prime_tower_line_ironing`) | `GCode/WipeTower.cpp` | ✓ | ✓ | Planned; multi-colour prints only. |

## Measuring

`tools/gcode_parity` slices the same cases in Bambu Studio 02.09.01.70 and Slyce. A case with a
hole is needed to see the loop-direction change; one with a top surface for the monotonic-line fill.
Results go in `docs/parity/` with the exact versions and commands. No parity claim without them.

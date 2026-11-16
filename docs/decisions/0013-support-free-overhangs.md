<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0013 — Support-free overhangs (arc / wave overhangs)

**Status:** Accepted (research done, 2026-11-16). Port planned after the current Bambu parity work.

## Goal

Print horizontal (up to 90°) overhangs with no support material, by laying down rings that each bond
to the previous ring in the same layer, spreading outward from the supported edge.

## What exists

| Work | What it is | Code | Licence |
| --- | --- | --- | --- |
| Steven McCulloch, *Arc Overhang* (2022) | The original technique: concentric arcs grown from the supported edge. Python, generates G-code for one overhang. | [stmcculloch/arc-overhang](https://github.com/stmcculloch/arc-overhang) (~480★) | GPL-3.0 |
| CNC Kitchen fork | Tuning of the above, documented in [CNC Kitchen's write-up](https://www.cnckitchen.com/blog/arc-overhangs-in-prusaslicer) | [CNCKitchen/arc-overhang](https://github.com/CNCKitchen/arc-overhang) | GPL-3.0 |
| Nicolai Wachenschwan, PrusaSlicer integration | Post-processing script: finds bridge-infill regions in PrusaSlicer G-code and replaces them with arcs ([Hackaday, 2023](https://hackaday.com/2023/02/28/arc-overhangs-in-prusaslicer-are-a-simple-script-away)) | [nicolai-wachenschwan/arc-overhang-prusaslicer-integration](https://github.com/nicolai-wachenschwan/arc-overhang-prusaslicer-integration) (~370★) | GPL-3.0 |
| **WaveOverhangs** (2026) | A fork of **OrcaSlicer** that builds the rings natively in the slicer: a seed band along the supported edge, then wavefronts offset outward, each bonding to the last ([Hackaday, 2026](https://hackaday.com/2026/04/28/new-slicer-enables-horizontal-overhangs-without-support/), [site](https://waveoverhangs.com/)). 30+ settings, Smart / Monotonic / ZigZag traversal, wall carving, end-of-line retraction, corner-aware spacing, per-region perimeter speed. | [dennisklappe/OrcaSlicer-WaveOverhangs](https://github.com/dennisklappe/OrcaSlicer-WaveOverhangs) (~600★, 69 commits, active Oct 2026) | AGPL-3.0 |
| OrcaSlicer "make overhang printable" | Already in Slyce: reshapes steep overhangs into printable cones. A different idea: it changes the geometry instead of printing the overhang flat. | in tree | AGPL-3.0 |

**Credits** (from the fork's source headers and README): wave-overhang algorithm by **Janis A. Andersons**,
building on the arc-overhang algorithm by **Steven McCulloch**, who also wrote the PrusaSlicer integration
([stmcculloch/PrusaSlicer-WaveOverhangs](https://github.com/stmcculloch/PrusaSlicer-WaveOverhangs)); OrcaSlicer
port by **Dennis Klappe**. Research: *Wave-Inspired Path-Planning Strategy for Support-Free Horizontal
Overhangs in FDM* (2026), SSRN preprint, [doi:10.2139/ssrn.6640458](https://doi.org/10.2139/ssrn.6640458),
dataset [doi:10.17632/xhw8xkjyc2.1](https://data.mendeley.com/datasets/xhw8xkjyc2/1). The early "Kaiser LaSO"
generator was later removed from the fork; only the Andersons algorithm remains. These credits stay in the
ported source files.

Known limitation stated by the fork (`docs/LIMITATIONS.md`): warping of laterally supported overhangs, a
coupled thermal/mechanical problem that cooling alone does not solve.

## Decision

Port **WaveOverhangs** into Slyce.

- **Same codebase.** It is an OrcaSlicer fork, so its code drops into Slyce with adaptation rather than
  a rewrite, and the licence is the same (AGPL-3.0).
- **Self-contained.** The generator lives in its own directory (`WaveOverhangs/`) behind one entry
  point, so it becomes the first overhang technique in Slyce's "printing techniques are plugins" design
  ([ARCHITECTURE.md](../ARCHITECTURE.md)), next to OrcaSlicer's cone method.
- **Proven in use**, with an active issue tracker and community gallery, versus the arc-overhang scripts
  that work on finished G-code only.

## Scope of the port (from the fork's main commit `7bf6ee788` and later fixes)

New: `src/libslic3r/WaveOverhangs/WaveOverhangs.{hpp,cpp}` (≈980 lines at the fork's current head). Hooks: `PerimeterGenerator.cpp`, `PrintObject.cpp`, `GCode.cpp`,
`GCode/CoolingBuffer.cpp`, `Support/TreeSupport.cpp`, `PrintConfig.{hpp,cpp}` (settings),
`GUI/Tab.cpp`, `GUI/ConfigManipulation.cpp`. The fork's base is older than Slyce's (v2.5.1), so each hook
is re-applied by hand, not cherry-picked blindly. Branding, update-check and CI changes from the fork are
not taken.

## Testing (before calling it working)

- Unit tests on the generators: rings stay inside the overhang, each ring touches the previous one,
  growth stops when the area saturates.
- Settings off ⇒ G-code unchanged (parity harness, all Bambu cases).
- Real test prints on the P1S and P2S of the fork's reference overhang models, with photos and notes in
  `docs/overhangs/`, as the brief requires for non-planar work. No "works" claim before those prints.

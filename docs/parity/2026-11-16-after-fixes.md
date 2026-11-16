<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# Parity after the first fixes — 2026-11-16

Same reference, cases and method as the [baseline](2026-11-16-baseline.md). Slyce now includes the
default-value overlay, Bambu's wipe retraction split, layer-change lift height (lazy and instant),
short-travel acceleration, power-loss recovery and the final spiral lift as an arc. All 649 `fff_print`
test cases pass.

## Results

| Case | Total extrusion | Temps / fans / AMS | Z-hop lifts | Accelerations | Est. time |
| --- | --- | --- | --- | --- | --- |
| P1S cube | **+0.0008 %** (was −0.52 %) | identical | **identical** (was 0.6 mm vs 0.4 mm) | 312 vs 310 (was 214) | +1.0 % |
| P1S square tube | −9.2 % (was −10.6 %) | identical | **identical** | 314 vs 314 | +0.2 % |
| P1S overhang ramp (new model) | −1.7 % | identical | **identical** | 237 vs 235 | +1.0 % |
| P2S cube | **+0.0009 %** (was −0.57 %) | fans: 2 extra | lift heights identical; Z-only lifts where Bambu slopes | 312 vs 310 | +22 % |
| P2S square tube | −10.7 % | fans: 2 extra | as above | 314 vs 314 | +26 % |
| P2S overhang ramp | +3.4 % | fans: 2 extra | as above | 237 vs 235 | +25 % |

On the cube, the outer wall is now identical move for move (coordinates, extrusion, wipe after the
wall); the P1S end of print is identical except one object-label line (`M625`).

## Still open

| # | Difference | Notes |
| --- | --- | --- |
| 1 | Narrow regions (square tube, ramp): sparse vs solid infill split, floating vertical shells | Largest remaining gap. Port of Bambu's narrow-region handling (decision 0012). |
| 2 | Sparse/solid infill run in the opposite order in some layers, so the following travel differs (and with it slope vs straight lifts) | Infill ordering; to investigate. |
| 3 | Feedrate on walls differs slightly (e.g. F4931 vs F4759) | Cooling slowdown layer-time estimate. |
| 4 | P2S estimated time +22–26 % | Time estimator; not yet investigated. |
| 5 | Spiral lift centre (`I`/`J`) differs at layer changes | Bambu orients the spiral differently; cosmetic for print quality, to match. |
| 6 | Bed-mesh probe box 2 mm larger each side | Auto-brim area in the first-layer hull; safe. |
| 7 | Fan reset placed just before vs after the first layer marker; object labels `M624`/`M625` | Cosmetic. |

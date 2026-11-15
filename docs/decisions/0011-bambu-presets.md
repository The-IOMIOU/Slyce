<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0011 — Bambu Lab presets copied from Bambu Studio

**Status:** Accepted (2026-11-15). Priority printers: P1S, then P2S.

## Goal

A Bambu printer should print from Slyce the way it prints from Bambu Studio. The first
requirement is that every machine, process and filament preset carries **Bambu Studio's exact
values**.

## Source

Bambu Studio `v02.09.01.70` (commit `56a57d0`), `resources/profiles/BBL/` — AGPL-3.0, the same
licence as Slyce, so copying is permitted. Bundle version `02.09.00.74`.

## What we found (before the sync)

OrcaSlicer 2.5.1's BBL bundle (`02.08.00.16`) is a fork of Bambu's, tuned independently. Resolved
through `inherits` and `include` exactly as the loader does, against Bambu Studio 02.09.01.70:

| Printer | Machine | Process | Filament |
| --- | --- | --- | --- |
| P1S | 4 presets, 12 values differ (`farthest_point_timelapse`, `support_air_filtration`, `extruder_clearance_radius`) | identical | 187 presets differ (1059 values: fan speeds, drying data, softening temperature); 4 Bambu presets missing |
| P2S | 4 presets, 20 values differ (start, end, filament-change and timelapse G-code updated by Bambu in July–August 2026; `support_air_filtration`) | identical | 174 presets differ (fan speeds, `filament_max_volumetric_speed`, air filtration); 4 missing |

Because the parents (`fdm_bbl_3dp_001_common`, `fdm_filament_pla`, …) are shared, every other
Bambu printer was also affected, so **every Bambu printer model except the H3C** was synced the
same way (the H3C is not used by this project and was left out on request).

## How it was done

`tools/bbl_profiles/bbl_profiles.py`:

1. `diff` resolves every preset in both trees (parent → each `include` in order → own keys,
   as `PresetBundle` does), maps Bambu's keys through Slyce's loader (legacy renames,
   ignored keys, unknown keys dropped), and compares.
2. `sync` copies Bambu Studio's files **byte for byte**, except:
   - `filament_id`: Slyce keeps OrcaSlicer's minted `OF…` ids and maps them to Bambu's `GF…`
     catalog ids at the printer boundary through `resources/printers/bambu_filament_ids.json`
     (regenerated from Bambu Studio 02.09.01.70 with upstream's `scripts/update_bambu_filament_ids.py`).
     Copying Bambu's raw ids would break AMS spool matching.
   - Two keys Bambu Studio has no option for (`use_3mf`, `reduce_infill_retraction`) keep their
     existing value in the two base files that set them.
3. Then the upstream profile workflow: `orca_profile_tool.py normalize`, `update-index`,
   `generate-id`, `fix-variant`, and `check` → **0 errors, 0 warnings across all 72 vendors**.

Fixes needed for Bambu's files to pass the checks, none of which change a P1S or P2S print setting:
- `normalize` reorders keys, adds `type` to G-code template files, and removes keys the loader
  ignores anyway.
- Where Bambu writes both `extruder_clearance_radius` and `extruder_clearance_max_radius` (which
  Slyce merges into one key), `normalize` keeps the larger value for collision safety. For P1S
  this means 68 mm instead of 57 mm; it only affects spacing in print-by-object mode.
- `fix-variant` writes per-variant arrays at full width (`["10"]` → `["10","10"]`), which is how
  both loaders pad them anyway.
- Bambu's `fdm_filament_pc.json`, `fdm_filament_pva.json` and `Bambu Lab A2L 0.4 nozzle.json` repeat
  a key; the earlier copy was removed (JSON parsers keep the last one).
- `default_materials` in five machine-model files named filaments that exist in neither tree;
  those names were removed (wizard pre-selection only).
- `0.20mm Steady @BBL A2L` has a "TPU 2.85" nozzle variant that Slyce's engine cannot select; that
  column was removed, keeping the Standard values exact.

## Result

After the sync, every Bambu model (H3C excluded) has **0 differing values** in machine, process
and filament presets, except the `extruder_clearance_radius` safety choice above and the A2L
TPU 2.85 variant.

## What presets cannot fix: Bambu engine features Slyce does not have yet

About 100 settings in Bambu's P1S/P2S presets belong to Bambu Studio features that OrcaSlicer's
engine does not implement, so Slyce drops them on load. Most are off or irrelevant by default. The
ones **switched on** in Bambu's own P1S/P2S presets, which therefore change Bambu's G-code:

| Setting (Bambu value) | P1S | P2S | What it does |
| --- | --- | --- | --- |
| `cooling_slowdown_logic = uniform_cooling` | ✓ | ✓ | Bambu's layer-cooling slowdown algorithm |
| `detect_floating_vertical_shell = 1` | ✓ | ✓ | detects unsupported vertical shells |
| `filament_pre_heating_enabled = 1` | ✓ | ✓ | preheats the next filament before an AMS change |
| `prime_tower_line_ironing = 1` | ✓ | ✓ | prime-tower ironing (multi-colour only) |
| `print_in_clockwise = 1` | | ✓ | perimeter direction |
| `monotonic_travel_into_wall = 45` | | ✓ | travel approach into walls |

**Next step:** port these features from Bambu Studio's engine (AGPL-3.0) into Slyce's
`libslic3r`, P1S-relevant ones first, and confirm each with the G-code parity harness against
Bambu Studio 02.09.01.70. Until then Slyce's G-code for these printers is not identical to Bambu
Studio's, even with identical presets.

## Keeping in sync

Re-run when Bambu Studio ships new profiles:

```bash
python tools/bbl_profiles/bbl_profiles.py diff --bambu <BambuStudio checkout> --slyce . --model "Bambu Lab P1S"
python tools/bbl_profiles/bbl_profiles.py sync --bambu <BambuStudio checkout> --slyce . --model "Bambu Lab P1S" ...
# then the orca_profile_tool.py steps above, bump BBL.json version, and check
```

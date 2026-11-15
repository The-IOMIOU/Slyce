<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# G-code parity harness

Slices the same cases in a reference slicer (Bambu Studio) and in Slyce, then compares the G-code
by category: layers, extrusion per layer and per feature, extrusion move positions, path length,
temperatures, fans, tool changes / AMS commands, and the start and end sequences.
Design and rationale: [decision 0008](../../docs/decisions/0008-gcode-parity-harness.md).

Pure Python 3.10+, standard library only.

```bash
python -m unittest discover -s tests          # self-tests (run in CI)
python -m gcode_parity.run --compare a.gcode b.gcode.3mf
python -m gcode_parity.run --reference <bambu-studio> --candidate <slyce> \
    --reference-profiles <bambu>/resources/profiles --candidate-profiles <slyce>/resources/profiles
```

Exit code is 1 if any category `differs`, so it can gate CI once parity is the goal of a change.

## Cases

`cases/*.json`:

```json
{
  "name": "x1c_pla_cube_20mm",
  "model": "cube_20mm",                       // a generated model name, or a path to a model file
  "settings": ["BBL/machine/....json", "BBL/process/....json"],   // relative to --*-profiles
  "filaments": ["BBL/filament/....json"],
  "extra_args": []
}
```

Generated models (`cube_20mm`, `cylinder_r10_h20`, `overhang_ramp`) avoid third-party model licences.

## Known limits (honest list)

- **Not yet run against a real Bambu Studio binary.** The CLI flags follow both projects' wikis,
  but whether system presets with `inherits` resolve when passed by path must be checked on the
  first run; OrcaSlicer's own test repo flattens inherited presets first for this reason.
- Position comparison only runs on layers whose extrusion move counts match; other layers are
  counted as skipped and the category is marked `differs`.
- Layers are aligned by index, not by Z. A one-layer offset makes everything after it differ —
  which is the correct verdict, but the report will be long.

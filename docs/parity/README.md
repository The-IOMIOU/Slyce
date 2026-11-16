<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# G-code parity reports

Measured differences between Slyce and Bambu Studio for the same model, printer, filament and process.
Each report names the exact builds and how it was produced. Nothing here claims parity that a report
does not show. Method: [decision 0008](../decisions/0008-gcode-parity-harness.md). Engine work driven by
these reports: [decision 0012](../decisions/0012-bambu-engine-parity.md).

| Report | Slyce build | Reference |
| --- | --- | --- |
| [2026-11-16 baseline](2026-11-16-baseline.md) | `241eaae5e5` + presets synced | Bambu Studio 02.09.01.70 (official Windows zip) |
| [2026-11-16 after fixes](2026-11-16-after-fixes.md) | parity fixes in this commit | Bambu Studio 02.09.01.70 |

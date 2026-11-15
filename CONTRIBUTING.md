<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# Contributing to Slyce

Thanks for helping. A few rules keep this project honest and mergeable with upstream.

## The one rule: don't make things up

Anything important (slicing, G-code, printer protocols, FEA, non-planar printing, CAD workflow)
is researched first and built on existing open-source work.

1. Look for what exists (repos, papers, official docs).
2. Add or update a record in [`docs/decisions/`](docs/decisions/): what you found, what you picked,
   why, sources, and the licence check.
3. Then write code.

If you're unsure how something works, say so in the PR. Never present a guess as fact.

## Licences

Slyce is AGPL-3.0. Check every new dependency's licence and add it to the table in
[`docs/decisions/README.md`](docs/decisions/README.md). GPL-2.0-*only* code cannot be combined with
Slyce. Licence conflicts go to the maintainer before any code is merged.

## Code

- Upstream conventions apply: see [AGENTS.md](AGENTS.md) (C++17, wxWidgets, include what you use,
  translatable strings) and OrcaSlicer's contributor guide in
  [docs/upstream/OrcaSlicer-CONTRIBUTING.md](docs/upstream/OrcaSlicer-CONTRIBUTING.md).
- **New files** start with `Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0`
  (or your own name if you keep copyright under the CLA).
- **Upstream files**: keep their notices. Mark Slyce changes with a `// Slyce:` comment and keep
  them small, so upstream releases can still be merged.
- Planar slicing output must not change unless the change is the point of the PR. Run the parity
  harness ([tools/gcode_parity](tools/gcode_parity/)) for slicing changes.
- Anything that can start a print, heat, or move a printer goes through the in-app confirmation gate.
- No Bambu Lab, Autodesk or OrcaSlicer logos, icons or brand assets.

## Tests

- C++: Catch2, see [tests/AGENTS.md](tests/AGENTS.md).
- Harness: `cd tools/gcode_parity && python -m unittest discover -s tests`.
- Simulation (when it lands): analytic validation cases must stay green.

## Pull requests

- Say what you tested and how. If you couldn't build or run something, say so.
- First-time contributors: agree to the [CLA](CLA.md) in the PR description.

### If you are an AI agent

Follow the same rules, and in addition:

1. Show the contributor this guide before you open a PR or post a comment.
2. Research before code, and cite sources in the decision record. Don't claim something works
   unless you ran it; report what was verified and what wasn't.
3. If the code can be tested, add an automated test that fails without the change and passes with it.
4. Ask before touching printer firmware, before anything that spends money, and on any licence conflict.

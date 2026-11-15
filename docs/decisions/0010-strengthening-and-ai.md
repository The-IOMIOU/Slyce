<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0010 — Strengthening and AI design help

**Status:** Proposed (phase 7). Depends on 0004 (FEA) and 0006 (MCP / control API).

## Principles

- **Driven by simulation, not guessed.** Every suggestion (orientation, ribs, fillets, wall count,
  infill density) is evaluated by re-running the solver and shown as before/after stress and
  safety factor.
- **The user decides.** Each change is a proposal the user accepts or rejects individually; accepted
  geometry changes become normal Design-tab timeline features, so they can be edited or rolled back.
- **One API.** The assistant uses the same control API as the MCP server, so anything it does an
  external agent can do too, and vice versa.

## Existing building blocks in the fork

- OrcaSlicer has adaptive infill and per-region modifiers
  ([adaptive-infill.md](../HLSD/adaptive-infill.md)); stress-following infill can be expressed as
  generated modifier volumes with higher density, before writing any new infill pattern.
- Wall count and orientation are already settings / transforms.

## To research before implementation

- Published methods for stress-aligned infill and orientation optimisation for FDM (anisotropy
  aware), with code where available.
- Which LLM provider(s) the assistant supports and how users bring their own key. Default design:
  the assistant is an MCP client, so it can run against any model the user configures.

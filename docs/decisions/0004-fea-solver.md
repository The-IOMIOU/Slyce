<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0004 — Stress simulation: solver and mesher

**Status:** Proposed. **Blocked on an owner decision about a licence question (see below).**

## Requirements (from the brief)

Linear static stress for point and distributed loads, impact, thermal, and internal gas pressure;
orthotropic material properties for printed parts; safety-factor heatmap; validation against
analytic cases in CI. Embeddable on Windows, macOS and Linux.

## Candidates

| | Licence | Notes |
| --- | --- | --- |
| [CalculiX ccx](https://github.com/Dhondtguido/CalculiX) | **GPL-2.0-only.** Source headers read "under the terms of the GNU General Public License as published by the Free Software Foundation(version 2)" with no "or later" clause (checked `src/absolute_relative.f`). | Mature, Abaqus-style input deck, orthotropic materials, static/thermal/dynamic. Used by FreeCAD FEM. |
| [FEniCSx / DOLFINx](https://github.com/FEniCS/dolfinx) | LGPL-3.0 | Very flexible; heavy runtime (Python, PETSc, MPI). Windows support is weaker. |
| [Elmer](https://github.com/ElmerCSC/elmerfem) | GPL-2.0 (solver) / LGPL-2.1 (libraries); "or later" not verified | Multiphysics; large. |
| Code_Aster | GPL-3.0 | Very capable; heavy and Linux-centred. |
| [Gmsh](https://gmsh.info/) (mesher) | GPL-2.0-or-later with a linking exception | Tet meshing from STEP/STL; Python and C++ API. |
| TetGen (mesher) | AGPL-3.0 (TetGen 1.6; to verify against the upstream tarball) | Tet meshing. |

## The licence question

GPL-2.0-only code cannot be combined into an AGPL-3.0 program (the GPLv2 has no compatibility
clause with v3-family licences). So CalculiX **cannot be linked into Slyce**.

It may still be usable as a **separate program**: Slyce writes an input deck, runs `ccx` as a
subprocess, and reads the result files. The FSF's position is that pipes, sockets and command-line
arguments between separate programs are normally "mere aggregation", but that is a legal
judgment, and the brief says licence conflicts go to the owner. **We have not decided this.**

## Proposed decision (pending owner answer)

- **Mesher:** Gmsh (used under GPL-3.0, compatible).
- **Solver, option A (preferred technically):** CalculiX `ccx` as an external, separately
  distributed executable, driven through input files only. Never linked, never patched in-tree.
- **Solver, option B (no licence question):** FEniCSx (LGPL-3.0), run out of process from the
  embedded Python runtime. Heavier install, weaker Windows story.

## Validation plan (applies to either option)

CI cases with closed-form answers, each with a stated tolerance:
1. Cantilever, end point load: tip deflection `δ = F L³ / (3 E I)`, root stress `σ = F L c / I`.
2. Thin-walled cylinder under internal pressure: hoop `σ = p r / t`, axial `σ = p r / (2 t)`.
3. Thick sphere under pressure (Lamé).
4. Uniform bar under thermal expansion with fixed ends: `σ = E α ΔT`.

## Material data

Printed parts are orthotropic: in-plane (along strands) stiffness and strength are higher than
across layers. Sources to read before choosing numbers (not yet extracted):
- Li, Xu, Fang et al., orthotropic interlayer bonding of FDM PLA,
  [UTS repository PDF](https://opus.lib.uts.edu.au/bitstream/10453/186075/2/1-s2.0-S026382312400243X-main.pdf).
- Desktop FDM PLA Z-strength study, [PMC6414919](https://pmc.ncbi.nlm.nih.gov/articles/PMC6414919).
- Orthotropic elastic characterisation of FDM PLA via multi-axial testing,
  [Biopolymer Applications Journal](https://univ-bejaia.dz/revue/baj/article/view/839).

No material numbers will ship until they are traced to one of these (or better) sources.

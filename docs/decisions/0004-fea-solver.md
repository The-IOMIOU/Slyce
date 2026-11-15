<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0004 — Stress simulation: solver and mesher

**Status:** Accepted (2026-11-15). Implementation is phase 5.

## Requirements

- **Built into the app.** The owner's requirement: Slyce is all-in-one, so the solver and mesher
  are compiled into Slyce and run in-process. No external solver executable.
- Linear static stress for point and distributed loads, thermal, internal gas pressure; impact
  (transient); orthotropic material for printed parts; safety-factor heatmap; analytic validation in CI.
- Licence compatible with AGPL-3.0 **for linking**.

## Candidates

| | Licence (checked in each repo) | Linkable into AGPL-3.0? | Notes |
| --- | --- | --- | --- |
| [CalculiX ccx](https://github.com/Dhondtguido/CalculiX) | GPL-2.0-only (source headers: "version 2", no "or later") | **No** | Rejected: cannot be linked, and the owner does not want an external process. |
| [MFEM](https://github.com/mfem/mfem) | BSD-3-Clause | Yes | C++ finite-element library from LLNL. Serial build has no mandatory dependencies. Linear elasticity, diffusion (thermal) and time-dependent examples ship with it. |
| [deal.II](https://github.com/dealii/dealii) | LGPL-2.1-or-later (repo `LICENSE.md`) | Yes | Very capable; heavier build (Boost, TBB, optional PETSc/Trilinos). |
| [libMesh](https://github.com/libMesh/libmesh) | LGPL-2.1 | Yes | Capable; heavier build. |
| [FEniCSx / DOLFINx](https://github.com/FEniCS/dolfinx) | LGPL-3.0 | Yes | Python + PETSc + MPI runtime: too heavy to embed. |
| [CGAL Mesh_3](https://github.com/CGAL/cgal) | GPL-3.0-or-later (`Mesh_3/package_info/Mesh_3/license.txt`) | Yes | Tetrahedral meshing of a closed triangle mesh. **CGAL 6.2.1 is already a Slyce dependency** (`deps/CGAL`). |
| [Gmsh](https://gmsh.info/) | GPL-2.0-or-later + exception | Yes (as GPL-3) | Good mesher, but a new dependency where CGAL already covers the need. |
| Eigen | MPL-2.0 | Yes | Already a dependency; sparse direct/iterative solvers as a fallback. |

## Decision

- **Mesher: CGAL Mesh_3** (already linked; no new dependency).
- **Solver: MFEM**, built serial (no MPI) as a new entry in `deps/`, the same way the other
  dependencies are built.
- Everything runs in-process on a worker thread with progress and cancel, like slicing does.

## Known work and unknowns (not guessed)

- MFEM's stock `ElasticityIntegrator` is isotropic (Lamé λ, μ). Orthotropic printed material
  needs an integrator that takes the full stiffness tensor rotated into each part's layer frame.
  That integrator has to be written (a small, testable class), or taken from an existing MFEM
  example if one is found during implementation; to be checked first.
- Impact: start with an equivalent static load (energy method) clearly labelled as an estimate;
  a transient solve is a later step.
- Internal gas pressure: a pressure traction on the inner surfaces of enclosed cavities. Detecting
  sealed cavities from the sliced geometry (infill + walls) is its own research item.
- Solver performance for ~10⁵–10⁶ unknowns on desktop hardware: to be measured, not assumed.

## Validation plan (CI)

Closed-form cases, each with a stated tolerance:
1. Cantilever, end point load: tip deflection `δ = F L³ / (3 E I)`, root stress `σ = F L c / I`.
2. Thin-walled cylinder under internal pressure: hoop `σ = p r / t`, axial `σ = p r / (2 t)`.
3. Thick sphere under pressure (Lamé).
4. Bar with fixed ends under uniform heating: `σ = E α ΔT`.
5. Orthotropic block under uniaxial load in each material axis: strains match the compliance matrix.

## Material data

Orthotropic properties for FDM parts must be traced to published measurements before any number
ships. Sources to read first:
- Li, Xu, Fang et al., orthotropic interlayer bonding of FDM PLA,
  [UTS repository PDF](https://opus.lib.uts.edu.au/bitstream/10453/186075/2/1-s2.0-S026382312400243X-main.pdf).
- Desktop FDM PLA Z-strength study, [PMC6414919](https://pmc.ncbi.nlm.nih.gov/articles/PMC6414919).
- Orthotropic elastic characterisation of FDM PLA via multi-axial testing,
  [Biopolymer Applications Journal](https://univ-bejaia.dz/revue/baj/article/view/839).

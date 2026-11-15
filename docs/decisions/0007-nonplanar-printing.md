<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0007 — Non-planar printing (research record)

**Status:** Research started. No implementation yet. Nothing here claims to work.

## Prior work found so far

| Work | What it does | Code | Licence |
| --- | --- | --- | --- |
| Etienne, Ray, Panozzo et al., *CurviSlicer: Slightly curved slicing for 3-axis printers*, ACM TOG 2019 ([HAL](https://hal-univ-tlse3.archives-ouvertes.fr/INRIA/hal-02120033v1)) | Optimises a volumetric deformation so planar slicing of the deformed part yields slightly curved layers on a normal 3-axis printer; respects nozzle-angle and layer-thickness bounds. | [mfx-inria/curvislicer](https://github.com/mfx-inria/curvislicer) | AGPL-3.0 |
| Ahlers, Wasserfall, Hendrich, Zhang, *3D Printing of Nonplanar Layers for Smooth Surface Generation*, CASE 2019 ([PDF](https://tams-www.informatik.uni-hamburg.de/publications/2019/case_ahlers_2019.pdf)) | Planar core + non-planar top surfaces, with a max-slope limit from the print-head geometry. | Slic3r fork, `nonplanar` branch, [Zip-o-mat/Slic3r](https://github.com/Zip-o-mat/Slic3r) (GPL-3.0 per the project page) | GPL-3.0 |
| Joshua Bird, *S4 Slicer* | Generic non-planar slicer: deforms the model, slices, and un-deforms toolpaths; targets rotary-axis printers. | [jyjblrd/S4_Slicer](https://github.com/jyjblrd/S4_Slicer) | GPL-3.0 |
| Conical slicing (rotating/tilted nozzle work, xyzdims) | Slices on cones instead of planes. | [xyzdims overview](https://xyzdims.com/tag/non-planar-slicing/) | to check |
| Community overview | Index of projects and papers | [3D-Printing-Discord wiki](https://github.com/3D-Printing-Discord/wiki/wiki/Non-Planar-Printing) | — |

Note: a [Fabbaloo article](https://www.fabbaloo.com/2019/09/possible-patent-infringement-by-non-planar-slic3r-development)
raised a possible patent issue around non-planar slicing. Unverified; to be checked before release.

## Direction (to be confirmed by the research)

- Technique **plugins** behind one interface: `prepare(model, printer_kinematics) → layer surfaces`,
  `toolpaths(surfaces) → paths with per-point Z and extrusion`. Planar is the default plugin and
  must leave existing output byte-identical.
- First candidate: the Ahlers approach (planar body + non-planar top skins limited by max slope),
  because it runs on stock 3-axis Bambu printers. CurviSlicer is the second (more general, needs
  an optimiser).
- Safety checks: nozzle/fan-shroud/gantry collision model per printer (max slope and max
  non-planar height), extrusion scaled by local layer height, and toolpath simulation before any
  print.
- Every claim of "works" requires documented test prints in `docs/nonplanar/`.

## Open questions

- Bambu nozzle/shroud geometry for the max-slope limit: no published numbers found yet; may need
  measuring.
- Whether Bambu firmware accepts the required Z moves within extrusion moves at useful speeds
  (expected yes for G-code `G1` with Z, but must be tested).

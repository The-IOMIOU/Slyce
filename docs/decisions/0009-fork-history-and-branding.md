<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# 0009 — Fork history, branding and copyright headers

**Status:** Accepted (2026-11-15)

## History

The repository contains OrcaSlicer's full git history up to `v2.5.1`, plus the original Slyce
initial commit merged in, plus Slyce commits on top. `upstream` remote =
`https://github.com/OrcaSlicer/OrcaSlicer.git`. Syncing is an ordinary `git merge` of an
upstream release tag.

## Branding

Done now (minimal, low-risk):
- `SLIC3R_APP_NAME` = `Slyce` (window titles, about box, G-code header comment).
- New `SLYCE_DATA_KEY` = `Slyce`: Slyce stores settings, presets and plugins in its own user
  data directory (`%APPDATA%\Slyce`, `~/Library/Application Support/Slyce`, `~/.config/Slyce`),
  so it never touches an OrcaSlicer install's data.

Deliberately **not** changed yet, because each is also a compatibility key:
- `SLIC3R_APP_KEY` stays `OrcaSlicer`: it names the gettext catalog (`OrcaSlicer.mo`), the config
  file, and the `Application` metadata in saved 3MF files that OrcaSlicer/Bambu readers inspect.
- Executable name, installer, icons and OrcaSlicer strings inside the UI and translations.

Planned: our own icon set and app icon, executable `slyce`, and replacing remaining user-visible
"OrcaSlicer" strings — each change tested against 3MF round trips. OrcaSlicer, Bambu Studio and
PrusaSlicer remain credited in the README and About dialog, as the AGPL and good manners require.
No Bambu Lab or Autodesk logos, names or assets are added.

## Copyright headers

The brief asks for `Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0` on every source
file. We apply it to **files Slyce creates**. We do **not** stamp it onto upstream files: those
are copyrighted by OrcaSlicer, Bambu Lab, Prusa Research and other contributors, and replacing or
adding an author line there would misstate authorship. Upstream files that Slyce modifies keep
their notices; the modification is recorded by git history and `// Slyce:` comments (AGPLv3 §5a
requires modified files to carry a notice that they were changed, which those comments do).

## CLA

To keep the option of dual licensing, contributions are accepted under [CLA.md](../../CLA.md).
Note this only covers Slyce's own code: upstream OrcaSlicer code is AGPL-3.0 only, so a
dual-licensed Slyce would have to exclude or replace it.

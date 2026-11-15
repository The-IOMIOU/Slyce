# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
"""Make a system preset self-contained before handing it to a slicer's CLI.

Bambu Studio and Slyce resolve `inherits` only against presets already installed in their bundle.
A preset file passed by path keeps just its own keys, and everything it inherits falls back to the
app's built-in defaults (seen in practice: `top_surface_pattern` came out as zig-zag instead of the
preset's monotonic line). A flattened preset, with every key explicit and no `inherits`, is used as is.

Same approach as OrcaSlicer's own test suite (OrcaSlicer/orca-test-repo, presets.py), extended to
follow `include` templates, which Bambu's machine presets use for their start and end G-code. Keys
are merged in the loaders' order: parent first, then each include in order, then the preset's own.
"""
from __future__ import annotations

import json
from pathlib import Path

# Bookkeeping that identifies a preset rather than describing the print: only the leaf's counts.
LEAF_ONLY = {"name", "from", "setting_id", "filament_id", "instantiation", "version", "is_custom",
             "url", "inherits", "include", "renamed_from", "description"}


class PresetIndex:
    """Every preset JSON under a vendor folder (e.g. resources/profiles/BBL), by name."""

    def __init__(self, vendor_dir: Path):
        self.by_name: dict[str, Path] = {}
        for p in Path(vendor_dir).rglob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(data, dict):
                # A template without a name goes by its file name, as the loaders do.
                self.by_name.setdefault(data.get("name") or p.stem, p)

    def load(self, name: str) -> dict:
        if name not in self.by_name:
            raise ValueError(f"cannot resolve preset {name!r}")
        return json.loads(self.by_name[name].read_text(encoding="utf-8"))


def _resolved(data: dict, index: PresetIndex, stack: tuple[str, ...]) -> dict:
    out: dict = {}
    parent = data.get("inherits")
    if parent:
        if parent in stack:
            raise ValueError(f"inherits cycle at {parent!r}")
        out.update(_resolved(index.load(parent), index, stack + (parent,)))
    includes = data.get("include", [])
    for name in ([includes] if isinstance(includes, str) else includes):
        if name in stack:
            raise ValueError(f"include cycle at {name!r}")
        out.update(_resolved(index.load(name), index, stack + (name,)))
    out.update({k: v for k, v in data.items() if k not in LEAF_ONLY})
    return out


def flatten(leaf_path: Path, vendor_dir: Path, index: PresetIndex | None = None) -> dict:
    """Merge a preset's inherits and include chain into one self-contained config."""
    leaf = json.loads(Path(leaf_path).read_text(encoding="utf-8"))
    if leaf.get("type") not in ("machine", "process", "filament"):
        raise ValueError(f"{leaf_path}: preset has no machine/process/filament type")
    index = index or PresetIndex(vendor_dir)
    merged = _resolved(leaf, index, (leaf.get("name", ""),))
    merged["type"] = leaf["type"]
    merged["name"] = leaf.get("name", Path(leaf_path).stem)
    for key in ("setting_id", "filament_id"):
        if key in leaf:
            merged[key] = leaf[key]
    # A flattened preset is its own root. The CLI takes the system identity from the preset's own name
    # when `from` is "system" (otherwise from `inherits`, now gone), and compatibility checks need it.
    merged["from"] = "system"
    merged["instantiation"] = "true"
    return merged


def flatten_to(leaf_path: Path, vendor_dir: Path, out_dir: Path, index: PresetIndex | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / Path(leaf_path).name
    out.write_text(json.dumps(flatten(leaf_path, vendor_dir, index), indent=2, ensure_ascii=False), encoding="utf-8")
    return out

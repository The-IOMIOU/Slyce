# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
"""Resolve, diff and sync Bambu Lab (BBL) system presets between Bambu Studio and Slyce.

Both apps store presets as JSON files indexed by resources/profiles/BBL.json. A preset's effective
settings are: its parent's (``inherits``), then each ``include`` in order, then its own keys
(the order OrcaSlicer's PresetBundle applies them; see src/libslic3r/PresetBundle.cpp).

Slyce reads Bambu Studio's keys through OrcaSlicer's loader, which renames some legacy keys and
silently drops keys it does not know (PrintConfigDef::handle_legacy). The tool models that so a
diff shows what Slyce will actually end up with.

  python bbl_profiles.py diff --bambu <BambuStudio repo> --slyce <Slyce repo> --model "Bambu Lab P1S"
  python bbl_profiles.py sync --bambu <BambuStudio repo> --slyce <Slyce repo> --model "Bambu Lab P1S"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

META_KEYS = {"type", "name", "inherits", "from", "setting_id", "instantiation", "include",
             "renamed_from", "description", "version", "is_custom_defined", "filament_id",
             "base_id", "upward_compatible_machine"}
INDEX_LISTS = {"machine_model_list": "machine_model", "machine_list": "machine",
               "process_list": "process", "filament_list": "filament"}


# ---------------------------------------------------------------------------------------------
# Option tables read from each app's PrintConfig.cpp
# ---------------------------------------------------------------------------------------------
_ADD = re.compile(r'\badd(?:_nullable)?\(\s*"([A-Za-z0-9_]+)"')
_RENAME = re.compile(r'opt_key\s*==\s*"([A-Za-z0-9_]+)"\s*\)\s*\{\s*opt_key\s*=\s*"([A-Za-z0-9_]+)"')
_IGNORE = re.compile(r"static std::set<std::string> ignore\s*=\s*\{(.*?)\};", re.S)


_ADD_AXIS = re.compile(r'\badd(?:_nullable)?\(\s*"([A-Za-z0-9_]+_)"\s*\+\s*axis\.name')
_OVERRIDE_LIST = re.compile(
    r"filament_extruder_override_keys\s*=\s*\{(.*?)\};", re.S)


def option_keys(print_config_cpp: Path) -> set[str]:
    """Every option key PrintConfigDef defines: literal add("key") calls, the per-axis
    machine limits added in a loop ("machine_max_speed_" + axis.name), and the filament
    retraction overrides generated from filament_extruder_override_keys."""
    text = print_config_cpp.read_text(encoding="utf-8", errors="replace")
    keys = set(_ADD.findall(text))
    for prefix in _ADD_AXIS.findall(text):
        keys.update(prefix + axis for axis in "xyze")
    m = _OVERRIDE_LIST.search(text)
    if m:
        keys.update(re.findall(r'"([A-Za-z0-9_]+)"', re.sub(r"//[^\n]*", "", m.group(1))))
    return keys


@dataclass
class Loader:
    """How OrcaSlicer/Slyce turns a key from a JSON file into its own option key."""
    known: set[str]
    renames: dict[str, str] = field(default_factory=dict)
    ignored: set[str] = field(default_factory=set)

    @classmethod
    def from_source(cls, print_config_cpp: Path) -> "Loader":
        text = print_config_cpp.read_text(encoding="utf-8", errors="replace")
        body = text[text.find("void PrintConfigDef::handle_legacy("):]
        body = body[:body.find("void PrintConfigDef::handle_legacy_composite")]
        renames = dict(_RENAME.findall(body))
        m = _IGNORE.search(body)
        ignored = set(re.findall(r'"([A-Za-z0-9_]+)"', m.group(1))) if m else set()
        return cls(option_keys(print_config_cpp), renames, ignored)

    def map_key(self, key: str) -> str | None:
        key = self.renames.get(key, key)
        if key in self.ignored or key not in self.known:
            return None
        return key


# ---------------------------------------------------------------------------------------------
# Profile tree
# ---------------------------------------------------------------------------------------------
class Tree:
    def __init__(self, repo: Path, loader: Loader | None = None):
        self.root = repo / "resources" / "profiles"
        self.index = json.loads((self.root / "BBL.json").read_text(encoding="utf-8"),
                                object_pairs_hook=OrderedDict)
        self.loader = loader
        self.paths: dict[str, tuple[str, str]] = {}      # name -> (kind, sub_path)
        for list_key, kind in INDEX_LISTS.items():
            for entry in self.index.get(list_key, []):
                self.paths[entry["name"]] = (kind, entry["sub_path"])
        self._raw: dict[str, OrderedDict] = {}
        self._resolved: dict[str, dict] = {}

    def raw(self, name: str) -> OrderedDict:
        if name not in self._raw:
            _, sub = self.paths[name]
            self._raw[name] = json.loads((self.root / "BBL" / sub).read_text(encoding="utf-8"),
                                         object_pairs_hook=OrderedDict)
        return self._raw[name]

    def own_settings(self, name: str) -> dict:
        out = {}
        for k, v in self.raw(name).items():
            if k in META_KEYS:
                continue
            if self.loader is not None:
                k = self.loader.map_key(k)
                if k is None:
                    continue
            out[k] = v
        return out

    def parents(self, name: str) -> list[str]:
        raw = self.raw(name)
        inc = raw.get("include", [])
        inc = [inc] if isinstance(inc, str) else list(inc)
        return ([raw["inherits"]] if raw.get("inherits") else []) + inc

    def closure(self, names) -> set[str]:
        seen: set[str] = set()
        stack = list(names)
        while stack:
            n = stack.pop()
            if n in seen or n not in self.paths:
                continue
            seen.add(n)
            stack.extend(self.parents(n))
        return seen

    def resolved(self, name: str) -> dict:
        if name in self._resolved:
            return self._resolved[name]
        raw = self.raw(name)
        out: dict = {}
        if raw.get("inherits"):
            out.update(self.resolved(raw["inherits"]))
        inc = raw.get("include", [])
        for n in ([inc] if isinstance(inc, str) else inc):
            out.update(self.resolved(n))
        out.update(self.own_settings(name))
        self._resolved[name] = out
        return out

    def instantiated(self, kind: str) -> list[str]:
        return [n for n, (k, _) in self.paths.items()
                if k == kind and str(self.raw(n).get("instantiation", "true")) == "true"]


def presets_for_model(tree: Tree, model: str) -> dict[str, list[str]]:
    machines = [n for n in tree.instantiated("machine") if tree.resolved(n).get("printer_model") == model]
    mset = set(machines)

    def compatible(n: str) -> bool:
        cp = tree.resolved(n).get("compatible_printers", [])
        return bool(mset.intersection(cp))

    return {
        "machine_model": [n for n, (k, _) in tree.paths.items() if k == "machine_model" and n == model],
        "machine": sorted(machines),
        "process": sorted(n for n in tree.instantiated("process") if compatible(n)),
        "filament": sorted(n for n in tree.instantiated("filament") if compatible(n)),
    }


# ---------------------------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------------------------
def _padded_equal(x, y) -> bool:
    """Per-variant arrays are padded by repeating the last value when a preset writes fewer values
    than it has variants (both apps' extend_default_config_length), so ["10"] == ["10", "10"]."""
    if x == y:
        return True
    if isinstance(x, list) and isinstance(y, list) and x and y:
        short, long_ = (x, y) if len(x) <= len(y) else (y, x)
        return long_[:len(short)] == short and all(v == short[-1] for v in long_[len(short):])
    return False


def ignored_keys(tree: Tree, names) -> dict[str, list[str]]:
    """Keys a Bambu Studio preset sets that Slyce's loader drops (unknown or obsolete in Slyce)."""
    out: dict[str, set[str]] = {}
    for n in tree.closure(names):
        for k in tree.raw(n):
            if k not in META_KEYS and tree.loader is not None and tree.loader.map_key(k) is None:
                out.setdefault(k, set()).add(n)
    return {k: sorted(v) for k, v in sorted(out.items())}


def diff_preset(bambu: Tree, slyce: Tree, name: str) -> dict:
    a, b = bambu.resolved(name), slyce.resolved(name)
    return {
        "changed": {k: [a[k], b[k]] for k in sorted(set(a) & set(b)) if not _padded_equal(a[k], b[k])},
        "only_bambu": sorted(set(a) - set(b)),
        "only_slyce": sorted(set(b) - set(a)),
    }


def diff_model(bambu: Tree, slyce: Tree, model: str) -> dict:
    want = presets_for_model(bambu, model)
    have = presets_for_model(slyce, model)
    report = {"model": model, "kinds": {},
              "bambu_keys_slyce_ignores": ignored_keys(bambu, [n for v in want.values() for n in v])}
    for kind in ("machine", "process", "filament"):
        missing = sorted(set(want[kind]) - set(have[kind]))
        extra = sorted(set(have[kind]) - set(want[kind]))
        per = {}
        for n in sorted(set(want[kind]) & set(have[kind])):
            d = diff_preset(bambu, slyce, n)
            if d["changed"] or d["only_bambu"]:
                per[n] = d
        report["kinds"][kind] = {"bambu_count": len(want[kind]), "slyce_count": len(have[kind]),
                                 "missing_in_slyce": missing, "extra_in_slyce": extra,
                                 "differing": per}
    return report


def summarise(report: dict) -> str:
    lines = [f"# BBL preset diff: {report['model']}", ""]
    for kind, r in report["kinds"].items():
        n_changed = sum(len(d["changed"]) for d in r["differing"].values())
        lines.append(f"- **{kind}**: Bambu {r['bambu_count']}, Slyce {r['slyce_count']}; "
                     f"missing in Slyce {len(r['missing_in_slyce'])}, extra in Slyce {len(r['extra_in_slyce'])}; "
                     f"{len(r['differing'])} shared presets differ ({n_changed} values)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# Sync: copy Bambu Studio's files verbatim, keep only Slyce-only keys Bambu does not define
# ---------------------------------------------------------------------------------------------
def sync_model(bambu: Tree, slyce: Tree, model: str, bambu_known: set[str]) -> dict:
    want = presets_for_model(bambu, model)
    names = bambu.closure([n for v in want.values() for n in v])
    log = {"written": [], "added_to_index": [], "kept_slyce_only_keys": {}}
    for name in sorted(names):
        kind, sub = bambu.paths[name]
        new = OrderedDict(bambu.raw(name))
        # filament_id is not a print setting. Slyce (like OrcaSlicer) carries minted "OF" ids and
        # translates them to Bambu's "GF" catalog ids at the printer boundary through
        # resources/printers/bambu_filament_ids.json (docs/HLSD/filament_id.md), so Bambu's raw id
        # is never copied; the existing id is kept and new presets get one from
        # `scripts/orca_profile_tool.py generate-id`.
        bambu_fid = new.pop("filament_id", None)
        if name in slyce.paths and "filament_id" in slyce.raw(name):
            new["filament_id"] = slyce.raw(name)["filament_id"]
        if bambu_fid is not None:
            log.setdefault("bambu_filament_ids_dropped", []).append(name)
        if name in slyce.paths:
            old = slyce.raw(name)
            # Keys Bambu Studio has no option for are Slyce/OrcaSlicer features. Bambu Studio's file
            # cannot say anything about them, so the existing tuned value is kept.
            kept = [k for k in old if k not in new and k not in META_KEYS and k not in bambu_known]
            for k in kept:
                new[k] = old[k]
            if kept:
                log["kept_slyce_only_keys"][name] = kept
            _, old_sub = slyce.paths[name]
            if old_sub != sub:
                (slyce.root / "BBL" / old_sub).unlink(missing_ok=True)
        dest = slyce.root / "BBL" / sub
        dest.parent.mkdir(parents=True, exist_ok=True)
        if log["kept_slyce_only_keys"].get(name) or bambu_fid is not None or "filament_id" in new:
            dest.write_text(json.dumps(new, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
        else:  # byte-for-byte copy of Bambu Studio's file
            dest.write_bytes((bambu.root / "BBL" / sub).read_bytes())
        log["written"].append(name)
        list_key = {v: k for k, v in INDEX_LISTS.items()}[kind]
        entries = slyce.index.setdefault(list_key, [])
        for e in entries:
            if e["name"] == name:
                e["sub_path"] = sub
                break
        else:
            entries.append(OrderedDict(name=name, sub_path=sub))
            log["added_to_index"].append(name)
    _order_index_parents_first(slyce.index, bambu)
    (slyce.root / "BBL.json").write_text(json.dumps(slyce.index, indent=4, ensure_ascii=False) + "\n",
                                         encoding="utf-8")
    return log


def _order_index_parents_first(index: dict, bambu: Tree) -> None:
    """Keep the vendor index in Bambu Studio's order for names Bambu Studio lists, so every parent
    precedes its children; names only Slyce has stay where they were relative to each other."""
    for list_key in INDEX_LISTS:
        entries = index.get(list_key, [])
        order = {e["name"]: i for i, e in enumerate(bambu.index.get(list_key, []))}
        known = sorted((e for e in entries if e["name"] in order), key=lambda e: order[e["name"]])
        it = iter(known)
        index[list_key] = [next(it) if e["name"] in order else e for e in entries]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["diff", "sync"])
    ap.add_argument("--bambu", type=Path, required=True, help="Bambu Studio source checkout")
    ap.add_argument("--slyce", type=Path, required=True, help="Slyce source checkout")
    ap.add_argument("--model", action="append", required=True, help='e.g. "Bambu Lab P1S" (repeatable)')
    ap.add_argument("--json", type=Path, help="write the full diff/sync log as JSON here")
    args = ap.parse_args(argv)

    slyce_loader = Loader.from_source(args.slyce / "src/libslic3r/PrintConfig.cpp")
    bambu_known = option_keys(args.bambu / "src/libslic3r/PrintConfig.cpp")
    out = {}
    for model in args.model:
        bambu = Tree(args.bambu, slyce_loader)       # Bambu's files as Slyce will read them
        slyce = Tree(args.slyce, slyce_loader)
        if args.command == "diff":
            rep = diff_model(bambu, slyce, model)
            print(summarise(rep))
            out[model] = rep
        else:
            raw_bambu = Tree(args.bambu)
            raw_bambu.loader = None
            log = sync_model(raw_bambu, slyce, model, bambu_known)
            print(f"{model}: wrote {len(log['written'])} preset files, added {len(log['added_to_index'])} "
                  f"to BBL.json, kept Slyce-only keys in {len(log['kept_slyce_only_keys'])} files")
            out[model] = log
    if args.json:
        args.json.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

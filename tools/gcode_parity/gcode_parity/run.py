# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
"""Run reference (Bambu Studio) and candidate (Slyce) slicers on the same cases and diff the G-code.

Usage:
  python -m gcode_parity.run --reference "C:/Program Files/Bambu Studio/bambu-studio.exe" \
                             --candidate build/Slyce/orca-slicer.exe --out parity-report
  python -m gcode_parity.run --compare ref.gcode cand.gcode       # just diff two files
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from .compare import compare, results_to_dict, DIFFERS, IDENTICAL
from .models import GENERATORS, generate
from .parse import parse_gcode
from .presets import PresetIndex, flatten_to

HERE = Path(__file__).resolve().parent.parent
CASES_DIR = HERE / "cases"


def extract_gcode(path: Path, plate: int = 1) -> str:
    """Return G-code text from a .gcode file or a .gcode.3mf archive."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            name = f"Metadata/plate_{plate}.gcode"
            if name not in z.namelist():
                candidates = [n for n in z.namelist() if n.endswith(".gcode")]
                if not candidates:
                    raise FileNotFoundError(f"no .gcode inside {path}")
                name = sorted(candidates)[0]
            return z.read(name).decode("utf-8", errors="replace")
    return path.read_text(encoding="utf-8", errors="replace")


def slice_with(exe: Path, model: Path, settings: list[Path], filaments: list[Path],
               out_3mf: Path, extra: list[str], timeout: int) -> subprocess.CompletedProcess:
    cmd = [str(exe), str(model)]
    if settings:
        cmd += ["--load-settings", ";".join(str(p) for p in settings)]
    if filaments:
        cmd += ["--load-filaments", ";".join(str(p) for p in filaments)]
    cmd += ["--arrange", "1", "--slice", "0", "--export-3mf", str(out_3mf), *extra]
    out_3mf.parent.mkdir(parents=True, exist_ok=True)
    # Run inside the case folder: both CLIs drop a result.json into their working directory.
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=out_3mf.parent)


def _resolve(case_value: str, base: Path | None) -> Path:
    p = Path(case_value)
    return p if p.is_absolute() or base is None else base / p


_INDEXES: dict[Path, PresetIndex] = {}


def _vendor_dir(preset: Path) -> Path:
    """The vendor folder a preset belongs to: the child of `profiles` on its path (e.g. profiles/BBL)."""
    for parent in preset.resolve().parents:
        if parent.parent.name == "profiles":
            return parent
    return preset.resolve().parents[1]


def _index(vendor_dir: Path) -> PresetIndex:
    """One preset index per vendor folder; scanning a folder is the slow part of flattening."""
    vendor_dir = vendor_dir.resolve()
    if vendor_dir not in _INDEXES:
        _INDEXES[vendor_dir] = PresetIndex(vendor_dir)
    return _INDEXES[vendor_dir]


def render_markdown(name: str, results) -> str:
    lines = [f"## {name}", "", "| Category | Status | Summary |", "| --- | --- | --- |"]
    for r in results:
        lines.append(f"| {r.name} | {r.status} | {r.summary} |")
    for r in results:
        if r.details:
            lines += ["", f"<details><summary>{r.name}</summary>", "", "```", *r.details, "```",
                      "", "</details>"]
    return "\n".join(lines) + "\n"


def compare_files(ref: Path, cand: Path) -> list:
    return compare(parse_gcode(extract_gcode(ref)), parse_gcode(extract_gcode(cand)))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--compare", nargs=2, metavar=("REFERENCE", "CANDIDATE"),
                    help="compare two existing .gcode / .gcode.3mf files and exit")
    ap.add_argument("--reference", type=Path, help="reference slicer executable (Bambu Studio)")
    ap.add_argument("--candidate", type=Path, help="candidate slicer executable (Slyce)")
    ap.add_argument("--reference-profiles", type=Path,
                    help="reference slicer's resources/profiles directory (for relative preset paths)")
    ap.add_argument("--candidate-profiles", type=Path,
                    help="candidate slicer's resources/profiles directory")
    ap.add_argument("--cases", type=Path, default=CASES_DIR)
    ap.add_argument("--out", type=Path, default=Path("parity-report"))
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--no-flatten", action="store_true",
                    help="pass preset files as they are instead of flattening inherits/include first")
    args = ap.parse_args(argv)

    if args.compare:
        results = compare_files(Path(args.compare[0]), Path(args.compare[1]))
        sys.stdout.write(render_markdown("comparison", results))
        return 1 if any(r.status == DIFFERS for r in results) else 0

    if not (args.reference and args.candidate):
        ap.error("--reference and --candidate are required unless --compare is used")

    args.out.mkdir(parents=True, exist_ok=True)
    report_md = ["# G-code parity report", "",
                 f"Reference: `{args.reference}`  ", f"Candidate: `{args.candidate}`", ""]
    report_json = []
    worst = IDENTICAL
    for case_file in sorted(args.cases.glob("*.json")):
        case = json.loads(case_file.read_text(encoding="utf-8"))
        name = case["name"]
        work = args.out / name
        model = (generate(case["model"], work) if case["model"] in GENERATORS
                 else _resolve(case["model"], case_file.parent))
        runs = {}
        for role, exe, prof in (("reference", args.reference, args.reference_profiles),
                                ("candidate", args.candidate, args.candidate_profiles)):
            settings = [_resolve(p, prof) for p in case.get("settings", [])]
            filaments = [_resolve(p, prof) for p in case.get("filaments", [])]
            if not args.no_flatten:
                # A preset passed by path loses everything it inherits; hand the CLI a flattened copy.
                flat_dir = work / f"{role}_presets"
                settings = [flatten_to(p, _vendor_dir(p), flat_dir, _index(_vendor_dir(p))) for p in settings]
                filaments = [flatten_to(p, _vendor_dir(p), flat_dir, _index(_vendor_dir(p))) for p in filaments]
            out_3mf = work / f"{role}.gcode.3mf"
            proc = slice_with(exe, model, settings, filaments, out_3mf,
                              case.get("extra_args", []), args.timeout)
            (work / f"{role}.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
            runs[role] = (proc.returncode, out_3mf)
        failed = [r for r, (code, out) in runs.items() if code != 0 or not out.exists()]
        if failed:
            report_md.append(f"## {name}\n\nSlicing failed for: {', '.join(failed)} "
                             f"(see `{work}/*.log`).\n")
            report_json.append({"case": name, "error": f"slicing failed: {failed}"})
            worst = DIFFERS
            continue
        results = compare_files(runs["reference"][1], runs["candidate"][1])
        report_md.append(render_markdown(name, results))
        report_json.append({"case": name, "results": results_to_dict(results)})
        if any(r.status == DIFFERS for r in results):
            worst = DIFFERS
    (args.out / "report.md").write_text("\n".join(report_md), encoding="utf-8")
    (args.out / "report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")
    print(f"wrote {args.out / 'report.md'}")
    return 1 if worst == DIFFERS else 0


if __name__ == "__main__":
    raise SystemExit(main())

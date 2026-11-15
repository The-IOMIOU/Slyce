# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
"""Compare two parsed G-code files category by category."""
from __future__ import annotations

import difflib
import math
from dataclasses import dataclass, field, asdict

from .parse import ParsedGCode

IDENTICAL = "identical"
WITHIN = "within tolerance"
DIFFERS = "differs"


@dataclass
class Tolerances:
    position_mm: float = 1e-3      # max XYZ delta between matching extrusion endpoints
    extrusion_rel: float = 1e-3    # relative difference in E per layer / total
    length_rel: float = 1e-3       # relative difference in path length per layer


@dataclass
class CategoryResult:
    name: str
    status: str
    summary: str
    details: list[str] = field(default_factory=list)


def _rel(a: float, b: float) -> float:
    if a == b:
        return 0.0
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def _status(value: float, tol: float) -> str:
    if value == 0.0:
        return IDENTICAL
    return WITHIN if value <= tol else DIFFERS


def _sequence(name: str, ref: list[str], cand: list[str], max_details: int) -> CategoryResult:
    if ref == cand:
        return CategoryResult(name, IDENTICAL, f"{len(ref)} commands, identical")
    diff = list(difflib.unified_diff(ref, cand, "reference", "candidate", lineterm="", n=1))
    return CategoryResult(
        name, DIFFERS,
        f"reference {len(ref)} vs candidate {len(cand)} commands",
        diff[:max_details],
    )


def compare(ref: ParsedGCode, cand: ParsedGCode, tol: Tolerances | None = None,
            max_details: int = 20) -> list[CategoryResult]:
    tol = tol or Tolerances()
    results: list[CategoryResult] = []

    # Layer count
    nr, nc = len(ref.layers), len(cand.layers)
    results.append(CategoryResult(
        "layers", IDENTICAL if nr == nc else DIFFERS, f"reference {nr} vs candidate {nc} layers"))

    # Per-layer moves, extrusion and positions (aligned by index)
    worst_e = worst_len = worst_pos = 0.0
    layer_details: list[str] = []
    pos_compared = pos_skipped = 0
    for lr, lc in zip(ref.layers, cand.layers):
        de = _rel(lr.extrusion, lc.extrusion)
        dl = _rel(lr.path_length, lc.path_length)
        worst_e, worst_len = max(worst_e, de), max(worst_len, dl)
        if de > tol.extrusion_rel or dl > tol.length_rel:
            layer_details.append(
                f"layer {lr.index} (z={lr.z}): E {lr.extrusion:.5f} vs {lc.extrusion:.5f} "
                f"({de:.2%}), path {lr.path_length:.3f} vs {lc.path_length:.3f} mm ({dl:.2%})")
        if len(lr.extrusion_endpoints) == len(lc.extrusion_endpoints):
            pos_compared += 1
            for pr, pc in zip(lr.extrusion_endpoints, lc.extrusion_endpoints):
                worst_pos = max(worst_pos, math.dist(pr, pc))
        else:
            pos_skipped += 1
    results.append(CategoryResult(
        "extrusion per layer", _status(worst_e, tol.extrusion_rel),
        f"worst layer relative difference {worst_e:.4%}", layer_details[:max_details]))
    results.append(CategoryResult(
        "path length per layer", _status(worst_len, tol.length_rel),
        f"worst layer relative difference {worst_len:.4%}"))
    pos_status = _status(worst_pos, tol.position_mm)
    if pos_skipped and pos_status == IDENTICAL:
        pos_status = DIFFERS
    results.append(CategoryResult(
        "extrusion move positions", pos_status,
        f"max endpoint delta {worst_pos:.4f} mm over {pos_compared} layers with equal move counts; "
        f"{pos_skipped} layers skipped because move counts differ"))

    # Feature mix (whole print)
    def by_feature(p: ParsedGCode) -> dict[str, float]:
        acc: dict[str, float] = {}
        for layer in p.layers:
            for k, v in layer.extrusion_by_feature.items():
                acc[k] = acc.get(k, 0.0) + v
        return acc
    fr, fc = by_feature(ref), by_feature(cand)
    worst_f = 0.0
    feat_details = []
    for key in sorted(set(fr) | set(fc)):
        d = _rel(fr.get(key, 0.0), fc.get(key, 0.0))
        worst_f = max(worst_f, d)
        if d > tol.extrusion_rel:
            feat_details.append(f"{key}: {fr.get(key, 0.0):.3f} vs {fc.get(key, 0.0):.3f} mm ({d:.2%})")
    results.append(CategoryResult(
        "extrusion by feature", _status(worst_f, tol.extrusion_rel),
        f"worst feature relative difference {worst_f:.4%}", feat_details[:max_details]))

    dt = _rel(ref.total_extrusion, cand.total_extrusion)
    results.append(CategoryResult(
        "total extrusion", _status(dt, tol.extrusion_rel),
        f"{ref.total_extrusion:.3f} vs {cand.total_extrusion:.3f} mm ({dt:.4%})"))

    results.append(_sequence("temperatures", ref.temperatures, cand.temperatures, max_details))
    results.append(_sequence("fans", ref.fans, cand.fans, max_details))
    results.append(_sequence("tool changes / AMS", ref.tool_changes, cand.tool_changes, max_details))
    results.append(_sequence("start sequence", ref.start_sequence, cand.start_sequence, max_details))
    results.append(_sequence("end sequence", ref.end_sequence, cand.end_sequence, max_details))
    return results


def results_to_dict(results: list[CategoryResult]) -> list[dict]:
    return [asdict(r) for r in results]

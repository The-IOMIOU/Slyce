# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
"""Parse slicer G-code into a normalised, comparable structure.

Handles the conventions of the libslic3r family (PrusaSlicer, Bambu Studio, OrcaSlicer):
  * layer markers  `; CHANGE_LAYER` + `; Z_HEIGHT: z`   (Bambu Studio / OrcaSlicer on BBL printers)
                   `;LAYER_CHANGE`  + `;Z:z`            (PrusaSlicer / OrcaSlicer generic)
  * feature tags   `; FEATURE: Outer wall`              (Bambu Studio / OrcaSlicer)
                   `;TYPE:External perimeter`           (PrusaSlicer / OrcaSlicer generic)
  * absolute or relative extrusion (M82 / M83), G92 resets, G90 / G91.
Comments are only read for those markers; everything else in a comment is ignored.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

_WORD = re.compile(r"([A-Za-z])\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")

LAYER_MARKERS = ("; CHANGE_LAYER", ";LAYER_CHANGE")
FEATURE_PREFIXES = ("; FEATURE:", ";TYPE:")
TEMP_CODES = {"M104", "M109", "M140", "M190"}
FAN_CODES = {"M106", "M107"}
TOOL_CODES = {"M620", "M621"}


@dataclass
class Layer:
    index: int
    z: float | None = None
    moves: int = 0                 # G0/G1/G2/G3 commands
    extrusion_moves: int = 0       # moves with positive E delta
    path_length: float = 0.0       # XY+Z length of extruding moves (mm)
    travel_length: float = 0.0     # length of non-extruding moves (mm)
    extrusion: float = 0.0         # total positive E (mm of filament)
    retraction: float = 0.0        # total negative E (mm of filament, positive number)
    extrusion_by_feature: dict[str, float] = field(default_factory=dict)
    extrusion_endpoints: list[tuple[float, float, float]] = field(default_factory=list)


@dataclass
class ParsedGCode:
    layers: list[Layer]
    start_sequence: list[str]       # normalised commands before the first layer marker
    end_sequence: list[str]         # normalised commands after the last extruding move
    temperatures: list[str]         # e.g. "M104 S220 T0"
    fans: list[str]                 # e.g. "M106 P1 S255"
    tool_changes: list[str]         # T<n>, M620 ..., M621 ...
    total_extrusion: float
    header: dict[str, str]          # key: value pairs from the header block


def normalise_command(line: str) -> str:
    """Strip comment and whitespace, upper-case the code, sort nothing (order matters)."""
    code = line.split(";", 1)[0].strip()
    if not code:
        return ""
    parts = code.split()
    parts[0] = parts[0].upper()
    return " ".join(parts)


def _words(cmd: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for letter, value in _WORD.findall(cmd.split(None, 1)[1] if " " in cmd else ""):
        out[letter.upper()] = float(value)
    return out


def _arc_length(x0, y0, x1, y1, i, j, clockwise) -> float:
    cx, cy = x0 + i, y0 + j
    r = math.hypot(i, j)
    a0 = math.atan2(y0 - cy, x0 - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    sweep = a0 - a1 if clockwise else a1 - a0
    while sweep <= 0:
        sweep += 2 * math.pi
    if abs(x0 - x1) < 1e-9 and abs(y0 - y1) < 1e-9:
        sweep = 2 * math.pi
    return r * sweep


def _parse_header(lines: list[str]) -> dict[str, str]:
    header: dict[str, str] = {}
    in_block = False
    for raw in lines[:400]:
        s = raw.strip()
        if s.startswith("; HEADER_BLOCK_START"):
            in_block = True
            continue
        if s.startswith("; HEADER_BLOCK_END"):
            break
        if in_block and s.startswith(";") and ":" in s:
            key, value = s[1:].split(":", 1)
            header[key.strip().lower()] = value.strip()
    return header


def parse_gcode(text: str) -> ParsedGCode:
    lines = text.splitlines()
    layers: list[Layer] = []
    start_seq: list[str] = []
    temps: list[str] = []
    fans: list[str] = []
    tools: list[str] = []
    after_last_extrusion: list[str] = []

    x = y = z = e = 0.0
    abs_xyz = True
    abs_e = True
    feature = "unknown"
    cur: Layer | None = None
    total_e = 0.0

    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if s.startswith(";"):
            if s.startswith(LAYER_MARKERS):
                cur = Layer(index=len(layers))
                layers.append(cur)
                continue
            if cur is not None and cur.z is None:
                if s.startswith("; Z_HEIGHT:"):
                    cur.z = float(s.split(":", 1)[1])
                elif s.startswith(";Z:"):
                    cur.z = float(s.split(":", 1)[1])
            for prefix in FEATURE_PREFIXES:
                if s.startswith(prefix):
                    feature = s[len(prefix):].strip()
            continue

        cmd = normalise_command(s)
        if not cmd:
            continue
        code = cmd.split()[0]

        if cur is None:
            start_seq.append(cmd)
        else:
            after_last_extrusion.append(cmd)

        if code == "G90":
            abs_xyz = True
        elif code == "G91":
            abs_xyz = False
        elif code == "M82":
            abs_e = True
        elif code == "M83":
            abs_e = False
        elif code == "G92":
            w = _words(cmd)
            x, y, z, e = w.get("X", x), w.get("Y", y), w.get("Z", z), w.get("E", e)
        elif code in ("G0", "G1", "G2", "G3"):
            w = _words(cmd)
            if abs_xyz:
                nx, ny, nz = w.get("X", x), w.get("Y", y), w.get("Z", z)
            else:
                nx, ny, nz = x + w.get("X", 0.0), y + w.get("Y", 0.0), z + w.get("Z", 0.0)
            de = 0.0
            if "E" in w:
                de = (w["E"] - e) if abs_e else w["E"]
                e = w["E"] if abs_e else e + w["E"]
            if code in ("G2", "G3") and ("I" in w or "J" in w):
                xy = _arc_length(x, y, nx, ny, w.get("I", 0.0), w.get("J", 0.0), code == "G2")
                length = math.hypot(xy, nz - z)
            else:
                length = math.dist((x, y, z), (nx, ny, nz))
            if cur is not None:
                cur.moves += 1
                if de > 1e-9:
                    cur.extrusion_moves += 1
                    cur.extrusion += de
                    cur.path_length += length
                    cur.extrusion_by_feature[feature] = cur.extrusion_by_feature.get(feature, 0.0) + de
                    cur.extrusion_endpoints.append((round(nx, 4), round(ny, 4), round(nz, 4)))
                    after_last_extrusion = []
                else:
                    if de < -1e-9:
                        cur.retraction += -de
                    cur.travel_length += length
            if de > 0:
                total_e += de
            x, y, z = nx, ny, nz
        elif code in TEMP_CODES:
            temps.append(cmd)
        elif code in FAN_CODES:
            fans.append(cmd)
        elif code in TOOL_CODES or re.fullmatch(r"T\d+", code):
            tools.append(cmd)

    return ParsedGCode(
        layers=layers,
        start_sequence=start_seq,
        end_sequence=after_last_extrusion,
        temperatures=temps,
        fans=fans,
        tool_changes=tools,
        total_extrusion=total_e,
        header=_parse_header(lines),
    )

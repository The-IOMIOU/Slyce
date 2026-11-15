# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
"""Generate simple reference models as binary STL, so the harness needs no third-party models."""
from __future__ import annotations

import math
import struct
from pathlib import Path

Tri = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def _normal(t: Tri) -> tuple[float, float, float]:
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / n, ny / n, nz / n


def write_stl(path: Path, tris: list[Tri]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"slyce gcode_parity reference model".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<3f", *_normal(t)))
            for v in t:
                f.write(struct.pack("<3f", *v))
            f.write(b"\0\0")
    return path


def _quad(a, b, c, d) -> list[Tri]:
    return [(a, b, c), (a, c, d)]


def box(sx: float, sy: float, sz: float) -> list[Tri]:
    p = [(x, y, z) for z in (0, sz) for y in (0, sy) for x in (0, sx)]
    # p index: x + 2*y + 4*z
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    out: list[Tri] = []
    for a, b, c, d in faces:
        out += _quad(p[a], p[b], p[c], p[d])
    return out


def cylinder(r: float, h: float, segments: int = 64) -> list[Tri]:
    out: list[Tri] = []
    ring = [(r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments))
            for i in range(segments)]
    for i in range(segments):
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % segments]
        out.append(((0, 0, 0), (x1, y1, 0), (x0, y0, 0)))
        out.append(((0, 0, h), (x0, y0, h), (x1, y1, h)))
        out += _quad((x0, y0, 0), (x1, y1, 0), (x1, y1, h), (x0, y0, h))
    return out


def overhang_ramp(width: float = 20.0, length: float = 30.0, height: float = 15.0) -> list[Tri]:
    """A wedge whose sloped underside overhangs at atan(height/length)."""
    a, b = (0, 0, 0), (0, width, 0)
    c, d = (0, 0, height), (0, width, height)
    e, f = (length, 0, height), (length, width, height)
    out: list[Tri] = []
    out += _quad(a, e, f, b)          # sloped underside
    out += _quad(c, d, f, e)          # top
    out += _quad(a, b, d, c)          # back wall
    out.append((a, c, e))             # side
    out.append((b, f, d))             # side
    return [(t[0], t[2], t[1]) for t in out]   # wound so normals point outwards


def square_tube(size: float = 20.0, wall: float = 4.0, height: float = 10.0) -> list[Tri]:
    """A square tube: one contour and one hole, to compare loop direction and seams."""
    o, i = size, size - wall
    w = wall
    out: list[Tri] = []
    outer = [(0, 0), (o, 0), (o, o), (0, o)]
    inner = [(w, w), (i, w), (i, i), (w, i)]
    for k in range(4):
        (ax, ay), (bx, by) = outer[k], outer[(k + 1) % 4]
        out += _quad((ax, ay, 0), (bx, by, 0), (bx, by, height), (ax, ay, height))       # outside, facing out
        (cx, cy), (dx, dy) = inner[k], inner[(k + 1) % 4]
        out += _quad((dx, dy, 0), (cx, cy, 0), (cx, cy, height), (dx, dy, height))       # inside, facing in
        out += _quad((ax, ay, height), (bx, by, height), (dx, dy, height), (cx, cy, height))  # top ring
        out += _quad((ax, ay, 0), (cx, cy, 0), (dx, dy, 0), (bx, by, 0))                 # bottom ring
    return out


GENERATORS = {
    "square_tube": square_tube,
    "cube_20mm": lambda: box(20, 20, 20),
    "cylinder_r10_h20": lambda: cylinder(10, 20),
    "overhang_ramp": overhang_ramp,
}


def generate(name: str, out_dir: Path) -> Path:
    return write_stl(out_dir / f"{name}.stl", GENERATORS[name]())

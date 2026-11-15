# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
import json
import math
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gcode_parity.parse import parse_gcode  # noqa: E402
from gcode_parity.compare import compare, IDENTICAL, DIFFERS, WITHIN  # noqa: E402
from gcode_parity.models import GENERATORS, write_stl  # noqa: E402
from gcode_parity.run import extract_gcode, main  # noqa: E402
from gcode_parity.presets import flatten  # noqa: E402

BAMBU_STYLE = """\
; HEADER_BLOCK_START
; total layer number: 2
; HEADER_BLOCK_END
M140 S55
M104 S220
G90
M83
G28
M109 S220
; CHANGE_LAYER
; Z_HEIGHT: 0.2
; FEATURE: Outer wall
G1 Z0.2 F600
G1 X10 Y0 E1.0
G1 X10 Y10 E1.0
; FEATURE: Sparse infill
G1 X0 Y10 E0.5
G1 E-0.8
G0 X0 Y0
G1 E0.8
; CHANGE_LAYER
; Z_HEIGHT: 0.4
M106 S255
G1 Z0.4
G1 X10 Y0 E1.0
M104 S0
M140 S0
M107
"""

PRUSA_STYLE_ABS_E = """\
M82
G92 E0
;LAYER_CHANGE
;Z:0.2
;TYPE:External perimeter
G1 X10 Y0 E1.0
G1 X10 Y10 E2.0
G92 E0
G1 X0 Y10 E0.5
;LAYER_CHANGE
;Z:0.4
G1 X0 Y0 E1.5
"""


class ParseTests(unittest.TestCase):
    def test_bambu_markers_layers_and_features(self):
        p = parse_gcode(BAMBU_STYLE)
        self.assertEqual(len(p.layers), 2)
        self.assertEqual(p.layers[0].z, 0.2)
        self.assertEqual(p.layers[1].z, 0.4)
        self.assertAlmostEqual(p.layers[0].extrusion, 2.5 + 0.8)  # 2.5 + un-retract
        self.assertAlmostEqual(p.layers[0].retraction, 0.8)
        self.assertAlmostEqual(p.layers[0].extrusion_by_feature["Outer wall"], 2.0)
        self.assertEqual(p.header["total layer number"], "2")
        self.assertEqual(p.temperatures[:2], ["M140 S55", "M104 S220"])
        self.assertEqual(p.end_sequence, ["M104 S0", "M140 S0", "M107"])
        self.assertIn("G28", p.start_sequence)

    def test_absolute_e_with_g92_reset(self):
        p = parse_gcode(PRUSA_STYLE_ABS_E)
        self.assertEqual(len(p.layers), 2)
        self.assertAlmostEqual(p.layers[0].extrusion, 2.0 + 0.5)
        self.assertAlmostEqual(p.layers[1].extrusion, 1.0)
        self.assertAlmostEqual(p.layers[0].path_length, 10 + 10 + 10)
        self.assertIn("External perimeter", p.layers[0].extrusion_by_feature)

    def test_arc_length(self):
        # Full circle of radius 5 starting at (5,0), centre (0,0): I=-5 J=0
        p = parse_gcode(";LAYER_CHANGE\n;Z:0.2\nG1 X5 Y0\nM83\nG2 X5 Y0 I-5 J0 E1\n")
        self.assertAlmostEqual(p.layers[0].path_length, 2 * math.pi * 5, places=6)
        # Quarter arc counter-clockwise from (5,0) to (0,5)
        p = parse_gcode(";LAYER_CHANGE\n;Z:0.2\nG1 X5 Y0\nM83\nG3 X0 Y5 I-5 J0 E1\n")
        self.assertAlmostEqual(p.layers[0].path_length, math.pi * 5 / 2, places=6)


class CompareTests(unittest.TestCase):
    def test_identical_files(self):
        a = parse_gcode(BAMBU_STYLE)
        results = compare(a, parse_gcode(BAMBU_STYLE))
        self.assertTrue(all(r.status == IDENTICAL for r in results), [(r.name, r.status) for r in results])

    def test_comments_and_case_ignored(self):
        noisy = BAMBU_STYLE.replace("G1 X10 Y0 E1.0", "g1 X10 Y0 E1.0 ; a comment")
        results = {r.name: r for r in compare(parse_gcode(BAMBU_STYLE), parse_gcode(noisy))}
        self.assertEqual(results["extrusion per layer"].status, IDENTICAL)
        self.assertEqual(results["extrusion move positions"].status, IDENTICAL)

    def test_temperature_change_detected(self):
        other = BAMBU_STYLE.replace("M109 S220", "M109 S225")
        results = {r.name: r for r in compare(parse_gcode(BAMBU_STYLE), parse_gcode(other))}
        self.assertEqual(results["temperatures"].status, DIFFERS)
        self.assertEqual(results["extrusion per layer"].status, IDENTICAL)

    def test_small_extrusion_change_within_tolerance(self):
        other = BAMBU_STYLE.replace("G1 X10 Y10 E1.0", "G1 X10 Y10 E1.0001")
        results = {r.name: r for r in compare(parse_gcode(BAMBU_STYLE), parse_gcode(other))}
        self.assertEqual(results["extrusion per layer"].status, WITHIN)

    def test_position_change_detected(self):
        other = BAMBU_STYLE.replace("G1 X10 Y10 E1.0", "G1 X10.5 Y10 E1.0")
        results = {r.name: r for r in compare(parse_gcode(BAMBU_STYLE), parse_gcode(other))}
        self.assertEqual(results["extrusion move positions"].status, DIFFERS)

    def test_layer_count_change_detected(self):
        other = BAMBU_STYLE + "; CHANGE_LAYER\n; Z_HEIGHT: 0.6\nG1 X0 Y0 E1\n"
        results = {r.name: r for r in compare(parse_gcode(BAMBU_STYLE), parse_gcode(other))}
        self.assertEqual(results["layers"].status, DIFFERS)


class IoTests(unittest.TestCase):
    def test_extract_from_gcode_3mf(self):
        with tempfile.TemporaryDirectory() as d:
            arch = Path(d) / "x.gcode.3mf"
            with zipfile.ZipFile(arch, "w") as z:
                z.writestr("Metadata/plate_1.gcode", BAMBU_STYLE)
            self.assertEqual(extract_gcode(arch), BAMBU_STYLE)

    def test_compare_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.gcode", Path(d) / "b.gcode"
            a.write_text(BAMBU_STYLE)
            b.write_text(BAMBU_STYLE)
            self.assertEqual(main(["--compare", str(a), str(b)]), 0)
            b.write_text(BAMBU_STYLE.replace("M109 S220", "M109 S230"))
            self.assertEqual(main(["--compare", str(a), str(b)]), 1)

    def test_generated_models_are_valid_binary_stl(self):
        with tempfile.TemporaryDirectory() as d:
            for name, gen in GENERATORS.items():
                tris = gen()
                path = write_stl(Path(d) / f"{name}.stl", tris)
                data = path.read_bytes()
                (count,) = struct.unpack_from("<I", data, 80)
                self.assertEqual(count, len(tris))
                self.assertEqual(len(data), 84 + 50 * count)


class ModelGeometryTests(unittest.TestCase):
    def test_models_are_closed_and_outward_facing(self):
        import collections
        for name, gen in GENERATORS.items():
            with self.subTest(name=name):
                tris = gen()
                edges = collections.Counter()
                for t in tris:
                    for k in range(3):
                        edges[(t[k], t[(k + 1) % 3])] += 1
                # Every directed edge appears once and its reverse once: closed and consistently wound.
                for (a, b), n in edges.items():
                    self.assertEqual(n, 1)
                    self.assertEqual(edges.get((b, a), 0), 1)
                volume = sum((a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                              + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6 for a, b, c in tris)
                self.assertGreater(volume, 0)


class FlattenTests(unittest.TestCase):
    def test_flatten_follows_inherits_and_include_in_loader_order(self):
        with tempfile.TemporaryDirectory() as d:
            vendor = Path(d) / "profiles" / "V"
            (vendor / "machine").mkdir(parents=True)
            def put(name, data):
                (vendor / "machine" / f"{name}.json").write_text(json.dumps(data))
            put("common", {"type": "machine", "name": "common", "instantiation": "false", "setting_id": "X",
                           "nozzle_diameter": ["0.4"], "machine_start_gcode": "old", "retraction_length": ["1"]})
            put("tmpl", {"type": "machine", "name": "tmpl", "machine_start_gcode": "G28 ; from template"})
            put("leaf", {"type": "machine", "name": "leaf", "inherits": "common", "include": ["tmpl"],
                         "from": "system", "setting_id": "GM1", "instantiation": "true", "retraction_length": ["0.8"]})
            flat = flatten(vendor / "machine" / "leaf.json", vendor)
            self.assertEqual(flat["nozzle_diameter"], ["0.4"])                     # inherited
            self.assertEqual(flat["machine_start_gcode"], "G28 ; from template")   # include over parent
            self.assertEqual(flat["retraction_length"], ["0.8"])                   # own over both
            self.assertEqual(flat["setting_id"], "GM1")                             # leaf bookkeeping only
            self.assertEqual(flat["from"], "system")
            self.assertNotIn("inherits", flat)
            self.assertNotIn("include", flat)


if __name__ == "__main__":
    unittest.main()

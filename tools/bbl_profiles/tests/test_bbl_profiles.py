# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bbl_profiles import Loader, Tree, _padded_equal, diff_preset, option_keys, presets_for_model  # noqa: E402

PRINT_CONFIG = r'''
const std::vector<std::string> filament_extruder_override_keys = {
    "filament_retraction_length", // comment "not_a_key"
};
void PrintConfigDef::init() {
    def = this->add("layer_height", coFloat);
    def = this->add_nullable("nozzle_temperature", coInts);
    def = this->add("compatible_printers", coStrings);
    def = this->add("printer_model", coString);
    def = this->add("overhang_fan_speed", coInts);
    for (const AxisDefault &axis : axes) {
        def = this->add("machine_max_speed_" + axis.name, coFloats);
    }
}
void PrintConfigDef::handle_legacy(t_config_option_key &opt_key, std::string &value)
{
    if (opt_key == "bridge_fan_speed") {
        opt_key = "overhang_fan_speed";
    }
    static std::set<std::string> ignore = { "silent_mode" };
}
void PrintConfigDef::handle_legacy_composite(DynamicPrintConfig &config) {}
'''


def make_tree(root: Path, presets: dict[str, dict]) -> Path:
    bbl = root / "resources" / "profiles" / "BBL"
    index = {"machine_model_list": [], "machine_list": [], "process_list": [], "filament_list": []}
    for name, data in presets.items():
        kind = data["type"]
        sub = f"{kind}/{name}.json"
        (bbl / kind).mkdir(parents=True, exist_ok=True)
        (bbl / sub).write_text(json.dumps(data), encoding="utf-8")
        index[f"{kind}_list"].append({"name": name, "sub_path": sub})
    (root / "resources" / "profiles" / "BBL.json").write_text(json.dumps(index), encoding="utf-8")
    return root


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cpp = Path(self.tmp.name) / "PrintConfig.cpp"
        self.cpp.write_text(PRINT_CONFIG, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_option_keys_include_loop_and_override_keys(self):
        keys = option_keys(self.cpp)
        self.assertIn("layer_height", keys)
        self.assertIn("nozzle_temperature", keys)
        self.assertIn("machine_max_speed_x", keys)
        self.assertIn("machine_max_speed_e", keys)
        self.assertIn("filament_retraction_length", keys)
        self.assertNotIn("not_a_key", keys)

    def test_loader_renames_and_drops(self):
        loader = Loader.from_source(self.cpp)
        self.assertEqual(loader.map_key("bridge_fan_speed"), "overhang_fan_speed")
        self.assertIsNone(loader.map_key("silent_mode"))
        self.assertIsNone(loader.map_key("does_not_exist"))
        self.assertEqual(loader.map_key("layer_height"), "layer_height")


class ResolveTests(unittest.TestCase):
    def test_inherits_then_includes_then_own(self):
        with tempfile.TemporaryDirectory() as d:
            root = make_tree(Path(d), {
                "base": {"type": "process", "name": "base", "instantiation": "false", "layer_height": "0.2",
                         "nozzle_temperature": ["200"]},
                "tmpl": {"type": "process", "name": "tmpl", "instantiation": "false", "layer_height": "0.3",
                         "overhang_fan_speed": ["50"]},
                "leaf": {"type": "process", "name": "leaf", "instantiation": "true", "inherits": "base",
                         "include": ["tmpl"], "nozzle_temperature": ["210"]},
            })
            t = Tree(root)
            r = t.resolved("leaf")
            self.assertEqual(r["layer_height"], "0.3")          # include overrides parent
            self.assertEqual(r["nozzle_temperature"], ["210"])  # own overrides both
            self.assertEqual(r["overhang_fan_speed"], ["50"])
            self.assertEqual(t.closure(["leaf"]), {"leaf", "base", "tmpl"})

    def test_presets_for_model_and_diff(self):
        common = {"m": {"type": "machine", "name": "m", "instantiation": "true", "printer_model": "P"},
                  "f": {"type": "filament", "name": "f", "instantiation": "true", "compatible_printers": ["m"],
                        "nozzle_temperature": ["220"]}}
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ta = Tree(make_tree(Path(a), common))
            changed = json.loads(json.dumps(common))
            changed["f"]["nozzle_temperature"] = ["225"]
            tb = Tree(make_tree(Path(b), changed))
            self.assertEqual(presets_for_model(ta, "P")["filament"], ["f"])
            d = diff_preset(ta, tb, "f")
            self.assertEqual(d["changed"], {"nozzle_temperature": [["220"], ["225"]]})


class PaddingTests(unittest.TestCase):
    def test_padded_equal(self):
        self.assertTrue(_padded_equal(["10"], ["10", "10"]))
        self.assertTrue(_padded_equal(["1", "2"], ["1", "2", "2"]))
        self.assertFalse(_padded_equal(["1", "2"], ["1", "3"]))
        self.assertFalse(_padded_equal(["10"], ["10", "20"]))
        self.assertTrue(_padded_equal("a", "a"))


if __name__ == "__main__":
    unittest.main()

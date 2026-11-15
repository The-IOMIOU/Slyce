# Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0
"""G-code parity harness: slice the same cases in Bambu Studio and Slyce and diff the output."""
from .parse import parse_gcode, ParsedGCode, Layer
from .compare import compare, Tolerances, CategoryResult

__all__ = ["parse_gcode", "ParsedGCode", "Layer", "compare", "Tolerances", "CategoryResult"]

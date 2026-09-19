# GHOST FIVE // SPECTRAL CORE // VECTIS
# Regression coverage for the VECTIS formatter contract.
from __future__ import annotations

import unittest

from vectis.formatter import format_program
from vectis.parser import parse


class FormatterTests(unittest.TestCase):
    def test_format_program_is_deterministic(self):
        source = '''mission "Format" {
source ready true;
let label upper("vectis");
when ready { publish label; } otherwise { publish "no"; }
}
'''
        first = format_program(parse(source, file="<format-test>"))
        second = format_program(parse(first, file="<format-test>"))
        self.assertEqual(first, second)
        self.assertIn("    let label upper(\"vectis\");", first)
        self.assertIn("    when ready {", first)

    def test_format_expression_preserves_semantics(self):
        source = '''mission "Math" {
    source x 2 + 3 * 4;
    publish x;
}
'''
        formatted = format_program(parse(source))
        program = parse(formatted)
        self.assertEqual(type(program).__name__, "Program")
        self.assertIn("source x (2 + (3 * 4));", formatted)


if __name__ == "__main__":
    unittest.main()

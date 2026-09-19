from __future__ import annotations

import unittest

from vectis.evaluator import EvaluationError, builtin_manifest, evaluate_expression
from vectis.parser import parse_expression


class EvaluatorTests(unittest.TestCase):
    def evaluate(self, source: str, values=None):
        return evaluate_expression(
            parse_expression(source, file="<evaluator-test>"),
            values or {},
        )

    def test_arithmetic_and_comparison(self):
        self.assertEqual(self.evaluate("2 + 3 * 4"), 14)
        self.assertTrue(self.evaluate("14 >= 14"))
        self.assertTrue(self.evaluate("15 > 14"))
        self.assertTrue(self.evaluate("13 < 14"))
        self.assertEqual(self.evaluate("14 % 5"), 4)

    def test_boolean_logic(self):
        self.assertTrue(self.evaluate("true && !false"))
        self.assertFalse(self.evaluate("false || false"))

    def test_reference_environment(self):
        self.assertEqual(
            self.evaluate("x + y", {"x": 5, "y": 7}),
            12,
        )

    def test_string_builtins(self):
        self.assertEqual(
            self.evaluate('upper(trim("  vectis  "))'),
            "VECTIS",
        )
        self.assertTrue(
            self.evaluate('contains("Ghost Five", "Five")')
        )
        self.assertEqual(
            self.evaluate('concat("Ghost", " ", "Five")'),
            "Ghost Five",
        )

    def test_numeric_builtins(self):
        self.assertEqual(self.evaluate("max(4, 9, 2)"), 9)
        self.assertEqual(self.evaluate("min(4, 9, 2)"), 2)
        self.assertEqual(self.evaluate("abs(-12)"), 12)
        self.assertEqual(self.evaluate("round(3.14159, 2)"), 3.14)

    def test_conversion_builtins(self):
        self.assertEqual(self.evaluate('number("42")'), 42)
        self.assertEqual(self.evaluate("string(true)"), "true")
        self.assertTrue(self.evaluate('boolean("yes")'))

    def test_unknown_builtin_is_rejected(self):
        with self.assertRaises(EvaluationError):
            self.evaluate("does_not_exist(1)")

    def test_builtin_manifest_is_stable_and_nonempty(self):
        manifest = builtin_manifest()
        self.assertGreaterEqual(len(manifest), 10)
        self.assertEqual(
            [item["name"] for item in manifest],
            sorted(item["name"] for item in manifest),
        )


if __name__ == "__main__":
    unittest.main()

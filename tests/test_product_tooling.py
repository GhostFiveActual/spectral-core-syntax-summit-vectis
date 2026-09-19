# GHOST FIVE // SPECTRAL CORE // VECTIS
# Regression coverage for project tooling, graph exports, and expanded built in functions.

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vectis.compiler import compile_program
from vectis.evaluator import evaluate_expression
from vectis.parser import parse, parse_expression
from vectis.product import (
    graph_summary,
    graph_to_dot,
    graph_to_mermaid,
    initialize_project,
    test_project,
)
from vectis.runtime import Runtime


class ProductToolingTests(unittest.TestCase):
    """Protect the operational product surface added for the 0.1 line."""

    def evaluate(self, source: str):
        """Evaluate one deterministic expression for focused assertions."""
        return evaluate_expression(
            parse_expression(source, file="<product-test>"),
            {},
        )

    def test_expanded_builtins(self):
        self.assertEqual(
            self.evaluate('replace("GHOST FIVE", "FIVE", "CORE")'),
            "GHOST CORE",
        )
        self.assertEqual(
            self.evaluate('repeat("V", 3)'),
            "VVV",
        )
        self.assertEqual(
            self.evaluate("clamp(108, 0, 100)"),
            100,
        )
        self.assertTrue(
            self.evaluate("between(94, 80, 100)")
        )
        self.assertEqual(
            self.evaluate(
                'if_else(94 >= 80, "AUTHORIZED", "REVIEW")'
            ),
            "AUTHORIZED",
        )
        self.assertEqual(
            self.evaluate('capitalize("spectral core")'),
            "Spectral core",
        )
        self.assertEqual(
            self.evaluate('title("spectral core")'),
            "Spectral Core",
        )

    def test_project_scaffold_is_branded_and_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vectis-project"
            created = initialize_project(root)

            self.assertEqual(len(created), 3)
            self.assertIn(
                "GHOST FIVE // SPECTRAL CORE // VECTIS",
                (root / "README.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "GHOST FIVE // SPECTRAL CORE // VECTIS",
                (root / "vectis.toml").read_text(encoding="utf-8"),
            )

            result = test_project(root)
            self.assertEqual(result["files"], 1)
            self.assertEqual(result["failed"], 0)

    def test_graph_exports_are_deterministic(self):
        source = """mission "Graph" {
    source ready true;
    let label upper("vectis");
    when ready {
        publish label;
    }
}
"""
        compiled = compile_program(
            parse(source, file="<graph-test>")
        )
        self.assertTrue(compiled.ok)
        graph = compiled.graph
        self.assertIsNotNone(graph)

        summary = graph_summary(graph)
        self.assertEqual(summary["nodes"], 4)
        self.assertGreaterEqual(summary["edges"], 2)

        dot = graph_to_dot(graph)
        mermaid = graph_to_mermaid(graph)

        self.assertIn("digraph vectis", dot)
        self.assertIn("flowchart LR", mermaid)
        self.assertIn("condition:0001", dot)
        self.assertIn("condition:0001", mermaid)

    def test_project_scaffold_executes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_project(root)
            source = (root / "missions" / "main.vectis").read_text(
                encoding="utf-8"
            )
            compiled = compile_program(
                parse(source, file="main.vectis")
            )
            self.assertTrue(compiled.ok)
            result = Runtime(compiled.graph).execute()
            self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()

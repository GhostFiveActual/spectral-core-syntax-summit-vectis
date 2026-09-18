from __future__ import annotations

from pathlib import Path
import re
import unittest

from vectis.compiler import compile_program
from vectis.parser import parse


ROOT = Path(__file__).resolve().parents[1]
PLAYGROUND = ROOT / "docs" / "playground"

INDEX = PLAYGROUND / "index.html"
APP = PLAYGROUND / "app.js"
STYLES = PLAYGROUND / "styles.css"
DESIGN = PLAYGROUND / "design.md"


class TestPlaygroundContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.app = APP.read_text(encoding="utf-8")
        cls.styles = STYLES.read_text(encoding="utf-8")
        cls.design = DESIGN.read_text(encoding="utf-8")

    def test_required_files_exist_and_are_nonempty(self):
        for path in (INDEX, APP, STYLES, DESIGN):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)

    def test_index_declares_language(self):
        self.assertRegex(
            self.index,
            r'<html\s+lang=["\']en["\']',
        )

    def test_index_loads_external_assets(self):
        self.assertIn('href="styles.css"', self.index)
        self.assertIn('src="app.js"', self.index)

    def test_source_editor_has_label(self):
        self.assertIn('for="source"', self.index)
        self.assertIn('id="source"', self.index)

    def test_native_controls_exist(self):
        self.assertIn('id="load-example"', self.index)
        self.assertIn('id="run-button"', self.index)
        self.assertGreaterEqual(
            self.index.count('type="button"'),
            2,
        )

    def test_output_regions_exist(self):
        for output_id in (
            "ast",
            "executionGraph",
            "diagnostics",
        ):
            with self.subTest(output_id=output_id):
                self.assertIn(
                    f'id="{output_id}"',
                    self.index,
                )

    def test_live_status_region_exists(self):
        self.assertIn('id="status"', self.index)
        self.assertIn('role="status"', self.index)
        self.assertIn('aria-live="polite"', self.index)

    def test_output_regions_are_keyboard_focusable(self):
        self.assertGreaterEqual(
            self.index.count('tabindex="0"'),
            3,
        )

    def test_javascript_uses_local_run_api(self):
        self.assertIn('fetch("/api/run"', self.app)
        self.assertIn('method: "POST"', self.app)
        self.assertIn(
            '"Content-Type": "application/json"',
            self.app,
        )
        self.assertIn(
            "JSON.stringify({ source })",
            self.app,
        )

    def test_javascript_renders_compiler_outputs(self):
        for output in (
            '"ast"',
            '"executionGraph"',
            '"diagnostics"',
        ):
            with self.subTest(output=output):
                self.assertIn(output, self.app)

    def test_javascript_handles_http_failure(self):
        self.assertIn(
            "if (!response.ok)",
            self.app,
        )
        self.assertIn(
            'setStatus("Request failed.")',
            self.app,
        )

    def test_javascript_avoids_dynamic_execution(self):
        self.assertIsNone(
            re.search(r"\beval\s*\(", self.app)
        )
        self.assertNotIn("new Function", self.app)
        self.assertNotIn(".innerHTML", self.app)

    def test_embedded_example_compiles(self):
        match = re.search(
            r"const EXAMPLE_SOURCE = `(?P<source>.*?)`;",
            self.app,
            flags=re.DOTALL,
        )

        self.assertIsNotNone(match)

        source = match.group("source").strip()

        program = parse(
            source,
            file="<playground-example>",
        )

        result = compile_program(program)

        self.assertFalse(result.diagnostics)
        self.assertIsNotNone(result.graph)

    def test_css_has_visible_focus(self):
        self.assertIn(":focus-visible", self.styles)
        self.assertIn("outline:", self.styles)
        self.assertNotIn("outline: none", self.styles)

    def test_css_is_responsive(self):
        self.assertIn(
            "@media (max-width:",
            self.styles,
        )

    def test_css_supports_reduced_motion(self):
        self.assertIn(
            "prefers-reduced-motion",
            self.styles,
        )

    def test_design_contains_contract_terms(self):
        lowered = self.design.lower()

        for term in (
            "browser",
            "source",
            "diagnostic",
            "example",
            "accessibility",
        ):
            with self.subTest(term=term):
                self.assertIn(term, lowered)

    def test_design_documents_local_api(self):
        self.assertIn("POST /api/run", self.design)
        self.assertIn(
            "Content-Type: application/json",
            self.design,
        )

    def test_no_external_cdn_dependency(self):
        combined = (
            self.index
            + "\n"
            + self.app
            + "\n"
            + self.styles
        ).lower()

        for marker in (
            "cdn.",
            "unpkg.com",
            "jsdelivr.net",
        ):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, combined)


if __name__ == "__main__":
    unittest.main()

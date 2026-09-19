# GHOST FIVE // SPECTRAL CORE // VECTIS
# Regression coverage for the Mission Readiness application powered by VECTIS.

from __future__ import annotations

from importlib.resources import files
import unittest

from vectis.demo_app import (
    build_readiness_source,
    run_readiness,
)


class DemoApplicationTests(unittest.TestCase):
    """Verify that the demo is a real VECTIS backed application."""

    def test_assets_are_packaged(self):
        root = files("vectis").joinpath("demo_assets")
        for name in ("index.html", "styles.css", "app.js"):
            with self.subTest(name=name):
                self.assertTrue(root.joinpath(name).is_file())

    def test_authorized_mission_runs_through_vectis(self):
        result = run_readiness(
            mission="Public preview",
            operator="Ghost Five Actual",
            ready=True,
            quality=94,
            risk=22,
        )

        self.assertEqual(result["diagnostics"], [])
        self.assertIsNotNone(result["graph"])
        self.assertTrue(result["runtime"]["success"])

        values = dict(result["runtime"]["node_values"])
        self.assertTrue(values["approved"])
        self.assertEqual(values["status"], "AUTHORIZED")

    def test_review_path_runs_through_vectis(self):
        result = run_readiness(
            mission="Public preview",
            operator="Ghost Five Actual",
            ready=True,
            quality=71,
            risk=22,
        )

        self.assertTrue(result["runtime"]["success"])
        values = dict(result["runtime"]["node_values"])
        self.assertFalse(values["approved"])
        self.assertEqual(values["status"], "REVIEW")

    def test_scores_are_bounded(self):
        with self.assertRaises(ValueError):
            build_readiness_source(
                mission="Mission",
                operator="Operator",
                ready=True,
                quality=101,
                risk=20,
            )


if __name__ == "__main__":
    unittest.main()

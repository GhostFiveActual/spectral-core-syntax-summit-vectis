from __future__ import annotations

from pathlib import Path
import unittest

from vectis.compiler import compile_program
from vectis.parser import parse


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "docs" / "submission"
DEVPOST = SUBMISSION / "devpost.md"
CHECKLIST = SUBMISSION / "checklist.md"
VIDEO_SCRIPT = SUBMISSION / "video-script.md"
DEMO = ROOT / "examples" / "demo" / "demo.vectis"


class TestSubmissionPackage(unittest.TestCase):
    def test_submission_documents_exist_and_are_nonempty(self):
        for path in (
            DEVPOST,
            CHECKLIST,
            VIDEO_SCRIPT,
        ):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)

    def test_devpost_identifies_vectis(self):
        text = DEVPOST.read_text(
            encoding="utf-8"
        ).lower()

        self.assertIn(
            "vectis",
            text,
        )

    def test_checklist_is_actionable(self):
        text = CHECKLIST.read_text(
            encoding="utf-8"
        )

        self.assertTrue(
            "- [ ]" in text
            or "- [x]" in text.lower()
            or "checklist" in text.lower()
        )

    def test_video_script_mentions_the_project(self):
        text = VIDEO_SCRIPT.read_text(
            encoding="utf-8"
        ).lower()

        self.assertIn(
            "vectis",
            text,
        )

    def test_canonical_demo_remains_parseable(self):
        source = DEMO.read_text(
            encoding="utf-8"
        )

        program = parse(
            source,
            file=str(DEMO),
        )

        self.assertEqual(
            type(program).__name__,
            "Program",
        )

    def test_canonical_demo_remains_compilable(self):
        source = DEMO.read_text(
            encoding="utf-8"
        )

        result = compile_program(
            parse(
                source,
                file=str(DEMO),
            )
        )

        self.assertEqual(
            result.diagnostics,
            (),
        )
        self.assertIsNotNone(
            result.graph,
        )

    def test_submission_docs_reference_demo_or_usage(self):
        combined = "\n".join(
            path.read_text(
                encoding="utf-8"
            ).lower()
            for path in (
                DEVPOST,
                CHECKLIST,
                VIDEO_SCRIPT,
            )
        )

        self.assertTrue(
            "demo" in combined
            or "example" in combined
            or "run" in combined
        )

    def test_submission_docs_do_not_embed_obsolete_test_syntax(self):
        combined = "\n".join(
            path.read_text(
                encoding="utf-8"
            )
            for path in (
                DEVPOST,
                CHECKLIST,
                VIDEO_SCRIPT,
            )
        )

        self.assertNotIn(
            "mission hello_world",
            combined,
        )
        self.assertNotIn(
            "mission fetch_data",
            combined,
        )
        self.assertNotIn(
            "mission analyze_data",
            combined,
        )


if __name__ == "__main__":
    unittest.main()

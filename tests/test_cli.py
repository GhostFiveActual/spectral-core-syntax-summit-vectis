from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from vectis import __version__
from vectis.cli import build_parser, main


class CliTests(unittest.TestCase):
    def invoke(
        self,
        argv: list[str],
        *,
        stdin: str = "",
    ) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()

        with (
            patch.object(
                sys,
                "stdin",
                StringIO(stdin),
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            try:
                code = main(argv)
            except SystemExit as exc:
                code = int(exc.code or 0)

        return (
            int(code),
            stdout.getvalue(),
            stderr.getvalue(),
        )

    def source_file(
        self,
        text: str,
    ):
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".vectis",
            delete=False,
        )

        tmp.write(text)
        tmp.close()

        self.addCleanup(
            lambda: Path(tmp.name).unlink(
                missing_ok=True
            )
        )

        return tmp.name

    def test_help_lists_all_toolchain_commands(self):
        help_text = build_parser().format_help()

        for command in (
            "check",
            "parse",
            "plan",
            "run",
        ):
            self.assertIn(command, help_text)

    def test_main_without_command_prints_help(self):
        code, stdout, stderr = self.invoke([])

        self.assertEqual(code, 0)
        self.assertIn(
            "VECTIS deterministic language toolchain",
            stdout,
        )
        self.assertEqual(stderr, "")

    def test_version_is_exposed(self):
        code, stdout, stderr = self.invoke(
            ["--version"]
        )

        self.assertEqual(code, 0)
        self.assertIn(__version__, stdout)
        self.assertEqual(stderr, "")

    def test_check_accepts_valid_empty_program(self):
        source = self.source_file("")

        code, stdout, stderr = self.invoke(
            ["check", source]
        )

        self.assertEqual(code, 0)
        self.assertEqual(stdout.strip(), "OK")
        self.assertEqual(stderr, "")

    def test_check_rejects_invalid_source(self):
        source = self.source_file("@")

        code, stdout, stderr = self.invoke(
            ["check", source]
        )

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertTrue(stderr.strip())

    def test_check_reads_standard_input(self):
        code, stdout, stderr = self.invoke(
            ["check"],
            stdin="",
        )

        self.assertEqual(code, 0)
        self.assertEqual(stdout.strip(), "OK")
        self.assertEqual(stderr, "")

    def test_parse_emits_json(self):
        source = self.source_file("")

        code, stdout, stderr = self.invoke(
            ["parse", source]
        )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

        parsed = json.loads(stdout)

        self.assertIsInstance(parsed, dict)

    def test_plan_emits_execution_graph_json(self):
        source = self.source_file("")

        code, stdout, stderr = self.invoke(
            ["plan", source]
        )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

        graph = json.loads(stdout)

        self.assertEqual(graph["nodes"], [])
        self.assertEqual(graph["edges"], [])

    def test_run_executes_empty_program(self):
        source = self.source_file("")

        code, stdout, stderr = self.invoke(
            ["run", source]
        )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

        result = json.loads(stdout)

        self.assertTrue(result["success"])
        self.assertFalse(result["dry_run"])

    def test_run_supports_dry_run(self):
        source = self.source_file("")

        code, stdout, stderr = self.invoke(
            [
                "run",
                "--dry-run",
                source,
            ]
        )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

        result = json.loads(stdout)

        self.assertTrue(result["success"])
        self.assertTrue(result["dry_run"])

    def test_missing_source_file_is_user_error(self):
        code, stdout, stderr = self.invoke(
            [
                "check",
                "/definitely/not/a/vectis/file",
            ]
        )

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("vectis:", stderr)

    def test_cli_entrypoint_remains_in_pyproject(self):
        text = Path(
            "pyproject.toml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'vectis = "vectis.cli:main"',
            text,
        )


if __name__ == "__main__":
    unittest.main()

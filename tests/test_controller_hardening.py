from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import spectral_core_controller as controller


CONTROLLER_PATH = TOOLS / "spectral_core_controller.py"


class ControllerHardeningTests(unittest.TestCase):
    def test_nonprogress_count_survives_failure_class_reset(self):
        task_id = "HARDEN-NONPROGRESS"
        sentinel = object()
        previous = controller.TASK_SPECS.get(task_id, sentinel)
        artifact = (
            controller.ROOT
            / ".autonomy"
            / "runtime"
            / "hardening-test-artifact.txt"
        )

        try:
            artifact.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            artifact.write_text(
                "v1\n",
                encoding="utf-8",
            )

            task_path = artifact.relative_to(
                controller.ROOT
            ).as_posix()

            controller.TASK_SPECS[task_id] = {
                "required_files": [task_path],
            }

            state = {
                "current_task": task_id,
                "repair_failures": 1,
            }

            controller._preserve_nonprogress_failure_count(state)
            self.assertEqual(
                state["repair_failures"],
                1,
            )

            # A different failure path tries to reset the counter,
            # but the task-owned artifact did not change.
            state["repair_failures"] = 0
            controller._preserve_nonprogress_failure_count(state)
            self.assertEqual(
                state["repair_failures"],
                1,
            )

            # A later failure advances from the preserved count.
            state["repair_failures"] = 2
            controller._preserve_nonprogress_failure_count(state)
            self.assertEqual(
                state["repair_failures"],
                2,
            )

            # Real artifact progress changes the fingerprint and
            # permits a reset.
            artifact.write_text(
                "v2\n",
                encoding="utf-8",
            )
            state["repair_failures"] = 0
            controller._preserve_nonprogress_failure_count(state)
            self.assertEqual(
                state["repair_failures"],
                0,
            )
        finally:
            artifact.unlink(missing_ok=True)

            if previous is sentinel:
                controller.TASK_SPECS.pop(task_id, None)
            else:
                controller.TASK_SPECS[task_id] = previous

    def test_no_task_clears_progress_tracking(self):
        state = {
            "current_task": None,
            "repair_failures": 0,
            "_repair_progress_task": "OLD",
            "_repair_progress_fingerprint": "abc",
            "_repair_progress_failures": 4,
        }

        controller._preserve_nonprogress_failure_count(state)

        self.assertNotIn(
            "_repair_progress_task",
            state,
        )
        self.assertNotIn(
            "_repair_progress_fingerprint",
            state,
        )
        self.assertNotIn(
            "_repair_progress_failures",
            state,
        )

    def test_task_contract_block_is_fail_closed(self):
        source = CONTROLLER_PATH.read_text(
            encoding="utf-8"
        )
        anchor = source.index(
            "TASK CONTRACT BLOCK"
        )
        window = source[
            anchor : anchor + 2500
        ]

        self.assertIn(
            "state = load_state()",
            window,
        )
        self.assertIn(
            'state["current_task"] = task["id"]',
            window,
        )
        self.assertIn(
            "block_controller(",
            window,
        )
        self.assertIn(
            "task contract validation failed:",
            window,
        )
        self.assertIn(
            "return 0",
            window,
        )
        self.assertNotIn(
            "return 2",
            window,
        )


if __name__ == "__main__":
    unittest.main()

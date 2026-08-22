"""
Unit tests for context-checkpoint CLI and state synchronizer.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add script directory to sys.path
SCRIPT_DIR = (
    Path(__file__).resolve().parent.parent / "skills" / "context-checkpoint" / "scripts"
)
CHECKPOINT_SCRIPT = str(SCRIPT_DIR / "checkpoint.py")


class TestContextCheckpoint(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.checkpoint_file = self.base_path / ".checkpoint.json"
        self.session_file = self.base_path / "SESSION.md"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args):
        cmd = [
            sys.executable,
            CHECKPOINT_SCRIPT,
            "--file",
            str(self.checkpoint_file),
            "--session-file",
            str(self.session_file),
            *args,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def test_init_and_render(self):
        res = self.run_cli(
            "init",
            "--session-id",
            "test-session-001",
            "--goal",
            "Implement feature X",
            "--scope",
            "File A",
            "--scope",
            "File B",
            "--criteria",
            "Criteria 1",
            "--criteria",
            "Criteria 2",
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        self.assertTrue(self.checkpoint_file.exists())
        self.assertTrue(self.session_file.exists())

        with open(self.checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["session_id"], "test-session-001")
        self.assertEqual(data["goal"]["primary"], "Implement feature X")
        self.assertEqual(len(data["goal"]["scope_boundaries"]), 2)
        self.assertEqual(len(data["goal"]["acceptance_criteria"]), 2)

        with open(self.session_file, "r", encoding="utf-8") as f:
            md = f.read()

        self.assertIn("Implement feature X", md)
        self.assertIn("test-session-001", md)

    def test_milestones_and_decisions(self):
        # Init
        self.run_cli(
            "init", "--session-id", "test-session-002", "--goal", "Milestones Test"
        )

        # Add milestone
        res = self.run_cli(
            "milestone",
            "add",
            "--title",
            "Setup scaffolding",
            "--status",
            "in_progress",
        )
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")

        # Complete milestone
        res = self.run_cli("milestone", "complete", "M1", "--verify-cmd", "make test")
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")

        # Add decision
        res = self.run_cli(
            "decision",
            "add",
            "--topic",
            "Auth",
            "--choice",
            "JWT",
            "--rationale",
            "Stateless auth",
        )
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")

        # Add blocker
        res = self.run_cli(
            "blocker",
            "add",
            "--desc",
            "API rate limit",
            "--workaround",
            "Use mock",
        )
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")

        # Update context
        res = self.run_cli(
            "update-context",
            "--step",
            "Running tests",
            "--file-add",
            "tests/test_auth.py",
            "--next-action",
            "Review diff",
        )
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")

        # Validate
        res = self.run_cli("validate")
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}")

        with open(self.checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["milestones"][0]["status"], "completed")
        self.assertEqual(data["decisions"][0]["choice"], "JWT")
        self.assertEqual(data["blockers"][0]["description"], "API rate limit")
        self.assertEqual(data["active_context"]["current_step"], "Running tests")


if __name__ == "__main__":
    unittest.main()

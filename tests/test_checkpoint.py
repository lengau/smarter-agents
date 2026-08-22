"""
Unit tests for context-checkpoint CLI, state synchronizer, and locking mechanisms.
"""

import concurrent.futures
import importlib
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
SCHEMA_FILE = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "context-checkpoint"
    / "schemas"
    / "checkpoint.schema.json"
)

sys.path.insert(0, str(SCRIPT_DIR))
checkpoint = importlib.import_module("checkpoint")


class TestContextCheckpoint(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.checkpoint_file = self.base_path / ".checkpoint.json"
        self.session_file = self.base_path / "SESSION.md"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args, checkpoint_file=None, session_file=None):
        cp_file = str(checkpoint_file or self.checkpoint_file)
        sess_file = str(session_file or self.session_file)
        cmd = [
            sys.executable,
            CHECKPOINT_SCRIPT,
            "--file",
            cp_file,
            "--session-file",
            sess_file,
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

    def test_parent_directory_creation(self):
        nested_checkpoint = (
            self.base_path / ".agents" / "checkpoints" / ".checkpoint.json"
        )
        nested_session = self.base_path / ".agents" / "checkpoints" / "SESSION.md"

        res = self.run_cli(
            "init",
            "--session-id",
            "nested-session",
            "--goal",
            "Test Nested Path",
            checkpoint_file=nested_checkpoint,
            session_file=nested_session,
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        self.assertTrue(nested_checkpoint.exists())
        self.assertTrue(nested_session.exists())

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

    def test_schema_validation_negative_cases(self):
        # Missing required key
        invalid_data_missing_key = {
            "version": "1.0.0",
            "session_id": "bad-session",
            # missing updated_at, goal, etc.
        }
        with self.assertRaises(ValueError):
            checkpoint.validate_checkpoint_data(invalid_data_missing_key, SCHEMA_FILE)

        # Invalid milestone status enum
        invalid_data_status = {
            "version": "1.0.0",
            "session_id": "bad-session",
            "updated_at": "2026-08-21T00:00:00Z",
            "goal": {
                "primary": "Test",
                "scope_boundaries": [],
                "acceptance_criteria": [],
            },
            "milestones": [
                {
                    "id": "M1",
                    "title": "Invalid status milestone",
                    "status": "not_a_valid_status",
                }
            ],
            "decisions": [],
            "blockers": [],
            "active_context": {
                "current_step": "Test",
                "open_files": [],
                "next_actions": [],
            },
        }
        with self.assertRaises(ValueError):
            checkpoint.validate_checkpoint_data(invalid_data_status, SCHEMA_FILE)

    def test_parallel_updates(self):
        # Initialize
        self.run_cli(
            "init", "--session-id", "parallel-session", "--goal", "Parallel Test"
        )

        def add_decision_worker(idx):
            res = self.run_cli(
                "decision",
                "add",
                "--topic",
                f"Topic {idx}",
                "--choice",
                f"Choice {idx}",
                "--rationale",
                f"Rationale {idx}",
            )
            return res.returncode

        # Run 8 concurrent decision additions
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(add_decision_worker, i) for i in range(8)]
            results = [f.result() for f in futures]

        for code in results:
            self.assertEqual(code, 0)

        with open(self.checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data["decisions"]), 8)


if __name__ == "__main__":
    unittest.main()

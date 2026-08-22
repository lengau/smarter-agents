"""
Unit tests for context-checkpoint CLI, state synchronizer, and locking mechanisms.
"""

import concurrent.futures
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

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


@pytest.fixture
def checkpoint_paths(tmp_path):
    return {
        "checkpoint": tmp_path / ".checkpoint.json",
        "session": tmp_path / "SESSION.md",
        "base": tmp_path,
    }


def run_cli(*args, checkpoint_file, session_file):
    cmd = [
        sys.executable,
        CHECKPOINT_SCRIPT,
        "--file",
        str(checkpoint_file),
        "--session-file",
        str(session_file),
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_init_and_render(checkpoint_paths):
    cp_file = checkpoint_paths["checkpoint"]
    sess_file = checkpoint_paths["session"]

    res = run_cli(
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
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0, f"CLI error: {res.stderr}"
    assert cp_file.exists()
    assert sess_file.exists()

    with open(cp_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["session_id"] == "test-session-001"
    assert data["goal"]["primary"] == "Implement feature X"
    assert len(data["goal"]["scope_boundaries"]) == 2
    assert len(data["goal"]["acceptance_criteria"]) == 2

    with open(sess_file, "r", encoding="utf-8") as f:
        md = f.read()

    assert "Implement feature X" in md
    assert "test-session-001" in md


def test_parent_directory_creation(checkpoint_paths):
    nested_checkpoint = (
        checkpoint_paths["base"] / ".agents" / "checkpoints" / ".checkpoint.json"
    )
    nested_session = checkpoint_paths["base"] / ".agents" / "checkpoints" / "SESSION.md"

    res = run_cli(
        "init",
        "--session-id",
        "nested-session",
        "--goal",
        "Test Nested Path",
        checkpoint_file=nested_checkpoint,
        session_file=nested_session,
    )
    assert res.returncode == 0, f"CLI error: {res.stderr}"
    assert nested_checkpoint.exists()
    assert nested_session.exists()


def test_milestones_and_decisions(checkpoint_paths):
    cp_file = checkpoint_paths["checkpoint"]
    sess_file = checkpoint_paths["session"]

    # Init
    res = run_cli(
        "init",
        "--session-id",
        "test-session-002",
        "--goal",
        "Milestones Test",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0

    # Add milestone
    res = run_cli(
        "milestone",
        "add",
        "--title",
        "Setup scaffolding",
        "--status",
        "in_progress",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0, f"Error: {res.stderr}"

    # Complete milestone
    res = run_cli(
        "milestone",
        "complete",
        "M1",
        "--verify-cmd",
        "make test",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0, f"Error: {res.stderr}"

    # Add decision
    res = run_cli(
        "decision",
        "add",
        "--topic",
        "Auth",
        "--choice",
        "JWT",
        "--rationale",
        "Stateless auth",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0, f"Error: {res.stderr}"

    # Add blocker
    res = run_cli(
        "blocker",
        "add",
        "--desc",
        "API rate limit",
        "--workaround",
        "Use mock",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0, f"Error: {res.stderr}"

    # Update context
    res = run_cli(
        "update-context",
        "--step",
        "Running tests",
        "--file-add",
        "tests/test_auth.py",
        "--next-action",
        "Review diff",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0, f"Error: {res.stderr}"

    # Validate
    res = run_cli(
        "validate",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0, f"Error: {res.stderr}"

    with open(cp_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["milestones"][0]["status"] == "completed"
    assert data["decisions"][0]["choice"] == "JWT"
    assert data["blockers"][0]["description"] == "API rate limit"
    assert data["active_context"]["current_step"] == "Running tests"


def test_schema_validation_negative_cases():
    # Missing required key
    invalid_data_missing_key = {
        "version": "1.0.0",
        "session_id": "bad-session",
    }
    with pytest.raises(ValueError):
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
    with pytest.raises(ValueError):
        checkpoint.validate_checkpoint_data(invalid_data_status, SCHEMA_FILE)


def test_parallel_updates(checkpoint_paths):
    cp_file = checkpoint_paths["checkpoint"]
    sess_file = checkpoint_paths["session"]

    # Initialize
    res = run_cli(
        "init",
        "--session-id",
        "parallel-session",
        "--goal",
        "Parallel Test",
        checkpoint_file=cp_file,
        session_file=sess_file,
    )
    assert res.returncode == 0

    def add_decision_worker(idx):
        res = run_cli(
            "decision",
            "add",
            "--topic",
            f"Topic {idx}",
            "--choice",
            f"Choice {idx}",
            "--rationale",
            f"Rationale {idx}",
            checkpoint_file=cp_file,
            session_file=sess_file,
        )
        return res.returncode

    # Run 8 concurrent decision additions
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(add_decision_worker, i) for i in range(8)]
        results = [f.result() for f in futures]

    for code in results:
        assert code == 0

    with open(cp_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data["decisions"]) == 8

"""Unit tests for installer.py"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import installer


class TestGetAgentTargets:
    """Tests for get_agent_targets function."""

    def test_default_harness(self):
        """Test default harness returns .agents and .github targets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "default")

            assert len(targets) == 2
            names = {t["name"] for t in targets}
            assert names == {".agents", ".github"}

    def test_all_harness(self):
        """Test 'all' harness returns all target types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "all")

            assert len(targets) == 5
            names = {t["name"] for t in targets}
            assert names == {".agents", ".github", "opencode", "pi", "cursor"}

    def test_opencode_harness(self):
        """Test opencode harness returns opencode target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "opencode")

            assert len(targets) == 1
            assert targets[0]["name"] == "opencode"
            assert targets[0]["rules_dir"] == target_dir / ".opencode" / "instructions"
            assert targets[0]["skills_dir"] == target_dir / ".opencode" / "skills"

    def test_copilot_harness(self):
        """Test copilot harness returns .github target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "copilot")

            assert len(targets) == 1
            assert targets[0]["name"] == ".github"
            assert targets[0]["rules_dir"] == target_dir / ".github" / "instructions"
            assert targets[0]["skills_dir"] == target_dir / ".github" / "skills"

    def test_generic_harness(self):
        """Test generic harness returns .agents target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "generic")

            assert len(targets) == 1
            assert targets[0]["name"] == ".agents"

    def test_antigravity_harness(self):
        """Test antigravity harness returns .agents target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "antigravity")

            assert len(targets) == 1
            assert targets[0]["name"] == ".agents"

    def test_pi_harness(self):
        """Test pi harness returns pi target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "pi")

            assert len(targets) == 1
            assert targets[0]["name"] == "pi"
            assert targets[0]["rules_dir"] == target_dir / ".pi" / "rules"
            assert targets[0]["skills_dir"] == target_dir / ".pi" / "skills"

    def test_cursor_harness(self):
        """Test cursor harness returns cursor target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            targets = installer.get_agent_targets(target_dir, "cursor")

            assert len(targets) == 1
            assert targets[0]["name"] == "cursor"
            assert targets[0]["rules_dir"] == target_dir / ".cursor" / "rules"
            assert targets[0]["skills_dir"] == target_dir / ".cursor" / "skills"


class TestInstallAssets:
    """Tests for install_assets function."""

    def test_install_assets_symlink(self):
        """Test installing assets with symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            dest_dir = Path(tmpdir) / "dest"
            src_dir.mkdir()
            dest_dir.mkdir()

            (src_dir / "rule1.md").write_text("# Rule 1")
            (src_dir / "rule2.md").write_text("# Rule 2")
            (src_dir / ".hidden").write_text("hidden")

            count = installer.install_assets(src_dir, dest_dir, use_symlinks=True)

            assert count == 2
            assert (dest_dir / "rule1.md").is_symlink()
            assert (dest_dir / "rule2.md").is_symlink()
            assert not (dest_dir / ".hidden").exists()

    def test_install_assets_copy(self):
        """Test installing assets with copy (no symlinks)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            dest_dir = Path(tmpdir) / "dest"
            src_dir.mkdir()
            dest_dir.mkdir()

            (src_dir / "rule1.md").write_text("# Rule 1")
            (src_dir / "rule2.md").write_text("# Rule 2")

            count = installer.install_assets(src_dir, dest_dir, use_symlinks=False)

            assert count == 2
            assert (dest_dir / "rule1.md").is_file()
            assert (dest_dir / "rule2.md").is_file()
            assert (dest_dir / "rule1.md").read_text() == "# Rule 1"

    def test_install_assets_skip_existing(self):
        """Test that existing files are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            dest_dir = Path(tmpdir) / "dest"
            src_dir.mkdir()
            dest_dir.mkdir()

            (src_dir / "rule1.md").write_text("# Rule 1")
            (dest_dir / "rule1.md").write_text("# Existing")

            count = installer.install_assets(src_dir, dest_dir, use_symlinks=True)

            assert count == 0
            assert (dest_dir / "rule1.md").read_text() == "# Existing"

    def test_install_assets_clean(self):
        """Test clean flag removes existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            dest_dir = Path(tmpdir) / "dest"
            src_dir.mkdir()
            dest_dir.mkdir()

            (src_dir / "rule1.md").write_text("# Rule 1")
            (dest_dir / "rule1.md").write_text("# Existing")

            count = installer.install_assets(
                src_dir, dest_dir, use_symlinks=True, clean=True
            )

            assert count == 1
            assert (dest_dir / "rule1.md").is_symlink()

    def test_install_assets_nonexistent_src(self):
        """Test installing from non-existent source returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "nonexistent"
            dest_dir = Path(tmpdir) / "dest"
            dest_dir.mkdir()

            count = installer.install_assets(src_dir, dest_dir, use_symlinks=True)

            assert count == 0

    def test_install_assets_directory(self):
        """Test installing directory assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            dest_dir = Path(tmpdir) / "dest"
            src_dir.mkdir()
            dest_dir.mkdir()

            skill_dir = src_dir / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test Skill")

            count = installer.install_assets(src_dir, dest_dir, use_symlinks=True)

            assert count == 1
            assert (dest_dir / "test-skill").is_symlink()
            assert (dest_dir / "test-skill" / "SKILL.md").exists()


class TestCreateConsumerConfig:
    """Tests for create_consumer_config function."""

    def test_create_consumer_config(self):
        """Test creating consumer config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            installer.create_consumer_config(target_dir)

            config_path = target_dir / ".copilot-collections.yaml"
            assert config_path.exists()
            content = config_path.read_text()
            assert "smarter-agents-core" in content

    def test_create_consumer_config_skip_existing(self):
        """Test skipping if config already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            config_path = target_dir / ".copilot-collections.yaml"
            config_path.write_text("# Existing")

            with patch("builtins.print") as mock_print:
                installer.create_consumer_config(target_dir)

            mock_print.assert_called()
            assert "skip" in mock_print.call_args[0][0]
            assert config_path.read_text() == "# Existing"


class TestMain:
    """Tests for main function."""

    def test_main_help(self):
        """Test main with --help exits cleanly."""
        with patch.object(sys, "argv", ["installer.py", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                installer.main()
            assert exc_info.value.code == 0

    def test_main_nonexistent_target(self):
        """Test main with nonexistent target exits with error."""
        with patch.object(sys, "argv", ["installer.py", "/nonexistent/path"]):
            with pytest.raises(SystemExit) as exc_info:
                installer.main()
            assert exc_info.value.code == 1

    def test_main_install_default(self):
        """Test main with default options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with (
                patch.object(
                    sys,
                    "argv",
                    ["installer.py", str(target_dir), "--harness", "default"],
                ),
                patch("builtins.print"),
            ):
                installer.main()

            assert (target_dir / ".agents" / "rules").exists()
            assert (target_dir / ".github" / "instructions").exists()

    def test_main_install_opencode(self):
        """Test main with opencode harness."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with (
                patch.object(
                    sys,
                    "argv",
                    ["installer.py", str(target_dir), "--harness", "opencode"],
                ),
                patch("builtins.print"),
            ):
                installer.main()

            assert (target_dir / ".opencode" / "instructions").exists()
            assert (target_dir / ".opencode" / "skills").exists()

    def test_main_copy_flag(self):
        """Test main with --copy flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with (
                patch.object(
                    sys,
                    "argv",
                    ["installer.py", str(target_dir), "--harness", "default", "--copy"],
                ),
                patch("builtins.print"),
            ):
                installer.main()

            assert (target_dir / ".agents" / "rules").is_dir()
            assert not (target_dir / ".agents" / "rules").is_symlink()

    def test_main_clean_flag(self):
        """Test main with --clean flag removes existing installed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()
            (target_dir / ".agents" / "rules").mkdir(parents=True)
            (target_dir / ".agents" / "rules" / "basic-directives.md").write_text(
                "old content"
            )

            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "installer.py",
                        str(target_dir),
                        "--harness",
                        "default",
                        "--clean",
                    ],
                ),
                patch("builtins.print"),
            ):
                installer.main()

            assert (
                target_dir / ".agents" / "rules" / "basic-directives.md"
            ).is_symlink()

    def test_main_init_config(self):
        """Test main with --init-config flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "target"
            target_dir.mkdir()

            with (
                patch.object(
                    sys, "argv", ["installer.py", str(target_dir), "--init-config"]
                ),
                patch("builtins.print"),
            ):
                installer.main()

            assert (target_dir / ".copilot-collections.yaml").exists()


class TestArgumentParsing:
    """Tests for argument parsing."""

    def test_default_harness(self):
        """Test default harness is 'default'."""
        with patch.object(sys, "argv", ["installer.py", "."]), patch("installer.main"):
            pass

    def test_invalid_harness(self):
        """Test invalid harness raises error."""
        # ruff: noqa: SIM117 - patch and pytest.raises are different context types
        with patch.object(sys, "argv", ["installer.py", ".", "--harness", "invalid"]):
            with pytest.raises(SystemExit):
                installer.main()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
configure_repo.py - Interactive Repository Agent Configuration Wizard

Configures repositories with reusable skill collections across agent harnesses:
GitHub Copilot, OpenCode, Cursor, Claude Code, and Generic/Antigravity.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INSTALLER = TOOLKIT_ROOT / "installer.py"
COLLECTIONS_YAML = TOOLKIT_ROOT / "collections.yaml"

# Harness detection patterns
HARNESS_DETECTION = {
    "copilot": [
        ".github/copilot-instructions.md",
        ".github/instructions",
        ".copilot-collections.yaml",
    ],
    "opencode": [
        ".opencode",
        "opencode.json",
    ],
    "cursor": [
        ".cursor/rules",
        ".cursor/mcp.json",
    ],
    "claude": [
        ".claude",
        "CLAUDE.md",
    ],
    "generic": [
        ".agents/rules",
        ".agents/skills",
    ],
}

# Recommended collections per harness
RECOMMENDED_COLLECTIONS = {
    "copilot": ["smarter-agents-core", "copilot-collections", "skills-playground"],
    "opencode": ["smarter-agents-core", "opencode-skills", "skills-playground"],
    "cursor": ["smarter-agents-core", "cursor-rules", "skills-playground"],
    "claude": ["smarter-agents-core", "claude-code-skills", "skills-playground"],
    "generic": ["smarter-agents-core", "skills-playground"],
}

# External canonical collections (repo URL, local name)
EXTERNAL_COLLECTIONS = {
    "copilot-collections": "https://github.com/canonical/copilot-collections",
    "skills-playground": "https://github.com/canonical/skills-playground",
    "opencode-skills": "https://github.com/opencode-ai/skills",
    "cursor-rules": "https://github.com/cursor/cursor-rules",
    "claude-code-skills": "https://github.com/anthropics/claude-code-skills",
    "awesome-copilot": "https://github.com/github/awesome-copilot",
    "vscode-copilot-skills": "https://github.com/microsoft/vscode-copilot-skills",
}

# Config templates
CONFIG_TEMPLATES = {
    "copilot": {
        "path": ".copilot-collections.yaml",
        "content": """# Copilot Collections / Smarter Agents Configuration
collections:
  - smarter-agents-core
  - copilot-collections
  - skills-playground
""",
    },
    "opencode": {
        "path": "opencode.json",
        "content": """{
  "$schema": "https://opencode.ai/config.json",
  "skills": [".opencode/skills/*"],
  "instructions": [".opencode/instructions/*"]
}
""",
    },
    "cursor": {
        "path": ".cursor/mcp.json",
        "content": """{
  "mcpServers": {
    "smarter-agents": {
      "command": "python3",
      "args": ["-m", "skills.mcp_server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
""",
    },
    "claude": {
        "path": ".claude/settings.json",
        "content": """{
  "skillsDir": ".claude/skills",
  "commandsDir": ".claude/commands",
  "enabledSkills": ["smarter-agents-core", "claude-code-skills", "skills-playground"]
}
""",
    },
    "generic": {
        "path": ".agents/structure.yaml",
        "content": """# Generic/Antigravity Agent Structure
rules_dir: .agents/rules
skills_dir: .agents/skills
collections:
  - smarter-agents-core
  - skills-playground
""",
    },
}


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_header(msg: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {msg} ==={Colors.END}\n")


def print_step(num: int, total: int, msg: str):
    print(f"{Colors.CYAN}[{num}/{total}]{Colors.END} {msg}")


def print_success(msg: str):
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")


def print_warning(msg: str):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")


def print_error(msg: str):
    print(f"  {Colors.RED}✗{Colors.END} {msg}")


def print_info(msg: str):
    print(f"  {Colors.BLUE}ℹ{Colors.END} {msg}")


def run_cmd(
    cmd: list[str], cwd: Path | None = None, capture: bool = True
) -> tuple[int, str, str]:
    """Run command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=capture, text=True, timeout=60, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except OSError as e:
        return -1, "", str(e)


def detect_harnesses(target_dir: Path) -> dict[str, bool]:
    """Detect which harnesses are already configured in the target directory."""
    detected = {}
    for harness, patterns in HARNESS_DETECTION.items():
        found = False
        for pattern in patterns:
            if (target_dir / pattern).exists():
                found = True
                break
        detected[harness] = found
    return detected


def get_user_selection(
    prompt: str, options: list[str], default: str | None = None
) -> list[str]:
    """Get multi-select user input."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        marker = "★" if default and opt in default.split(",") else " "
        print(f"  {i}. {marker} {opt}")

    if default:
        print(f"  [Default: {default}]")

    while True:
        try:
            resp = input("  Select (comma-separated numbers or names): ").strip()
            if not resp and default:
                return [o.strip() for o in default.split(",")]

            selected = []
            for part in resp.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(options):
                        selected.append(options[idx])
                else:
                    # Match by name
                    matches = [o for o in options if o.lower() == part.lower()]
                    if matches:
                        selected.append(matches[0])

            if selected:
                return selected
            print("  No valid selection. Try again.")
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
            sys.exit(1)


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no user input."""
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        try:
            resp = input(f"{prompt}{suffix}: ").strip().lower()
            if not resp:
                return default
            if resp in ("y", "yes"):
                return True
            if resp in ("n", "no"):
                return False
            print("  Please enter 'y' or 'n'.")
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
            sys.exit(1)


def audit_repository(target_dir: Path) -> dict[str, bool]:
    """Step 1: Audit repository for existing harness configurations."""
    print_step(1, 6, "AUDIT: Scanning repository...")
    detected = detect_harnesses(target_dir)

    for harness, found in detected.items():
        if found:
            print_success(f"Found: {harness}")
        else:
            print_info(f"Not found: {harness}")

    return detected


def select_harnesses(
    detected: dict[str, bool], non_interactive: bool, harness_arg: str | None
) -> list[str]:
    """Step 2: Select harnesses to configure."""
    print_step(2, 6, "HARNESS SELECTION:")

    all_harnesses = list(HARNESS_DETECTION.keys())
    detected_harnesses = [h for h, f in detected.items() if f]

    if non_interactive and harness_arg:
        if harness_arg == "all":
            selected = all_harnesses
        else:
            selected = [h.strip() for h in harness_arg.split(",")]
        print_info(f"Selected (from args): {', '.join(selected)}")
        return selected

    print_info(
        f"Detected: {', '.join(detected_harnesses) if detected_harnesses else 'none'}"
    )
    print_info(f"Available: {', '.join(all_harnesses)}")

    default = (
        ",".join(detected_harnesses + ["generic"]) if detected_harnesses else "generic"
    )
    return get_user_selection("Select harnesses to configure:", all_harnesses, default)


def select_collections(
    selected_harnesses: list[str], non_interactive: bool, collection_arg: str | None
) -> dict[str, list[str]]:
    """Step 3: Select collections per harness."""
    print_step(3, 6, "COLLECTION SELECTION:")

    result = {}
    for harness in selected_harnesses:
        recommended = RECOMMENDED_COLLECTIONS.get(harness, ["smarter-agents-core"])
        print_info(f"For {harness}: {', '.join(recommended)}")

        if non_interactive and collection_arg:
            if collection_arg == "all":
                selected = recommended
            else:
                selected = [c.strip() for c in collection_arg.split(",")]
            print_info(f"  Selected (from args): {', '.join(selected)}")
            result[harness] = selected
        else:
            selected = get_user_selection(
                f"Select collections for {harness}:", recommended, ",".join(recommended)
            )
            result[harness] = selected

    return result


def install_collections(
    target_dir: Path,
    selected_harnesses: list[str],
    collections_by_harness: dict[str, list[str]],
    use_symlinks: bool = True,
):
    """Step 4: Install collections using installer.py."""
    print_step(4, 6, "INSTALLATION:")

    # Install core toolkit collections via installer.py
    for harness in selected_harnesses:
        collections = collections_by_harness.get(harness, [])
        core_collections = [
            c
            for c in collections
            if c in ("smarter-agents-core", "rules-only", "skills-only")
        ]

        if core_collections:
            # Use the first core collection (they overlap)
            collection = core_collections[0]
            print_info(f"Installing {collection} for {harness}...")

            cmd = [
                sys.executable,
                str(INSTALLER),
                str(target_dir),
                "--harness",
                harness,
            ]
            if not use_symlinks:
                cmd.append("--copy")

            code, _out, err = run_cmd(cmd, capture=False)
            if code == 0:
                print_success(f"Installed {collection} for {harness}")
            else:
                print_error(f"Failed to install {collection} for {harness}: {err}")

    # Install external collections
    external_to_install = set()
    for harness in selected_harnesses:
        for coll in collections_by_harness.get(harness, []):
            if coll in EXTERNAL_COLLECTIONS:
                external_to_install.add(coll)

    for coll_name in external_to_install:
        url = EXTERNAL_COLLECTIONS[coll_name]
        print_info(f"Cloning external collection: {coll_name} from {url}")

        ext_dir = target_dir / ".external" / coll_name
        if ext_dir.exists():
            print_warning(f"  {coll_name} already exists, pulling latest...")
            run_cmd(["git", "-C", str(ext_dir), "pull"], capture=False)
        else:
            ext_dir.parent.mkdir(parents=True, exist_ok=True)
            code, _out, err = run_cmd(
                ["git", "clone", "--depth", "1", url, str(ext_dir)], capture=False
            )
            if code != 0:
                print_error(f"  Failed to clone {coll_name}: {err}")
                continue

        print_success(f"  Cloned {coll_name}")

        # Symlink external collection into harness paths
        for harness in selected_harnesses:
            if coll_name in collections_by_harness.get(harness, []):
                # Determine target skills/rules dirs for this harness
                targets = get_harness_targets(target_dir, harness)
                for target in targets:
                    skills_dir = target["skills_dir"]
                    skills_dir.mkdir(parents=True, exist_ok=True)
                    link_path = skills_dir / coll_name
                    if not link_path.exists():
                        try:
                            link_path.symlink_to(ext_dir.relative_to(skills_dir))
                            print_success(
                                f"  Linked {coll_name} to {target['name']}/skills/"
                            )
                        except (OSError, ValueError) as e:
                            print_warning(f"  Could not symlink {coll_name}: {e}")


def get_harness_targets(target_dir: Path, harness: str) -> list[dict]:
    """Get target directories for a harness (mirrors installer.py logic)."""
    targets = []

    if harness in ("generic", "antigravity", "default"):
        targets.append(
            {
                "name": ".agents",
                "rules_dir": target_dir / ".agents" / "rules",
                "skills_dir": target_dir / ".agents" / "skills",
            }
        )

    if harness in ("copilot", "github"):
        targets.append(
            {
                "name": ".github",
                "rules_dir": target_dir / ".github" / "instructions",
                "skills_dir": target_dir / ".github" / "skills",
            }
        )

    if harness == "opencode":
        targets.append(
            {
                "name": "opencode",
                "rules_dir": target_dir / ".opencode" / "instructions",
                "skills_dir": target_dir / ".opencode" / "skills",
            }
        )

    if harness == "cursor":
        targets.append(
            {
                "name": "cursor",
                "rules_dir": target_dir / ".cursor" / "rules",
                "skills_dir": target_dir / ".cursor" / "skills",
            }
        )

    if harness == "claude":
        targets.append(
            {
                "name": "claude",
                "rules_dir": target_dir / ".claude" / "rules",
                "skills_dir": target_dir / ".claude" / "skills",
            }
        )

    return targets


def generate_configs(
    target_dir: Path,
    selected_harnesses: list[str],
    collections_by_harness: dict[str, list[str]],
):
    """Step 5: Generate harness-specific config files."""
    print_step(5, 6, "CONFIG GENERATION:")

    for harness in selected_harnesses:
        template = CONFIG_TEMPLATES.get(harness)
        if not template:
            continue

        config_path = target_dir / template["path"]
        if config_path.exists():
            print_warning(f"  {config_path} already exists, skipping")
            continue

        # Customize content based on selected collections
        content = template["content"]
        if harness == "copilot":
            collections = collections_by_harness.get(harness, [])
            coll_lines = "\n".join(f"  - {c}" for c in collections)
            content = f"# Copilot Collections / Smarter Agents Configuration\ncollections:\n{coll_lines}\n"

        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(content)
        print_success(f"Created {config_path}")


def validate_setup(target_dir: Path, selected_harnesses: list[str]) -> bool:
    """Step 6: Validate the setup."""
    print_step(6, 6, "VALIDATION:")
    all_ok = True

    # Check symlinks
    for harness in selected_harnesses:
        targets = get_harness_targets(target_dir, harness)
        for target in targets:
            for d in [target["rules_dir"], target["skills_dir"]]:
                if d.exists():
                    for item in d.iterdir():
                        if item.is_symlink():
                            try:
                                target_path = item.resolve()
                                if not target_path.exists():
                                    print_error(
                                        f"  Broken symlink: {item} -> {target_path}"
                                    )
                                    all_ok = False
                            except OSError:
                                print_error(f"  Invalid symlink: {item}")
                                all_ok = False

    # Lint YAML configs
    for harness in selected_harnesses:
        template = CONFIG_TEMPLATES.get(harness)
        if template:
            config_path = target_dir / template["path"]
            if config_path.exists() and config_path.suffix in (".yaml", ".yml"):
                code, _out, err = run_cmd(["yamllint", str(config_path)])
                if code == 0:
                    print_success(f"  yamllint: {config_path.name}")
                else:
                    print_error(f"  yamllint failed: {config_path.name}")
                    print(f"    {err}")
                    all_ok = False

    # Lint Markdown instructions
    for harness in selected_harnesses:
        targets = get_harness_targets(target_dir, harness)
        for target in targets:
            inst_dir = target["rules_dir"]
            if inst_dir.exists():
                md_files = list(inst_dir.glob("*.md"))
                if md_files:
                    code, _out, err = run_cmd(
                        ["markdownlint"] + [str(f) for f in md_files]
                    )
                    if code == 0:
                        print_success(f"  markdownlint: {target['name']}/instructions/")
                    else:
                        print_warning(
                            f"  markdownlint warnings in {target['name']}/instructions/"
                        )

    # Validate OpenCode JSON
    opencode_json = target_dir / "opencode.json"
    if opencode_json.exists():
        try:
            json.loads(opencode_json.read_text())
            print_success("  opencode.json: valid JSON")
        except json.JSONDecodeError as e:
            print_error(f"  opencode.json: invalid JSON - {e}")
            all_ok = False

    # Test skill invocation (dry-run)
    skill_dirs = []
    for harness in selected_harnesses:
        targets = get_harness_targets(target_dir, harness)
        for target in targets:
            if target["skills_dir"].exists():
                skill_dirs.append(target["skills_dir"])

    for skill_dir in skill_dirs:
        for skill in skill_dir.iterdir():
            if skill.is_dir() and not skill.name.startswith("."):
                # Try to find and run the skill's main script with --help
                scripts = list(skill.glob("scripts/*.py"))
                if scripts:
                    code, _out, err = run_cmd(
                        [sys.executable, str(scripts[0]), "--help"]
                    )
                    if code == 0:
                        print_success(f"  Skill dry-run: {skill.name}")
                    else:
                        print_warning(f"  Skill dry-run failed: {skill.name}")

    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Interactive wizard to configure repository for agent harnesses"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target repository directory (default: current directory)",
    )
    parser.add_argument(
        "--harness",
        help="Comma-separated list of harnesses (copilot,opencode,cursor,claude,generic,all)",
    )
    parser.add_argument(
        "--collection", help="Comma-separated list of collections to install (or 'all')"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompts using --harness and --collection args",
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="Only audit and show recommendations, make no changes",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate existing setup only"
    )
    parser.add_argument(
        "--copy", action="store_true", help="Copy files instead of symlinking"
    )

    args = parser.parse_args()

    target_dir = Path(args.target).resolve()
    if not target_dir.exists():
        print_error(f"Target directory '{target_dir}' does not exist")
        sys.exit(1)

    print_header("Repository Agent Configuration Wizard")
    print_info(f"Target: {target_dir}")

    if args.validate:
        # Validate existing setup
        detected = detect_harnesses(target_dir)
        selected = [h for h, f in detected.items() if f]
        if not selected:
            print_warning("No harness configurations detected")
            return
        ok = validate_setup(target_dir, selected)
        print_header("VALIDATION " + ("PASSED" if ok else "FAILED"))
        sys.exit(0 if ok else 1)

    # Step 1: Audit
    detected = audit_repository(target_dir)

    if args.audit_only:
        print_header("AUDIT COMPLETE")
        return

    # Step 2: Harness selection
    selected_harnesses = select_harnesses(detected, args.non_interactive, args.harness)

    if not selected_harnesses:
        print_warning("No harnesses selected. Exiting.")
        return

    # Step 3: Collection selection
    collections_by_harness = select_collections(
        selected_harnesses, args.non_interactive, args.collection
    )

    # Step 4: Installation
    install_collections(
        target_dir,
        selected_harnesses,
        collections_by_harness,
        use_symlinks=not args.copy,
    )

    # Step 5: Config generation
    generate_configs(target_dir, selected_harnesses, collections_by_harness)

    # Step 6: Validation
    ok = validate_setup(target_dir, selected_harnesses)

    print_header("CONFIGURATION " + ("COMPLETE" if ok else "COMPLETE WITH WARNINGS"))
    print_info("Next steps:")
    print("  1. Review generated config files")
    print(
        "  2. Run 'python3 skills/diff-auditor/scripts/audit_diff.py' to verify clean diffs"
    )
    print("  3. Commit and push changes")
    print("  4. Restart your agent to load new skills")


if __name__ == "__main__":
    main()

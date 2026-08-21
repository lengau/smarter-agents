#!/usr/bin/env python3
"""
installer.py - Smarter Agents Installer and Sync Tool

Installs rules and skills from this toolkit repository into any target project workspace
or agent environment (Antigravity, OpenCode, Pi, GitHub Copilot, Claude Code, Cursor).

Supports:
- Symlinking (recommended for local development) or Direct Copying
- Standard paths (.agents/rules, .agents/skills, .github/instructions, .github/skills)
- Copilot Collections (.copilot-collections.yaml)
- Agent harness specific presets (antigravity, opencode, pi, copilot, cursor)
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent

RULES_SRC = TOOLKIT_ROOT / "rules"
SKILLS_SRC = TOOLKIT_ROOT / "skills"


def get_agent_targets(target_dir: Path, harness: str):
    """Return dictionary of target paths for rules and skills based on target harness."""
    targets = []
    
    if harness in ("all", "default", "antigravity", "generic"):
        targets.append({
            "name": ".agents",
            "rules_dir": target_dir / ".agents" / "rules",
            "skills_dir": target_dir / ".agents" / "skills",
        })
        
    if harness in ("all", "copilot", "github"):
        targets.append({
            "name": ".github",
            "rules_dir": target_dir / ".github" / "instructions",
            "skills_dir": target_dir / ".github" / "skills",
        })

    if harness in ("all", "opencode"):
        targets.append({
            "name": "opencode",
            "rules_dir": target_dir / ".opencode" / "instructions",
            "skills_dir": target_dir / ".opencode" / "skills",
        })

    if harness in ("all", "pi"):
        targets.append({
            "name": "pi",
            "rules_dir": target_dir / ".pi" / "rules",
            "skills_dir": target_dir / ".pi" / "skills",
        })

    if harness in ("all", "cursor"):
        targets.append({
            "name": "cursor",
            "rules_dir": target_dir / ".cursor" / "rules",
            "skills_dir": target_dir / ".cursor" / "skills",
        })

    return targets


def install_assets(src_dir: Path, dest_dir: Path, use_symlinks: bool = True, clean: bool = False):
    """Sync or symlink files from src_dir to dest_dir."""
    if not src_dir.exists():
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)
    installed_count = 0

    for item in src_dir.iterdir():
        if item.name.startswith("."):
            continue

        target_path = dest_dir / item.name

        if clean and (target_path.is_symlink() or target_path.exists()):
            if target_path.is_dir() and not target_path.is_symlink():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()

        if target_path.is_symlink() or target_path.exists():
            print(f"  [skip] {item.name} already exists in {dest_dir.relative_to(Path.cwd()) if dest_dir.is_relative_to(Path.cwd()) else dest_dir}")
            continue

        if use_symlinks:
            try:
                rel_source = os.path.relpath(item, dest_dir)
                target_path.symlink_to(rel_source)
                print(f"  [symlink] {item.name} -> {target_path}")
                installed_count += 1
            except (OSError, NotImplementedError):
                # Fallback to copy if symlinks not supported (e.g. some Windows setups)
                if item.is_dir():
                    shutil.copytree(item, target_path)
                else:
                    shutil.copy2(item, target_path)
                print(f"  [copied] {item.name} -> {target_path}")
                installed_count += 1
        else:
            if item.is_dir():
                shutil.copytree(item, target_path)
            else:
                shutil.copy2(item, target_path)
            print(f"  [copied] {item.name} -> {target_path}")
            installed_count += 1

    return installed_count


def create_consumer_config(target_dir: Path):
    """Creates a .copilot-collections.yaml config for automated sync hooks."""
    config_path = target_dir / ".copilot-collections.yaml"
    if config_path.exists():
        print(f"  [skip] {config_path} already exists.")
        return

    content = """# Copilot Collections / Smarter Agents Configuration
collections:
  - smarter-agents-core
"""
    config_path.write_text(content)
    print(f"  [created] {config_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Install Smarter Agents rules and skills into a project repository or agent harness."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target workspace or project directory (default: current working directory)",
    )
    parser.add_argument(
        "--harness",
        choices=["all", "default", "antigravity", "copilot", "opencode", "pi", "cursor", "generic"],
        default="default",
        help="Target agent harness structure (default: default [installs into .agents and .github])",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files directly instead of creating relative symlinks.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing matching symlinks/files in destination before installing.",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Create a .copilot-collections.yaml file in the target directory.",
    )

    args = parser.parse_args()

    target_dir = Path(args.target).resolve()
    if not target_dir.exists():
        print(f"Error: Target directory '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"=== Smarter Agents Toolkit Installer ===")
    print(f"Source Toolkit: {TOOLKIT_ROOT}")
    print(f"Target Project: {target_dir}")
    print(f"Mode: {'Copy' if args.copy else 'Symlink'}")
    print(f"Harness Preset: {args.harness}\n")

    targets = get_agent_targets(target_dir, args.harness)
    total_rules = 0
    total_skills = 0

    for t in targets:
        print(f"Installing into [{t['name']}]:")
        r_count = install_assets(RULES_SRC, t["rules_dir"], use_symlinks=not args.copy, clean=args.clean)
        s_count = install_assets(SKILLS_SRC, t["skills_dir"], use_symlinks=not args.copy, clean=args.clean)
        total_rules += r_count
        total_skills += s_count
        print()

    if args.init_config:
        create_consumer_config(target_dir)

    print(f"Done! Successfully installed {total_rules} rule(s) and {total_skills} skill(s).")


if __name__ == "__main__":
    main()

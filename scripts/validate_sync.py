"""Validate that collections.yaml and README.md stay in sync with rules/ and skills/ directories."""

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent


def get_rule_files():
    """Get all rule files in rules/ directory."""
    rules_dir = REPO_ROOT / "rules"
    if not rules_dir.exists():
        return set()
    return {f.name for f in rules_dir.iterdir() if f.is_file() and f.suffix == ".md"}


def get_skill_dirs():
    """Get all skill directories in skills/ directory."""
    skills_dir = REPO_ROOT / "skills"
    if not skills_dir.exists():
        return set()
    return {d.name for d in skills_dir.iterdir() if d.is_dir()}


def get_collections_rules():
    """Get all rule files referenced in collections.yaml."""
    collections_file = REPO_ROOT / "collections.yaml"
    if not collections_file.exists():
        return set()

    with open(collections_file) as f:
        data = yaml.safe_load(f)

    rules = set()
    for collection in data.get("collections", []):
        for rule in collection.get("rules", []):
            # Extract filename from path like "rules/basic-directives.md"
            rules.add(Path(rule).name)
    return rules


def get_collections_skills():
    """Get all skill directories referenced in collections.yaml."""
    collections_file = REPO_ROOT / "collections.yaml"
    if not collections_file.exists():
        return set()

    with open(collections_file) as f:
        data = yaml.safe_load(f)

    skills = set()
    for collection in data.get("collections", []):
        for skill in collection.get("skills", []):
            # Extract directory name from path like "skills/diff-auditor"
            skills.add(Path(skill).name)
    return skills


def get_readme_rules():
    """Extract rule files mentioned in README.md structure section."""
    readme_file = REPO_ROOT / "README.md"
    if not readme_file.exists():
        return set()

    content = readme_file.read_text()
    rules = set()

    in_structure = False
    in_rules_section = False
    for line in content.splitlines():
        if "Repository Structure" in line:
            in_structure = True
            continue
        if in_structure and line.strip() == "```":
            if in_rules_section:
                break
            continue
        if in_structure and "rules/" in line:
            in_rules_section = True
            continue
        if in_rules_section:
            # Lines in the tree use Unicode box drawing characters
            if "├──" in line or "└──" in line:
                # Extract filename from lines like "│   ├── basic-directives.md"
                for sep in ["├──", "└──"]:
                    parts = line.split(sep)
                    if len(parts) > 1:
                        filename = parts[1].strip().rstrip(",")
                        if filename.endswith(".md"):
                            rules.add(filename)
            elif not line.startswith("│") and not "└──" in line:
                # End of rules section
                break

    return rules


def get_readme_skills():
    """Extract skill directories mentioned in README.md structure section."""
    readme_file = REPO_ROOT / "README.md"
    if not readme_file.exists():
        return set()

    content = readme_file.read_text()
    skills = set()

    in_structure = False
    in_skills_section = False
    for line in content.splitlines():
        if "Repository Structure" in line:
            in_structure = True
            continue
        if in_structure and line.strip() == "```":
            if in_skills_section:
                break
            continue
        if in_structure and "skills/" in line:
            in_skills_section = True
            continue
        if in_skills_section:
            if "├──" in line or "└──" in line:
                for sep in ["├──", "└──"]:
                    parts = line.split(sep)
                    if len(parts) > 1:
                        skill_name = parts[1].strip().rstrip("/").rstrip(",")
                        # Remove trailing comments
                        if "#" in skill_name:
                            skill_name = skill_name.split("#")[0].strip()
                        # Remove trailing slash
                        skill_name = skill_name.rstrip("/")
                        if skill_name:
                            skills.add(skill_name)
            elif not line.startswith("│") and not "└──" in line:
                break

    return skills


def main():
    """Run validation checks."""
    errors = []
    warnings = []

    # Get actual files
    actual_rules = get_rule_files()
    actual_skills = get_skill_dirs()

    # Get collections references
    collections_rules = get_collections_rules()
    collections_skills = get_collections_skills()

    # Get README references
    readme_rules = get_readme_rules()
    readme_skills = get_readme_skills()

    # Check collections.yaml has all rules
    missing_in_collections = actual_rules - collections_rules
    if missing_in_collections:
        errors.append(
            f"Rules missing from collections.yaml: {sorted(missing_in_collections)}"
        )

    extra_in_collections = collections_rules - actual_rules
    if extra_in_collections:
        warnings.append(
            f"Rules in collections.yaml but not in rules/: {sorted(extra_in_collections)}"
        )

    # Check collections.yaml has all skills
    missing_skills_in_collections = actual_skills - collections_skills
    if missing_skills_in_collections:
        errors.append(
            f"Skills missing from collections.yaml: {sorted(missing_skills_in_collections)}"
        )

    extra_skills_in_collections = collections_skills - actual_skills
    if extra_skills_in_collections:
        warnings.append(
            f"Skills in collections.yaml but not in skills/: {sorted(extra_skills_in_collections)}"
        )

    # Check README has all rules
    missing_in_readme = actual_rules - readme_rules
    if missing_in_readme:
        errors.append(
            f"Rules missing from README.md structure: {sorted(missing_in_readme)}"
        )

    # Check README has all skills
    missing_skills_in_readme = actual_skills - readme_skills
    if missing_skills_in_readme:
        errors.append(
            f"Skills missing from README.md structure: {sorted(missing_skills_in_readme)}"
        )

    # Print results
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("All sync checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

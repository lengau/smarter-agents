#!/usr/bin/env python3
"""
checkpoint.py - Context Checkpoint CLI & State Synchronizer

Manage, update, and render compact session state checkpoints (.checkpoint.json and SESSION.md)
to survive aggressive context window compaction and multi-turn amnesia.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

DEFAULT_CHECKPOINT_FILE = ".checkpoint.json"
DEFAULT_SESSION_FILE = "SESSION.md"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "checkpoint.schema.json"


def get_current_iso_time() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def load_checkpoint(filepath: Path) -> dict:
    if not filepath.exists():
        print(f"Error: Checkpoint file '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON in '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)


def save_checkpoint(filepath: Path, data: dict):
    data["updated_at"] = get_current_iso_time()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Saved checkpoint to {filepath}")


def render_markdown(data: dict) -> str:
    session_id = data.get("session_id", "session-unknown")
    updated_at = data.get("updated_at", "N/A")
    version = data.get("version", "1.0.0")

    goal = data.get("goal", {})
    primary_goal = goal.get("primary", "N/A")
    scope_boundaries = goal.get("scope_boundaries", [])
    acceptance_criteria = goal.get("acceptance_criteria", [])

    scope_str = "\n".join(f"- {s}" for s in scope_boundaries) if scope_boundaries else "- None specified"
    acceptance_str = "\n".join(f"- [ ] {a}" for a in acceptance_criteria) if acceptance_criteria else "- None specified"

    milestones = data.get("milestones", [])
    if milestones:
        status_icons = {
            "completed": "✅ `completed`",
            "in_progress": "🔄 `in_progress`",
            "pending": "⏳ `pending`",
            "failed": "❌ `failed`",
            "blocked": "🚫 `blocked`",
        }
        milestone_rows = []
        for m in milestones:
            m_id = m.get("id", "-")
            m_title = m.get("title", "-")
            m_status = status_icons.get(m.get("status"), f"`{m.get('status')}`")
            m_verify = f"`{m.get('verified_by')}`" if m.get("verified_by") else "-"
            m_time = m.get("timestamp") or "-"
            milestone_rows.append(f"| {m_id} | {m_title} | {m_status} | {m_verify} | {m_time} |")
        milestones_table = "\n".join(milestone_rows)
    else:
        milestones_table = "| - | No milestones recorded | - | - | - |"

    decisions = data.get("decisions", [])
    if decisions:
        decisions_list = "\n".join(
            f"- **[{d.get('id', 'D')}] {d.get('topic', 'Topic')}:** {d.get('choice', 'Choice')}\n  *Rationale:* {d.get('rationale', 'N/A')}"
            for d in decisions
        )
    else:
        decisions_list = "_No key architectural decisions recorded._"

    blockers = data.get("blockers", [])
    if blockers:
        blockers_list = "\n".join(
            f"- **[{b.get('id', 'B')}] ({b.get('status', 'active')}):** {b.get('description', 'N/A')}"
            + (f"\n  *Workaround:* {b.get('workaround')}" if b.get("workaround") else "")
            for b in blockers
        )
    else:
        blockers_list = "_No active blockers recorded._"

    active_ctx = data.get("active_context", {})
    current_step = active_ctx.get("current_step", "N/A")
    open_files = active_ctx.get("open_files", [])
    open_files_str = "\n".join(f"  - `{f}`" for f in open_files) if open_files else "  - _None_"
    next_actions = active_ctx.get("next_actions", [])
    next_actions_str = "\n".join(f"  1. {a}" for a in next_actions) if next_actions else "  1. _None specified_"

    content = f"""# Session Checkpoint: {session_id}

**Last Updated:** `{updated_at}`  
**Version:** `{version}`

---

## 🎯 Primary Goal
> {primary_goal}

### Scope Boundaries
{scope_str}

### Acceptance Criteria
{acceptance_str}

---

## 🚩 Milestones
| ID | Milestone | Status | Verified By | Completed At |
| :--- | :--- | :--- | :--- | :--- |
{milestones_table}

---

## 💡 Key Decisions
{decisions_list}

---

## ⚠️ Known Blockers & Issues
{blockers_list}

---

## ⚡ Active Working Context
- **Current Step:** {current_step}
- **Open / Modified Files:**
{open_files_str}
- **Next Actions:**
{next_actions_str}
"""
    return content


def sync_render(checkpoint_path: Path, session_path: Path):
    data = load_checkpoint(checkpoint_path)
    md_content = render_markdown(data)
    with open(session_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Rendered session summary to {session_path}")


def cmd_init(args):
    filepath = Path(args.file)
    if filepath.exists() and not args.force:
        print(f"Error: '{filepath}' already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    session_id = args.session_id or f"session-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    data = {
        "$schema": "https://raw.githubusercontent.com/lengau/smarter-agents/main/skills/context-checkpoint/schemas/checkpoint.schema.json",
        "version": "1.0.0",
        "session_id": session_id,
        "updated_at": get_current_iso_time(),
        "goal": {
            "primary": args.goal or "Primary goal to be defined",
            "scope_boundaries": args.scope or [],
            "acceptance_criteria": args.criteria or [],
        },
        "milestones": [],
        "decisions": [],
        "blockers": [],
        "active_context": {
            "current_step": "Initialized session checkpoint",
            "open_files": [],
            "next_actions": ["Define detailed milestones and explore codebase"],
        },
    }
    save_checkpoint(filepath, data)
    sync_render(filepath, Path(args.session_file))


def cmd_milestone_add(args):
    filepath = Path(args.file)
    data = load_checkpoint(filepath)
    milestones = data.setdefault("milestones", [])
    next_num = len(milestones) + 1
    m_id = args.id or f"M{next_num}"
    new_milestone = {
        "id": m_id,
        "title": args.title,
        "status": args.status,
        "verified_by": args.verify_cmd if args.status == "completed" else None,
        "timestamp": get_current_iso_time() if args.status == "completed" else None,
    }
    milestones.append(new_milestone)
    save_checkpoint(filepath, data)
    sync_render(filepath, Path(args.session_file))
    print(f"Added milestone [{m_id}]: {args.title}")


def cmd_milestone_complete(args):
    filepath = Path(args.file)
    data = load_checkpoint(filepath)
    milestones = data.get("milestones", [])
    found = False
    for m in milestones:
        if m.get("id") == args.id:
            m["status"] = "completed"
            m["verified_by"] = args.verify_cmd
            m["timestamp"] = get_current_iso_time()
            found = True
            break
    if not found:
        print(f"Error: Milestone with ID '{args.id}' not found.", file=sys.stderr)
        sys.exit(1)

    save_checkpoint(filepath, data)
    sync_render(filepath, Path(args.session_file))
    print(f"Completed and verified milestone [{args.id}]")


def cmd_decision_add(args):
    filepath = Path(args.file)
    data = load_checkpoint(filepath)
    decisions = data.setdefault("decisions", [])
    next_num = len(decisions) + 1
    d_id = args.id or f"D{next_num}"
    new_decision = {
        "id": d_id,
        "topic": args.topic,
        "choice": args.choice,
        "rationale": args.rationale,
    }
    decisions.append(new_decision)
    save_checkpoint(filepath, data)
    sync_render(filepath, Path(args.session_file))
    print(f"Added decision [{d_id}] for topic '{args.topic}'")


def cmd_blocker_add(args):
    filepath = Path(args.file)
    data = load_checkpoint(filepath)
    blockers = data.setdefault("blockers", [])
    next_num = len(blockers) + 1
    b_id = args.id or f"B{next_num}"
    new_blocker = {
        "id": b_id,
        "description": args.desc,
        "status": args.status,
        "workaround": args.workaround,
    }
    blockers.append(new_blocker)
    save_checkpoint(filepath, data)
    sync_render(filepath, Path(args.session_file))
    print(f"Added blocker [{b_id}]: {args.desc}")


def cmd_update_context(args):
    filepath = Path(args.file)
    data = load_checkpoint(filepath)
    ctx = data.setdefault("active_context", {})
    if args.step:
        ctx["current_step"] = args.step
    if args.file_add:
        current_files = set(ctx.get("open_files", []))
        current_files.update(args.file_add)
        ctx["open_files"] = sorted(list(current_files))
    if args.next_action:
        ctx["next_actions"] = args.next_action

    save_checkpoint(filepath, data)
    sync_render(filepath, Path(args.session_file))
    print(f"Updated active context.")


def cmd_render(args):
    sync_render(Path(args.file), Path(args.session_file))


def cmd_validate(args):
    filepath = Path(args.file)
    data = load_checkpoint(filepath)
    required_keys = ["version", "session_id", "updated_at", "goal", "milestones", "decisions", "blockers", "active_context"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"Validation FAILED: Missing required top-level keys: {missing}", file=sys.stderr)
        sys.exit(1)

    # Validate goal
    goal = data["goal"]
    for gk in ["primary", "scope_boundaries", "acceptance_criteria"]:
        if gk not in goal:
            print(f"Validation FAILED: Missing goal key '{gk}'", file=sys.stderr)
            sys.exit(1)

    print(f"Validation PASSED for '{filepath}'. Checkpoint structure is fully compliant.")


def main():
    def add_common_args(parser):
        parser.add_argument("--file", default=DEFAULT_CHECKPOINT_FILE, help=f"Path to JSON checkpoint file (default: {DEFAULT_CHECKPOINT_FILE})")
        parser.add_argument("--session-file", default=DEFAULT_SESSION_FILE, help=f"Path to Markdown session file (default: {DEFAULT_SESSION_FILE})")

    parent_parser = argparse.ArgumentParser(add_help=False)
    add_common_args(parent_parser)

    parser = argparse.ArgumentParser(description="Context Checkpoint CLI & State Synchronizer", parents=[parent_parser])
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Init
    p_init = subparsers.add_parser("init", parents=[parent_parser], help="Initialize a new checkpoint")
    p_init.add_argument("--session-id", help="Custom session ID")
    p_init.add_argument("--goal", help="Primary goal description")
    p_init.add_argument("--scope", action="append", help="Scope boundary (can specify multiple)")
    p_init.add_argument("--criteria", action="append", help="Acceptance criteria (can specify multiple)")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing checkpoint")
    p_init.set_defaults(func=cmd_init)

    # Milestone
    p_milestone = subparsers.add_parser("milestone", parents=[parent_parser], help="Manage milestones")
    m_sub = p_milestone.add_subparsers(dest="milestone_action", required=True)
    
    p_m_add = m_sub.add_parser("add", parents=[parent_parser], help="Add a milestone")
    p_m_add.add_argument("--id", help="Milestone ID (e.g. M1)")
    p_m_add.add_argument("--title", required=True, help="Milestone title")
    p_m_add.add_argument("--status", choices=["pending", "in_progress", "completed", "failed", "blocked"], default="pending", help="Initial status")
    p_m_add.add_argument("--verify-cmd", help="Verification command (if completed)")
    p_m_add.set_defaults(func=cmd_milestone_add)

    p_m_comp = m_sub.add_parser("complete", parents=[parent_parser], help="Complete and verify a milestone")
    p_m_comp.add_argument("id", help="Milestone ID to complete")
    p_m_comp.add_argument("--verify-cmd", required=True, help="Command used to verify this milestone")
    p_m_comp.set_defaults(func=cmd_milestone_complete)

    # Decision
    p_dec = subparsers.add_parser("decision", parents=[parent_parser], help="Record architectural decisions")
    d_sub = p_dec.add_subparsers(dest="decision_action", required=True)
    p_d_add = d_sub.add_parser("add", parents=[parent_parser], help="Add a decision")
    p_d_add.add_argument("--id", help="Decision ID (e.g. D1)")
    p_d_add.add_argument("--topic", required=True, help="Topic or area of decision")
    p_d_add.add_argument("--choice", required=True, help="Chosen solution or direction")
    p_d_add.add_argument("--rationale", required=True, help="Reasoning for this choice")
    p_d_add.set_defaults(func=cmd_decision_add)

    # Blocker
    p_blk = subparsers.add_parser("blocker", parents=[parent_parser], help="Record blockers or issues")
    b_sub = p_blk.add_subparsers(dest="blocker_action", required=True)
    p_b_add = b_sub.add_parser("add", parents=[parent_parser], help="Add a blocker")
    p_b_add.add_argument("--id", help="Blocker ID (e.g. B1)")
    p_b_add.add_argument("--desc", required=True, help="Blocker description")
    p_b_add.add_argument("--status", choices=["active", "resolved", "investigating"], default="active")
    p_b_add.add_argument("--workaround", help="Workaround if available")
    p_b_add.set_defaults(func=cmd_blocker_add)

    # Update context
    p_ctx = subparsers.add_parser("update-context", parents=[parent_parser], help="Update active working context")
    p_ctx.add_argument("--step", help="Current step description")
    p_ctx.add_argument("--file-add", action="append", help="Add open/modified file path")
    p_ctx.add_argument("--next-action", action="append", help="Next action item (can specify multiple)")
    p_ctx.set_defaults(func=cmd_update_context)

    # Render
    p_render = subparsers.add_parser("render", parents=[parent_parser], help="Render SESSION.md from .checkpoint.json")
    p_render.set_defaults(func=cmd_render)

    # Validate
    p_val = subparsers.add_parser("validate", parents=[parent_parser], help="Validate .checkpoint.json structure")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

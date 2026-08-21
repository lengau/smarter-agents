#!/usr/bin/env python3
"""
patch_helper.py - Resilient Patch & Edit Helper for Coding Agents

Provides fuzzy matching, whitespace-insensitive anchor triangulation,
indentation normalization, and syntax validation to recover from failed
string replacements and prevent file corruption.
"""

import argparse
import difflib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def normalize_whitespace(text: str) -> str:
    """Normalize lines by stripping leading/trailing whitespace and blank line variances."""
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines)


def find_best_block_match(
    file_lines: List[str], target_lines: List[str], min_ratio: float = 0.6
) -> Optional[Tuple[int, int, float, str]]:
    """
    Find best matching line window in file_lines for target_lines using difflib SequenceMatcher.
    Returns (start_idx_0_based, end_idx_0_based_exclusive, similarity_ratio, matched_text).
    """
    if not target_lines or not file_lines:
        return None

    target_norm = [line.strip() for line in target_lines if line.strip()]
    if not target_norm:
        return None

    target_len = len(target_lines)
    best_match = None
    best_ratio = 0.0

    # Search window sizes around target_len
    min_window = max(1, target_len - 5)
    max_window = min(len(file_lines), target_len + 5)

    for w_len in range(min_window, max_window + 1):
        for i in range(len(file_lines) - w_len + 1):
            window_lines = file_lines[i : i + w_len]
            window_norm = [line.strip() for line in window_lines if line.strip()]

            matcher = difflib.SequenceMatcher(None, target_norm, window_norm)
            ratio = matcher.ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = (i, i + w_len, ratio, "".join(window_lines))

    if best_match and best_match[2] >= min_ratio:
        return best_match
    return None


def detect_indentation(sample_lines: List[str]) -> str:
    """Detect dominant indentation style (spaces/tabs and count) from lines."""
    for line in sample_lines:
        if line.strip():
            leading = line[: len(line) - len(line.lstrip())]
            if leading:
                return leading
    return "    "


def align_indentation(replacement_text: str, target_indent: str) -> str:
    """Re-indent replacement text to match target base indentation."""
    rep_lines = replacement_text.splitlines(keepends=True)
    if not rep_lines:
        return replacement_text

    # Find minimum indentation of non-empty replacement lines
    rep_indents = []
    for line in rep_lines:
        if line.strip():
            leading = line[: len(line) - len(line.lstrip())]
            rep_indents.append(len(leading))

    min_rep_indent = min(rep_indents) if rep_indents else 0

    aligned = []
    for line in rep_lines:
        if not line.strip():
            aligned.append(line)
        else:
            stripped = line[min_rep_indent:] if len(line) >= min_rep_indent else line.lstrip()
            aligned.append(target_indent + stripped)

    return "".join(aligned)


def validate_syntax(file_path: Path) -> Tuple[bool, str]:
    """Validate syntax of the modified file based on file extension."""
    ext = file_path.suffix.lower()
    try:
        if ext == ".py":
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(file_path)],
                capture_output=True,
                text=True,
            )
            return (result.returncode == 0, result.stderr)

        elif ext in (".js", ".mjs", ".cjs"):
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True,
                text=True,
            )
            return (result.returncode == 0, result.stderr)

        elif ext == ".json":
            result = subprocess.run(
                [sys.executable, "-m", "json.tool", str(file_path)],
                capture_output=True,
                text=True,
            )
            return (result.returncode == 0, result.stderr)

        return (True, "")
    except FileNotFoundError:
        return (True, "Validator runtime not installed; skipped.")


def cmd_find(args):
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    file_lines = file_path.read_text(errors="replace").splitlines(keepends=True)
    target_lines = (
        Path(args.target_file).read_text(errors="replace").splitlines(keepends=True)
        if args.target_file
        else args.target.splitlines(keepends=True)
    )

    match = find_best_block_match(file_lines, target_lines, min_ratio=args.threshold)
    if match:
        start_idx, end_idx, ratio, matched_text = match
        print(f"Match Found (Similarity: {ratio:.1%}):")
        print(f"  Lines: {start_idx + 1} to {end_idx} (1-indexed)")
        print("--- Matching Content Snippet ---")
        for idx in range(start_idx, end_idx):
            print(f"{idx + 1:4d} | {file_lines[idx]}", end="")
        print("--------------------------------")
        return 0
    else:
        print(f"No match found above threshold {args.threshold:.1%}", file=sys.stderr)
        return 2


def cmd_replace(args):
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    content = file_path.read_text(errors="replace")
    file_lines = content.splitlines(keepends=True)

    target_text = Path(args.target_file).read_text() if args.target_file else args.target
    replacement_text = Path(args.replacement_file).read_text() if args.replacement_file else args.replacement

    # 1. Exact string match check first
    if target_text in content:
        count = content.count(target_text)
        if count == 1:
            new_content = content.replace(target_text, replacement_text, 1)
            if args.dry_run:
                print(f"[Dry Run] Exact 1:1 match found and replaceable.")
                return 0
            file_path.write_text(new_content)
            valid, err = validate_syntax(file_path)
            if not valid:
                file_path.write_text(content)  # Revert
                print(f"Error: Replacement produced syntax error. Reverted.\n{err}", file=sys.stderr)
                return 3
            print(f"Successfully applied exact replacement.")
            return 0
        else:
            print(f"Warning: Exact target found {count} times (ambiguous). Falling back to fuzzy anchor range.", file=sys.stderr)

    # 2. Fuzzy block match
    target_lines = target_text.splitlines(keepends=True)
    match = find_best_block_match(file_lines, target_lines, min_ratio=args.threshold)
    if not match:
        print("Error: Could not locate target block via fuzzy search.", file=sys.stderr)
        return 2

    start_idx, end_idx, ratio, _ = match
    print(f"Located target at lines {start_idx + 1}-{end_idx} with {ratio:.1%} similarity.")

    # Re-indent replacement text to match target
    target_indent = detect_indentation(file_lines[start_idx:end_idx])
    aligned_replacement = align_indentation(replacement_text, target_indent)

    new_lines = file_lines[:start_idx] + [aligned_replacement] + file_lines[end_idx:]
    new_content = "".join(new_lines)

    if args.dry_run:
        diff = difflib.unified_diff(
            file_lines,
            new_lines,
            fromfile=str(file_path),
            tofile=f"{file_path} (modified)",
        )
        print("".join(diff))
        return 0

    file_path.write_text(new_content)
    valid, err = validate_syntax(file_path)
    if not valid:
        file_path.write_text(content)  # Revert
        print(f"Error: Replacement caused syntax failure. Reverted to original.\n{err}", file=sys.stderr)
        return 3

    print(f"Successfully replaced lines {start_idx + 1}-{end_idx} and verified syntax.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Resilient AST & Fuzzy Patch Repair Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Find command
    find_parser = subparsers.add_parser("find", help="Find fuzzy line range matching target snippet")
    find_parser.add_argument("--file", "-f", required=True, help="Target file path")
    find_parser.add_argument("--target", "-t", default="", help="Target text snippet")
    find_parser.add_argument("--target-file", help="File containing target text snippet")
    find_parser.add_argument("--threshold", type=float, default=0.6, help="Fuzzy match threshold (default 0.6)")

    # Replace command
    rep_parser = subparsers.add_parser("replace", help="Fuzzy replace target snippet with replacement text")
    rep_parser.add_argument("--file", "-f", required=True, help="Target file path")
    rep_parser.add_argument("--target", "-t", default="", help="Target text snippet to replace")
    rep_parser.add_argument("--target-file", help="File containing target text snippet")
    rep_parser.add_argument("--replacement", "-r", default="", help="Replacement text snippet")
    rep_parser.add_argument("--replacement-file", help="File containing replacement text snippet")
    rep_parser.add_argument("--threshold", type=float, default=0.6, help="Fuzzy match threshold (default 0.6)")
    rep_parser.add_argument("--dry-run", action="store_true", help="Print diff without modifying file")

    args = parser.parse_args()

    if args.command == "find":
        sys.exit(cmd_find(args))
    elif args.command == "replace":
        sys.exit(cmd_replace(args))


if __name__ == "__main__":
    main()

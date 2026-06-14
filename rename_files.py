"""
rename_files.py — interactively remove a substring from filenames.

Run it, point it at a folder or a single file, optionally narrow to
specific file types, type what you want stripped from the names,
review the preview, confirm.

Originally written for PDFs whose names still had ".pptx" embedded in
them (e.g. "lecture.pptx.pdf"), but works on any file type.

Usage
-----
    python rename_files.py                  # asks for everything
    python rename_files.py ./slides         # uses ./slides as the folder
    python rename_files.py file.pdf         # rename a single file
    python rename_files.py ./slides -r      # also include subfolders
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


def clean_name(name: str, pattern: str, all_occurrences: bool = True) -> str:
    """Return ``name`` with ``pattern`` stripped out and tidied up.

    The file extension (everything after the last dot) is preserved.
    Leftover separators (spaces, underscores, hyphens) at the edges or
    doubled in the middle are collapsed.
    """
    if not pattern:
        return name

    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    else:
        ext = "." + ext

    count = 0 if all_occurrences else 1
    cleaned = re.sub(re.escape(pattern), "", stem, count=count, flags=re.IGNORECASE)

    # Collapse separators left behind by the removal, then trim the edges.
    cleaned = re.sub(r"[\s_\-]{2,}", " ", cleaned).strip(" _-")
    return (cleaned or "file") + ext


def unique_path(target: Path, taken: set[Path]) -> Path:
    """If ``target`` already exists (on disk or in ``taken``), append (2), (3), ..."""
    if target not in taken and not target.exists():
        return target
    stem, ext = target.stem, target.suffix
    i = 2
    while True:
        candidate = target.with_name(f"{stem} ({i}){ext}")
        if candidate not in taken and not candidate.exists():
            return candidate
        i += 1


def find_files(root: Path, recursive: bool, extensions: set[str] | None) -> list[Path]:
    """Return files in ``root``, optionally filtered to a set of extensions.

    ``extensions`` should be lowercase and include the leading dot, e.g. {".pdf"}.
    ``None`` means all files.
    """
    pattern = "**/*" if recursive else "*"
    matches: list[Path] = []
    for p in root.glob(pattern):
        if not p.is_file():
            continue
        if extensions is not None and p.suffix.lower() not in extensions:
            continue
        matches.append(p)
    return sorted(matches)


def normalize_extensions(raw: str) -> set[str]:
    """Parse a user string like 'pdf, .docx png' into {'.pdf', '.docx', '.png'}."""
    parts = re.split(r"[\s,]+", raw.strip().lower())
    return {("." + p.lstrip(".")) for p in parts if p}


def ask(prompt: str, default: str = "") -> str:
    """Prompt the user, returning the default if they just hit Enter."""
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        return default
    return answer or default


def strip_drag_quotes(s: str) -> str:
    """Remove a matching pair of surrounding quotes (e.g. from macOS drag-drop)."""
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            answer = input(f"{prompt} [{hint}]: ").strip().lower()
        except EOFError:
            return default
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please answer y or n.")


def summarize_types(files: list[Path]) -> str:
    """Build a short string like '12 .pdf, 3 .docx, 2 (no extension)'."""
    counts = Counter((p.suffix.lower() or "(no extension)") for p in files)
    return ", ".join(f"{n} {ext}" for ext, n in counts.most_common())


def preview_changes(files: list[Path], pattern: str, all_occurrences: bool) -> list[tuple[Path, Path]]:
    """Return the list of (source, destination) pairs that would actually change."""
    planned: list[tuple[Path, Path]] = []
    taken: set[Path] = set()
    for f in files:
        new_name = clean_name(f.name, pattern, all_occurrences)
        if new_name == f.name:
            continue
        target = unique_path(f.with_name(new_name), taken)
        taken.add(target)
        planned.append((f, target))
    return planned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interactively rename a file or folder of files by removing a substring.")
    parser.add_argument("folder", nargs="?", type=Path, help="Folder to scan or a single file (you'll be prompted if omitted).")
    parser.add_argument("--recursive", "-r", action="store_true", help="Also include files in subfolders (when folder is given).")
    args = parser.parse_args(argv)

    # 1. Folder or file
    target = args.folder
    if target is None:
        raw = ask("Folder or file to process", default=".")
        target = Path(strip_drag_quotes(raw)).expanduser()

    if target.is_file():
        files = [target]
        all_files = files
        print(f"\nProcessing 1 file: {target.name}")
    elif target.is_dir():
        all_files = find_files(target, args.recursive, extensions=None)
        if not all_files:
            scope = "(including subfolders)" if args.recursive else "(top level only)"
            print(f"No files found in {target} {scope}.")
            return 0

        print(f"\nFound {len(all_files)} file(s) in {target}: {summarize_types(all_files)}")

        # 2. Optional extension filter (folders only)
        ext_raw = ask(
            "\nLimit to specific extensions? (e.g. 'pdf' or 'pdf, docx' — blank = all)",
            default="",
        )
        if ext_raw:
            extensions = normalize_extensions(ext_raw)
            files = [f for f in all_files if f.suffix.lower() in extensions]
            if not files:
                print(f"No files matched {sorted(extensions)}.")
                return 0
            print(f"Filtered to {len(files)} file(s).")
        else:
            files = all_files
    else:
        print(f"error: {target} is neither a file nor a folder", file=sys.stderr)
        return 1

    # 3. Substring to remove — keep looping until something matches or they quit.
    while True:
        pattern = ask("\nWhat text should I remove from the filenames?", default=".pptx")
        if not pattern:
            print("Nothing to remove. Exiting.")
            return 0

        all_occurrences = ask_yes_no("Remove every occurrence (not just the first)?", default=True)
        planned = preview_changes(files, pattern, all_occurrences)

        if planned:
            break

        print(f"\nNo filenames contain '{pattern}'.")
        if not ask_yes_no("Try a different substring?", default=True):
            return 0

    # 4. Preview
    print(f"\nThe following {len(planned)} file(s) would be renamed:\n")
    for src, dst in planned:
        print(f"  {src.name}")
        print(f"   -> {dst.name}\n")

    skipped = len(files) - len(planned)
    if skipped:
        print(f"({skipped} file(s) unchanged.)\n")

    # 5. Confirm and apply
    if not ask_yes_no("Apply these renames?", default=False):
        print("Cancelled. No files changed.")
        return 0

    renamed = 0
    for src, dst in planned:
        try:
            src.rename(dst)
            renamed += 1
        except OSError as e:
            print(f"  failed: {src.name} ({e})", file=sys.stderr)

    print(f"\nDone. Renamed {renamed} of {len(planned)} file(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)
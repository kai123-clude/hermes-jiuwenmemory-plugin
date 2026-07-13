#!/usr/bin/env python3
"""Sync user-local Hermes skills into this repository.

Only directories containing SKILL.md are copied. Runtime caches, virtual
Environments, backups, generated work, and bytecode are intentionally omitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".hub", ".curator_backups",
    "work", "node_modules", ".pytest_cache", "dist", "build",
}
EXCLUDED_NAMES = {".DS_Store"}


def excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts) or path.name in EXCLUDED_NAMES


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_tree(source: Path, destination: Path) -> int:
    count = 0
    for path in sorted(source.rglob("*")):
        if excluded(path):
            continue
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path.home() / ".hermes" / "skills")
    parser.add_argument("--destination", type=Path, default=Path("skills"))
    parser.add_argument("--prune", action="store_true", help="remove destination skill directories absent from source")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    destination = args.destination.resolve()
    if not source.is_dir():
        raise SystemExit(f"source does not exist: {source}")

    skill_dirs = sorted({p.parent for p in source.rglob("SKILL.md") if not excluded(p)})
    expected = set()
    manifest_skills = []
    total_files = 0
    destination.mkdir(parents=True, exist_ok=True)

    for skill_dir in skill_dirs:
        relative = skill_dir.relative_to(source)
        expected.add(relative.as_posix())
        target = destination / relative
        if target.exists():
            shutil.rmtree(target)
        copied = copy_tree(skill_dir, target)
        total_files += copied
        files = []
        for path in sorted(target.rglob("*")):
            if path.is_file() and not excluded(path):
                files.append({"path": path.relative_to(target).as_posix(), "sha256": sha256(path)})
        manifest_skills.append({"path": relative.as_posix(), "files": files})

    if args.prune:
        for child in sorted(destination.iterdir()):
            if child.is_dir() and child.name not in {p.split("/", 1)[0] for p in expected}:
                shutil.rmtree(child)

    manifest = {
        "source": str(source),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_count": len(manifest_skills),
        "file_count": total_files,
        "excluded_directories": sorted(EXCLUDED_DIRS),
        "skills": manifest_skills,
    }
    (destination / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"synced_skills={len(manifest_skills)}")
    print(f"synced_files={total_files}")
    print(f"destination={destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

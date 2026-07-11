#!/usr/bin/env python3
"""Transactionally promote a fully validated coding-knowledge directory."""

import argparse
import os
import shutil
import sys
from pathlib import Path
from uuid import uuid4


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def promote(staging: Path, target: Path) -> None:
    staging = staging.resolve()
    target = target.resolve()
    if not staging.is_dir():
        raise ValueError(f"staging directory does not exist: {staging}")
    if staging == target or target in staging.parents:
        raise ValueError("staging must be a sibling of target, not inside target")
    if staging.stat().st_dev != target.parent.stat().st_dev:
        raise ValueError("staging and target must be on the same filesystem")
    if not (staging / "scan-baseline.yaml").is_file():
        raise ValueError("validated staging is incomplete: scan-baseline.yaml is missing")

    backup = target.parent / f".{target.name}.rollback-{uuid4().hex}"
    moved_old = False
    moved_new = False
    try:
        if target.exists():
            os.replace(target, backup)
            moved_old = True
        os.replace(staging, target)
        moved_new = True
        fsync_dir(target.parent)
    except BaseException:
        if moved_new and target.exists():
            os.replace(target, staging)
        if moved_old and backup.exists():
            os.replace(backup, target)
        fsync_dir(target.parent)
        raise

    if backup.exists():
        shutil.rmtree(backup)
        fsync_dir(target.parent)


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a validated coding-knowledge staging tree")
    parser.add_argument("--staging", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    try:
        promote(Path(args.staging), Path(args.target))
    except (OSError, ValueError) as exc:
        print(f"promotion failed: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

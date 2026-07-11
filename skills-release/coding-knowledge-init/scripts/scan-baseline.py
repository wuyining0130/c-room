#!/usr/bin/env python3
"""Track per-repository scan baselines without third-party dependencies."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def run(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True).stdout


def run_bytes(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def canonical_remote(remote):
    """Return a credential-free repository identity suitable for comparison."""
    remote = remote.strip()
    if not remote:
        return ""
    if "://" in remote:
        parsed = urlsplit(remote)
        hostname = parsed.hostname or ""
        if parsed.port:
            hostname += f":{parsed.port}"
        path = re.sub(r"/+", "/", parsed.path).rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return urlunsplit((parsed.scheme.lower(), hostname.lower(), path, "", ""))
    # SCP-style SSH remotes may contain a user but never retain it as identity.
    match = re.match(r"(?:[^@]+@)?([^:]+):(.+)$", remote)
    if match:
        host, path = match.groups()
        path = path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return f"ssh://{host.lower()}/{path}"
    return str(Path(remote).expanduser().resolve()) if not remote.startswith("/") else str(Path(remote).resolve())


def state(repo):
    head = run(repo, "rev-parse", "HEAD").strip()
    status = run(repo, "status", "--porcelain=v1", "--untracked-files=all")
    diff = run(repo, "diff", "--binary", "HEAD")
    staged = run(repo, "diff", "--cached", "--binary")
    untracked = [item for item in run_bytes(repo, "ls-files", "-z", "--others", "--exclude-standard").split(b"\0") if item]
    untracked_hashes = []
    for rel_bytes in sorted(untracked):
        rel = os.fsdecode(rel_bytes)
        path = repo / rel
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            continue
        if path.is_symlink():
            payload = os.fsencode(os.readlink(path))
            kind = b"symlink"
        elif path.is_file():
            payload = path.read_bytes()
            kind = b"file"
        else:
            # Git normally expands untracked directories, but preserve their type if one appears.
            payload = str(mode).encode("ascii")
            kind = b"other"
        untracked_hashes.append(rel_bytes + b":" + kind + b":" + hashlib.sha256(payload).hexdigest().encode("ascii"))
    digest_input = status.encode() + b"\0" + diff.encode() + b"\0" + staged.encode() + b"\0" + b"\n".join(untracked_hashes)
    digest = hashlib.sha256(digest_input).hexdigest()
    try:
        remote = canonical_remote(run(repo, "config", "--get", "remote.origin.url"))
    except subprocess.CalledProcessError:
        remote = ""
    return {"head": head, "remote": remote, "dirty": bool(status), "dirty_fingerprint": digest}


def baseline_is_ancestor(repo, commit):
    if not commit:
        return False
    return subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def load(path):
    if not path.exists():
        return {"repos": {}}
    # JSON is valid YAML and avoids adding a YAML runtime dependency.
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["changed", "record"])
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--scan-result")
    args = parser.parse_args()
    baseline = Path(args.baseline)
    repo = Path(args.repo).resolve()
    data = load(baseline)
    current = state(repo)
    previous = data.get("repos", {}).get(args.name)
    if args.command == "changed":
        identity_changed = bool(previous and previous.get("remote") != current["remote"])
        ancestor_ok = bool(previous and baseline_is_ancestor(repo, previous.get("last_scanned_commit")))
        full_scan = not previous or identity_changed or not ancestor_ok
        changed = full_scan or previous.get("last_scanned_commit") != current["head"] or previous.get("dirty_patch_fingerprint") != current["dirty_fingerprint"]
        reason = "full-scan" if full_scan else ("content-changed" if changed else "unchanged")
        print(json.dumps({"changed": changed, "full_scan": full_scan, "reason": reason, **current}))
        return
    if not args.scan_result:
        parser.error("record requires --scan-result after scan and quality validation")
    scan_result = Path(args.scan_result)
    scan_hash = hashlib.sha256(scan_result.read_bytes()).hexdigest()
    data.setdefault("repos", {})[args.name] = {
        "path": str(repo),
        "remote": current["remote"],
        "last_scanned_commit": current["head"],
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "dirty_at_scan": current["dirty"],
        "scan_fingerprint": scan_hash,
        "dirty_patch_fingerprint": current["dirty_fingerprint"],
    }
    save(baseline, data)


if __name__ == "__main__":
    main()

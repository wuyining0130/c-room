#!/usr/bin/env python3
"""Regression tests for scan-baseline.py using real temporary Git repositories."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("scan-baseline.py")
SPEC = importlib.util.spec_from_file_location("scan_baseline", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScanBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        (self.repo / "tracked.txt").write_text("base", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-qm", "initial")
        self.baseline = self.root / "state" / "baseline.yaml"
        self.scan = self.root / "scan.md"
        self.scan.write_text("scan result", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True).stdout

    def record(self):
        data = {"repos": {"repo": {
            "remote": MODULE.state(self.repo)["remote"],
            "last_scanned_commit": MODULE.state(self.repo)["head"],
            "dirty_patch_fingerprint": MODULE.state(self.repo)["dirty_fingerprint"],
        }}}
        MODULE.save(self.baseline, data)

    def test_unicode_and_newline_untracked_content_is_hashed(self):
        unusual = self.repo / "中文\n文件.txt"
        unusual.write_text("first", encoding="utf-8")
        self.record()
        before = MODULE.load(self.baseline)["repos"]["repo"]["dirty_patch_fingerprint"]
        unusual.write_text("second", encoding="utf-8")
        after = MODULE.state(self.repo)["dirty_fingerprint"]
        self.assertNotEqual(before, after)

    def test_broken_symlink_target_is_hashed_without_following_it(self):
        link = self.repo / "untracked-link"
        link.symlink_to("missing-a")
        first = MODULE.state(self.repo)["dirty_fingerprint"]
        link.unlink()
        link.symlink_to("missing-b")
        second = MODULE.state(self.repo)["dirty_fingerprint"]
        self.assertNotEqual(first, second)

    def test_symlink_does_not_hash_external_target_content(self):
        external = self.root / "external-secret"
        external.write_text("first", encoding="utf-8")
        (self.repo / "link").symlink_to(external)
        first = MODULE.state(self.repo)["dirty_fingerprint"]
        external.write_text("second", encoding="utf-8")
        second = MODULE.state(self.repo)["dirty_fingerprint"]
        self.assertEqual(first, second)

    def test_remote_credentials_are_removed_and_do_not_change_identity(self):
        first = MODULE.canonical_remote("https://alice:secret@example.com/org/repo.git")
        second = MODULE.canonical_remote("https://bob:new-token@example.com/org/repo.git")
        self.assertEqual(first, "https://example.com/org/repo")
        self.assertEqual(first, second)
        self.assertNotIn("secret", first)

    def test_atomic_save_keeps_old_baseline_if_replace_fails(self):
        MODULE.save(self.baseline, {"repos": {"old": {}}})
        with mock.patch.object(MODULE.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                MODULE.save(self.baseline, {"repos": {"new": {}}})
        self.assertIn("old", json.loads(self.baseline.read_text(encoding="utf-8"))["repos"])

    def test_unreachable_commit_requires_full_scan(self):
        self.record()
        data = MODULE.load(self.baseline)
        data["repos"]["repo"]["last_scanned_commit"] = "0" * 40
        MODULE.save(self.baseline, data)
        self.assertFalse(MODULE.baseline_is_ancestor(self.repo, "0" * 40))


if __name__ == "__main__":
    unittest.main()

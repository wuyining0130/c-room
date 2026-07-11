#!/usr/bin/env python3
"""Tests for transactional coding-knowledge promotion."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("promote-staging.py")
SPEC = importlib.util.spec_from_file_location("promote_staging", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PromoteStagingTests(unittest.TestCase):
    def make_tree(self, root, name, marker):
        tree = root / name
        tree.mkdir()
        (tree / "scan-baseline.yaml").write_text("{}", encoding="utf-8")
        (tree / "INDEX.md").write_text(marker, encoding="utf-8")
        return tree

    def test_promotes_complete_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.make_tree(root, "coding-knowledge", "old")
            staging = self.make_tree(root, "staging", "new")
            MODULE.promote(staging, target)
            self.assertEqual((target / "INDEX.md").read_text(), "new")
            self.assertFalse(staging.exists())

    def test_restores_old_tree_if_new_tree_move_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.make_tree(root, "coding-knowledge", "old")
            staging = self.make_tree(root, "staging", "new")
            real_replace = MODULE.os.replace
            calls = 0

            def fail_second(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated interruption")
                return real_replace(source, destination)

            with mock.patch.object(MODULE.os, "replace", side_effect=fail_second):
                with self.assertRaises(OSError):
                    MODULE.promote(staging, target)
            self.assertEqual((target / "INDEX.md").read_text(), "old")
            self.assertEqual((staging / "INDEX.md").read_text(), "new")

    def test_rejects_incomplete_staging(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.make_tree(root, "coding-knowledge", "old")
            staging = root / "staging"
            staging.mkdir()
            with self.assertRaises(ValueError):
                MODULE.promote(staging, target)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline safety and verification tests for tapd_sync.py."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("tapd_sync.py")
SPEC = importlib.util.spec_from_file_location("tapd_sync", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TapdSyncTests(unittest.TestCase):
    def test_secure_write_uses_private_permissions_and_exclusive_create(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "backup.json"
            MODULE.secure_write(path, b"secret")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                MODULE.secure_write(path, b"overwrite")
            self.assertEqual(path.read_bytes(), b"secret")

    def test_normalized_visible_text_accepts_safe_html_cleanup(self):
        expected = "<h2>A &amp; B</h2><p>Hello   world</p>"
        cleaned = "<div><strong>A &amp; B</strong></div>\n<p>Hello world</p>"
        self.assertEqual(MODULE.normalized_visible_text(expected), MODULE.normalized_visible_text(cleaned))

    def test_normalized_visible_text_detects_middle_or_tail_truncation(self):
        full = "<p>start</p><p>middle requirement</p><p>tail acceptance</p>"
        middle_missing = "<p>start</p><p>tail acceptance</p>"
        tail_missing = "<p>start</p><p>middle requirement</p>"
        self.assertNotEqual(MODULE.normalized_visible_text(full), MODULE.normalized_visible_text(middle_missing))
        self.assertNotEqual(MODULE.normalized_visible_text(full), MODULE.normalized_visible_text(tail_missing))

    def test_image_contract_detects_missing_or_empty_sources(self):
        expected = MODULE.normalized_content_contract('<p><img src="data:image/png;base64,abc" alt="" /></p>')
        missing = MODULE.normalized_content_contract('<p></p>')
        empty_src = MODULE.normalized_content_contract('<p><img src="" alt="" /></p>')
        self.assertNotEqual(len(expected["images"]), len(missing["images"]))
        self.assertFalse(all(item["src"] for item in empty_src["images"]))

    def test_image_contract_accepts_tapd_rehosting_with_same_order_and_alt(self):
        expected = MODULE.normalized_content_contract('<img src="data:image/png;base64,abc" alt="流程图">')
        rehosted = MODULE.normalized_content_contract('<img src="https://tapd.example/cdn/1.png" alt="流程图">')
        self.assertEqual([i["alt"] for i in expected["images"]], [i["alt"] for i in rehosted["images"]])
        self.assertTrue(all(item["src"] for item in rehosted["images"]))

    def test_local_mermaid_requires_explicit_local_script(self):
        old = MODULE.MERMAID_JS_PATH
        try:
            MODULE.MERMAID_JS_PATH = None
            self.assertIsNone(MODULE._mermaid_via_playwright("flowchart LR; A-->B"))
        finally:
            MODULE.MERMAID_JS_PATH = old

    def test_remote_mermaid_is_never_called_without_opt_in(self):
        old_remote = MODULE.ALLOW_REMOTE_MERMAID
        try:
            MODULE.ALLOW_REMOTE_MERMAID = False
            with mock.patch.object(MODULE, "_mermaid_via_playwright", return_value=None), \
                    mock.patch.object(MODULE, "_mermaid_via_ink") as remote:
                output = MODULE.mermaid_to_img("flowchart LR; A-->B")
            remote.assert_not_called()
            self.assertIn("language-mermaid", output)
        finally:
            MODULE.ALLOW_REMOTE_MERMAID = old_remote

    def test_local_mermaid_page_blocks_all_http_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            js = Path(temp) / "mermaid.min.js"
            js.write_text("window.mermaid = {};", encoding="utf-8")
            page = mock.MagicMock()
            svg = mock.MagicMock()
            svg.screenshot.return_value = b"png"
            page.query_selector.return_value = svg
            browser = mock.MagicMock()
            browser.new_page.return_value = page
            old_path = MODULE.MERMAID_JS_PATH
            try:
                MODULE.MERMAID_JS_PATH = str(js)
                with mock.patch.object(MODULE, "_get_playwright_browser", return_value=browser):
                    MODULE._mermaid_via_playwright('flowchart LR; A["<img src=https://evil.example/x>"]-->B')
            finally:
                MODULE.MERMAID_JS_PATH = old_path
            pattern, handler = page.route.call_args.args
            self.assertTrue(pattern.search("https://evil.example/x"))
            route = mock.MagicMock()
            handler(route)
            route.abort.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
